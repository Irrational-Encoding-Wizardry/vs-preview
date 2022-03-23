from __future__ import annotations

import gc
import sys
import yaml
import logging
import vapoursynth as vs
from pathlib import Path
from typing import Any, cast, List, Mapping, Tuple
from traceback import FrameSummary, TracebackException

from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QEvent
from PyQt5.QtGui import QCloseEvent, QPalette, QShowEvent, QColorSpace, QMoveEvent
from PyQt5.QtWidgets import (
    QVBoxLayout, QLabel, QWidget, QApplication, QGraphicsScene, QOpenGLWidget, QSizePolicy, QGraphicsView
)

from ..toolbars import Toolbars
from ..models import VideoOutputs
from ..core.vsenv import get_policy
from ..utils import get_usable_cpus_count, set_qobject_names
from ..core import AbstractMainWindow, Frame, VideoOutput, Time, try_load
from ..widgets import StatusBar, Timeline, GraphicsView, GraphicsImageItem

from .settings import MainSettings
from .dialog import ScriptErrorDialog, SettingsDialog

if sys.platform == 'win32':
    import win32gui  # type: ignore
    try:
        from PIL import _imagingcms  # type: ignore
    except ImportError:
        _imagingcms = None


class MainWindow(AbstractMainWindow):
    # those are defaults that can be overriden at runtime or used as fallbacks
    AUTOSAVE_INTERVAL = 60 * 1000  # s
    CHECKERBOARD_ENABLED = True
    CHECKERBOARD_TILE_COLOR_1 = Qt.white
    CHECKERBOARD_TILE_COLOR_2 = Qt.lightGray
    CHECKERBOARD_TILE_SIZE = 8  # px
    FPS_AVERAGING_WINDOW_SIZE = Frame(100)
    FPS_REFRESH_INTERVAL = 150  # ms
    LOG_LEVEL = logging.INFO
    OUTPUT_INDEX = 0
    PLAY_BUFFER_SIZE = Frame(get_usable_cpus_count())
    SAVE_TEMPLATE = '{script_name}_{frame}'
    STORAGE_BACKUPS_COUNT = 2
    SYNC_OUTPUTS = True
    SEEK_STEP = 1
    INSTANT_FRAME_UPDATE = False
    # it's allowed to stretch target interval betweewn notches by N% at most
    TIMELINE_LABEL_NOTCHES_MARGIN = 20  # %
    TIMELINE_MODE = 'frame'
    VSP_DIR_NAME = '.vspreview'
    # used for formats with subsampling
    VS_OUTPUT_RESIZER = VideoOutput.Resizer.Bicubic
    VS_OUTPUT_MATRIX = VideoOutput.Matrix.BT709
    VS_OUTPUT_TRANSFER = VideoOutput.Transfer.BT709
    VS_OUTPUT_PRIMARIES = VideoOutput.Primaries.BT709
    VS_OUTPUT_RANGE = VideoOutput.Range.LIMITED
    VS_OUTPUT_CHROMALOC = VideoOutput.ChromaLoc.LEFT
    VS_OUTPUT_RESIZER_KWARGS = {
        'dither_type': 'error_diffusion',
    }

    # status bar
    def STATUS_FRAME_PROP(self, prop: Any) -> str:
        return 'Type: %s' % (prop['_PictType'].decode('utf-8') if '_PictType' in prop else '?')

    DEBUG_PLAY_FPS = False
    DEBUG_TOOLBAR = False
    DEBUG_TOOLBAR_BUTTONS_PRINT_STATE = False

    EVENT_POLICY = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    storable_attrs = [
        'settings', 'toolbars',
    ]
    __slots__ = storable_attrs + [
        'app', 'display_scale', 'clipboard',
        'script_path', 'save_on_exit', 'timeline', 'main_layout',
        'graphics_scene', 'graphics_view', 'script_error_dialog',
        'central_widget', 'statusbar', 'storage_not_found',
        'current_storage_path', 'opengl_widget'
    ]

    # emit when about to reload a script: clear all existing references to existing clips.
    reload_signal = pyqtSignal()

    def __init__(self, config_dir: Path) -> None:
        super().__init__()

        self.settings = MainSettings()

        # logging
        logging.basicConfig(format='{asctime}: {levelname}: {message}', style='{', level=self.LOG_LEVEL)
        logging.Formatter.default_msec_format = '%s.%03d'

        self.config_dir = config_dir / self.VSP_DIR_NAME

        self.app = QApplication.instance()
        assert self.app

        if self.settings.dark_theme_enabled:
            try:
                from qdarkstyle import load_stylesheet_pyqt5
            except ImportError:
                self.self.settings.dark_theme_enabled = False
            else:
                self.app.setStyleSheet(self.patch_dark_stylesheet(load_stylesheet_pyqt5()))
                self.ensurePolished()

        self.display_scale = self.app.primaryScreen().logicalDotsPerInch() / self.settings.base_ppi
        self.setWindowTitle('VSPreview')
        self.move(400, 0)
        self.setup_ui()
        self.storage_not_found = None

        # global
        self.clipboard = self.app.clipboard()
        self.external_args: List[Tuple[str, str]] = []
        self.script_path = Path()
        self.save_on_exit = True
        self.script_exec_failed = False
        self.current_storage_path = Path()

        # graphics view
        self.graphics_scene = QGraphicsScene(self)
        self.graphics_view.setScene(self.graphics_scene)
        self.opengl_widget = None

        if self.settings.opengl_rendering_enabled:
            self.opengl_widget = QOpenGLWidget()
            self.graphics_view.setViewport(self.opengl_widget)

        self.graphics_view.wheelScrolled.connect(self.on_wheel_scrolled)

        # timeline
        self.timeline.clicked.connect(self.on_timeline_clicked)

        # display profile
        self.display_profile: QColorSpace | None = None
        self.current_screen = 0

        # init toolbars and outputs
        self.app_settings = SettingsDialog(self)
        self.toolbars = Toolbars(self)
        self.main_layout.addWidget(self.toolbars.main)

        for toolbar in self.toolbars:
            self.main_layout.addWidget(toolbar)
            self.toolbars.main.layout().addWidget(toolbar.toggle_button)

        self.app_settings.tab_widget.setUsesScrollButtons(False)
        self.app_settings.setMinimumWidth(
            int(len(self.toolbars) * 1.05 * self.app_settings.tab_widget.geometry().width() / 2)
        )

        set_qobject_names(self)
        self.setObjectName('MainWindow')

    def setup_ui(self) -> None:
        self.central_widget = QWidget(self)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        self.graphics_view = GraphicsView(self.central_widget)
        self.graphics_view.setBackgroundBrush(self.palette().brush(QPalette.Window))
        self.graphics_view.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.main_layout.addWidget(self.graphics_view)

        self.timeline = Timeline(self.central_widget)
        self.main_layout.addWidget(self.timeline)

        # status bar

        self.statusbar = StatusBar(self.central_widget)

        self.statusbar.total_frames_label = QLabel(self.central_widget)
        self.statusbar.total_frames_label.setObjectName('MainWindow.statusbar.total_frames_label')
        self.statusbar.addWidget(self.statusbar.total_frames_label)

        self.statusbar.duration_label = QLabel(self.central_widget)
        self.statusbar.duration_label.setObjectName('MainWindow.statusbar.duration_label')
        self.statusbar.addWidget(self.statusbar.duration_label)

        self.statusbar.resolution_label = QLabel(self.central_widget)
        self.statusbar.resolution_label.setObjectName('MainWindow.statusbar.resolution_label')
        self.statusbar.addWidget(self.statusbar.resolution_label)

        self.statusbar.pixel_format_label = QLabel(self.central_widget)
        self.statusbar.pixel_format_label.setObjectName('MainWindow.statusbar.pixel_format_label')
        self.statusbar.addWidget(self.statusbar.pixel_format_label)

        self.statusbar.fps_label = QLabel(self.central_widget)
        self.statusbar.fps_label.setObjectName('MainWindow.statusbar.fps_label')
        self.statusbar.addWidget(self.statusbar.fps_label)

        self.statusbar.frame_props_label = QLabel(self.central_widget)
        self.statusbar.frame_props_label.setObjectName('MainWindow.statusbar.frame_props_label')
        self.statusbar.addWidget(self.statusbar.frame_props_label)

        self.statusbar.label = QLabel(self.central_widget)
        self.statusbar.label.setObjectName('MainWindow.statusbar.label')
        self.statusbar.addPermanentWidget(self.statusbar.label)

        self.setStatusBar(self.statusbar)

        # dialogs

        self.script_error_dialog = ScriptErrorDialog(self)

    def patch_dark_stylesheet(self, stylesheet: str) -> str:
        return stylesheet + 'QGraphicsView { border: 0px; padding: 0px; }'

    def load_script(
        self, script_path: Path, external_args: List[Tuple[str, str]] | None = None, reloading: bool = False
    ) -> None:
        self.external_args = external_args or []

        self.toolbars.playback.stop()
        self.setWindowTitle('VSPreview: %s %s' % (script_path, self.external_args))

        self.statusbar.label.setText('Evaluating')
        self.script_path = script_path

        sys.path.append(str(self.script_path.parent))

        # Rewrite args so external args will be forwarded correctly
        try:
            argv_orig = sys.argv
            sys.argv = [script_path.name]
        except AttributeError:
            pass

        try:
            exec(
                self.script_path.read_text(encoding='utf-8'), dict([('__file__', sys.argv[0])] + self.external_args)
            )
        except BaseException as e:
            self.script_exec_failed = True
            logging.error(e)

            te = TracebackException.from_exception(e)
            # remove the first stack frame, which contains our exec() invocation
            del te.stack[0]

            # replace <string> with script path only for the first stack frames
            # in order to keep intact exec() invocations down the stack
            # that we're not concerned with
            for i, frame in enumerate(te.stack):
                if frame.filename == '<string>':
                    te.stack[i] = FrameSummary(
                        str(self.script_path), frame.lineno, frame.name
                    )
                else:
                    break
            logging.error(''.join(te.format()))

            return self.handle_script_error(
                '\n'.join([
                    'An error occured while evaluating script:',
                    str(e), 'See console output for details.'
                ])
            )
        finally:
            sys.argv = argv_orig
            sys.path.pop()

        self.script_exec_failed = False

        if len(vs.get_outputs()) == 0:
            logging.error('Script has no outputs set.')
            self.handle_script_error('Script has no outputs set.')
            return

        self.current_storage_path = self.config_dir / (self.script_path.stem + '.yml')

        if not self.current_storage_path.exists():
            self.current_storage_path = self.script_path.with_suffix('.yml')

        self.storage_not_found = not self.current_storage_path.exists()

        if self.storage_not_found:
            self.load_storage()

        if not reloading:
            self.toolbars.main.rescan_outputs()
            self.toolbars.playback.rescan_outputs()

        if not self.storage_not_found:
            self.load_storage()

        self.toolbars.misc.autosave_timer.start(self.AUTOSAVE_INTERVAL)

        if not reloading:
            self.switch_output(self.OUTPUT_INDEX)

    def load_storage(self) -> None:
        if self.storage_not_found:
            logging.info('No storage found. Using defaults.')
        else:
            try:
                with self.current_storage_path.open('r', encoding='utf-8') as storage_file:
                    yaml.load(storage_file, Loader=yaml.CLoader)  # type: ignore
            except yaml.YAMLError as exc:
                if isinstance(exc, yaml.MarkedYAMLError):
                    logging.warning(
                        'Storage parsing failed on line {} column {}. Using defaults.'
                        .format(exc.problem_mark.line + 1, exc.problem_mark.column + 1)
                    )
                else:
                    logging.warning('Storage parsing failed. Using defaults.')

        if self.settings.color_management_enabled:
            assert self.app
            self.current_screen = self.app.desktop().screenNumber(self)
            self.update_display_profile()

        self.statusbar.label.setText('Ready')

    def init_outputs(self) -> None:
        self.graphics_scene.clear()
        for output in self.outputs:
            frame_image = output.render_frame(output.last_showed_frame)

            raw_frame_item = self.graphics_scene.addPixmap(frame_image)
            raw_frame_item.hide()

            output.graphics_scene_item = GraphicsImageItem(raw_frame_item)

    def reload_script(self) -> None:
        if not self.script_exec_failed:
            self.toolbars.misc.save_sync()
        elif self.settings.autosave_control.value() != Time(seconds=0):
            self.toolbars.misc.save()

        vs.clear_outputs()
        self.graphics_scene.clear()

        self.outputs.clear()
        get_policy().reload_core()
        gc.collect(generation=0)
        gc.collect(generation=1)
        gc.collect(generation=2)

        self.load_script(self.script_path, reloading=True)

        self.show_message('Reloaded successfully')

    def switch_frame(
        self, pos: Frame | Time | int | None, *, render_frame: bool | Tuple[vs.VideoFrame, vs.VideoFrame | None] = True
    ) -> None:
        if pos is None:
            logging.debug('switch_frame: position is None!')
            return

        frame = Frame(pos)
        self.current_output.frame_to_show = Frame(frame)

        if frame > self.current_output.end_frame:
            return

        if render_frame:
            if not isinstance(render_frame, bool):
                self.current_output.render_frame(frame, *render_frame, output_colorspace=self.display_profile)
            else:
                self.current_output.render_frame(frame, output_colorspace=self.display_profile)

        self.current_output.last_showed_frame = frame

        self.timeline.set_position(frame)
        self.toolbars.main.on_current_frame_changed(frame)
        for toolbar in self.toolbars:
            if hasattr(toolbar, 'on_current_frame_changed'):
                toolbar.on_current_frame_changed(frame)

        self.statusbar.frame_props_label.setText(self.STATUS_FRAME_PROP(self.current_output.props))

    def switch_output(self, value: int | VideoOutput) -> None:
        if len(self.outputs) == 0:
            return
        if isinstance(value, VideoOutput):
            index = self.outputs.index_of(value)
        else:
            index = value

        if index < 0 or index >= len(self.outputs):
            return

        prev_index = self.toolbars.main.outputs_combobox.currentIndex()

        self.toolbars.playback.stop()

        # current_output relies on outputs_combobox
        self.toolbars.main.on_current_output_changed(index, prev_index)
        self.timeline.set_end_frame(self.current_output.end_frame)

        if self.current_output.frame_to_show is not None:
            self.current_frame = self.current_output.frame_to_show
        elif self.current_output.last_showed_frame:
            self.current_frame = self.current_output.last_showed_frame
        else:
            self.current_frame = Frame(0)

        for output in self.outputs:
            output.graphics_scene_item.hide()

        self.current_output.graphics_scene_item.show()
        self.graphics_scene.setSceneRect(QRectF(self.current_output.graphics_scene_item.pixmap().rect()))
        self.timeline.update_notches()

        for toolbar in self.toolbars:
            if hasattr(toolbar, 'on_current_output_changed'):
                toolbar.on_current_output_changed(index, prev_index)

        self.update_statusbar_output_info()

    @property
    def current_output(self) -> VideoOutput:
        return cast(VideoOutput, self.toolbars.main.outputs_combobox.currentData())

    @current_output.setter
    def current_output(self, value: VideoOutput) -> None:
        self.switch_output(self.outputs.index_of(value))

    @property
    def current_frame(self) -> Frame:
        return self.current_output.last_showed_frame or Frame(0)

    @current_frame.setter
    def current_frame(self, value: Frame) -> None:
        self.switch_frame(value)

    @property
    def outputs(self) -> VideoOutputs:
        return cast(VideoOutputs, self.toolbars.main.outputs)

    def handle_script_error(self, message: str) -> None:
        self.script_error_dialog.label.setText(message)
        self.script_error_dialog.open()

    def on_wheel_scrolled(self, steps: int) -> None:
        new_index = self.toolbars.main.zoom_combobox.currentIndex() + steps
        if new_index < 0:
            new_index = 0
        elif new_index >= len(self.toolbars.main.zoom_levels):
            new_index = len(self.toolbars.main.zoom_levels) - 1
        self.toolbars.main.zoom_combobox.setCurrentIndex(new_index)

    def on_timeline_clicked(self, start: int) -> None:
        if self.toolbars.playback.play_timer.isActive():
            self.toolbars.playback.stop()
            self.switch_frame(start)
            self.toolbars.playback.play()
        else:
            self.switch_frame(start)

    def update_display_profile(self) -> None:
        if sys.platform == 'win32':
            if _imagingcms is None:
                return

            assert self.app

            screen_name = self.app.screens()[self.current_screen].name()
            dc = win32gui.CreateDC(screen_name, None, None)

            logging.info('Changed screen: {}'.format(screen_name))

            icc_path = _imagingcms.get_display_profile_win32(dc, 1)
            if icc_path is not None:
                with open(icc_path, 'rb') as icc:
                    self.display_profile = QColorSpace.fromIccProfile(icc.read())

        if hasattr(self, 'current_output') and self.display_profile is not None:
            self.switch_frame(self.current_frame)

    def show_message(self, message: str) -> None:
        self.statusbar.showMessage(
            message, round(float(self.settings.statusbar_message_timeout) * 1000)
        )

    def update_statusbar_output_info(self, output: VideoOutput | None = None) -> None:
        output = output or self.current_output
        fmt = output.source.clip.format
        assert fmt

        self.statusbar.total_frames_label.setText('{} frames '.format(output.total_frames))
        self.statusbar.duration_label.setText('{} '.format(output.total_time))
        self.statusbar.resolution_label.setText('{}x{} '.format(output.width, output.height))
        self.statusbar.pixel_format_label.setText('{} '.format(fmt.name))
        if output.fps_den != 0:
            self.statusbar.fps_label.setText(
                '{}/{} = {:.3f} fps '.format(output.fps_num, output.fps_den, output.fps_num / output.fps_den)
            )
        else:
            self.statusbar.fps_label.setText('{}/{} fps '.format(output.fps_num, output.fps_den))

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.LayoutRequest:
            self.timeline.full_repaint()

        return super().event(event)

    # misc methods
    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.graphics_view.setSizePolicy(self.EVENT_POLICY)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.settings.autosave_control.value() != Time(seconds=0) and self.save_on_exit:
            self.toolbars.misc.save()

        self.reload_signal.emit()

    def moveEvent(self, _move_event: QMoveEvent) -> None:
        if self.settings.color_management_enabled:
            assert self.app
            screen_number = self.app.desktop().screenNumber(self)
            if self.current_screen != screen_number:
                self.current_screen = screen_number
                self.update_display_profile()

    def __getstate__(self) -> Mapping[str, Any]:
        return {
            attr_name: getattr(self, attr_name)
            for attr_name in self.storable_attrs
        } | {
            'timeline_mode': self.timeline.mode,
            'window_geometry': bytes(cast(bytearray, self.saveGeometry())),
            'window_state': bytes(cast(bytearray, self.saveState()))
        }

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        # toolbars is singleton, so it initialize itself right in its __setstate__()
        try_load(state, 'timeline_mode', str, self.timeline.mode)
        try_load(state, 'window_geometry', bytes, self.restoreGeometry)
        try_load(state, 'window_state', bytes, self.restoreState)
