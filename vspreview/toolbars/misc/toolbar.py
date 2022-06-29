from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any, Mapping

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QFileDialog, QLabel, QSpacerItem

from ...core import (
    AbstractMainWindow, AbstractToolbar, CheckBox, CroppingInfo, HBoxLayout,
    LineEdit, PushButton, SpinBox, Stretch, Time, Timer, VBoxLayout, ViewMode, try_load
)
from ...core.custom import ComboBox, Switch
from ...models import GeneralModel
from ...utils import qt_silent_call, video_heuristics
from .settings import MiscSettings


class MiscToolbar(AbstractToolbar):
    __slots__ = (
        'autosave_timer', 'reload_script_button',
        'save_storage_button', 'autosave_checkbox',
        'save_template_lineedit',
        'show_debug_checkbox', 'save_frame_as_button',
        'toggle_button', 'save_file_types', 'copy_frame_button',
        'crop_top_spinbox', 'crop_left_spinbox', 'crop_width_spinbox',
        'crop_bottom_spinbox', 'crop_right_spinbox', 'crop_height_spinbox',
        'crop_active_switch', 'crop_mode_combox', 'crop_copycommand_button',
        'view_mode_layout', 'view_mode_combox'
    )

    def __init__(self, main: AbstractMainWindow) -> None:
        super().__init__(main, MiscSettings())

        self.setup_ui()

        self.autosave_timer = Timer(timeout=self.main.dump_storage_async)

        self.save_file_types = {'Single Image (*.png)': self.save_as_png}

        self.main.reload_signal.connect(self.autosave_timer.stop)
        self.main.settings.autosave_control.valueChanged.connect(self.on_autosave_interval_changed)

        self.add_shortcuts()

        self.set_qobject_names()

    def setup_ui(self) -> None:
        super().setup_ui()

        self.reload_script_button = PushButton('Reload Script', self, clicked=self.main.reload_script)

        self.save_storage_button = PushButton(
            'Save Storage', self, clicked=partial(self.main.dump_storage_async, manually=True)
        )

        self.autosave_checkbox = CheckBox('Autosave', self, checked=True)

        self.copy_frame_button = PushButton('Copy Frame', self, clicked=self.copy_frame_to_clipboard)

        self.save_frame_as_button = PushButton('Save Frame as', self, clicked=self.on_save_frame_as_clicked)

        self.save_template_lineedit = LineEdit(
            self.settings.SAVE_TEMPLATE, self, tooltip='''
                Available placeholders:
                    {format}, {fps_den}, {fps_num}, {frame},
                    {height}, {index}, {matrix}, {primaries}, {range},
                    {script_name}, {total_frames}, {transfer}, {width}.
                Frame props can be accessed as well using their names.
            '''.replace(' ' * 16, ' ').strip()
        )

        self.show_debug_checkbox = CheckBox('Show Debug Toolbar', self, stateChanged=self.on_show_debug_changed)

        VBoxLayout(self.hlayout, [
            HBoxLayout([self.autosave_checkbox, self.get_separator(), self.show_debug_checkbox, Stretch()]),
            HBoxLayout([
                self.reload_script_button, self.get_separator(),
                self.save_storage_button, self.get_separator(),
                self.copy_frame_button, Stretch()
            ]),
            HBoxLayout([self.save_frame_as_button, self.save_template_lineedit, Stretch()])
        ])

        self.view_mode_combox = ComboBox[str](
            self, model=GeneralModel[str]([str(x.value) for x in ViewMode], False),
            currentIndex=0, sizeAdjustPolicy=QComboBox.AdjustToContents
        )
        self.view_mode_combox.currentTextChanged.connect(
            lambda mode: self.main.change_video_viewmode(ViewMode(mode))
        )

        self.view_mode_layout = VBoxLayout(self.hlayout, [
            HBoxLayout([QLabel('View mode:'), self.view_mode_combox]),
        ])

        self.view_mode_layout.setAlignment(Qt.AlignTop)

        self.hlayout.addStretch()
        self.hlayout.addStretch()

        self.crop_active_switch = Switch(10, 22, checked=True, clicked=self.crop_active_onchange)

        self.crop_top_spinbox = SpinBox(None, 0, 2 ** 16, valueChanged=self.crop_top_onchange)
        self.crop_left_spinbox = SpinBox(None, 0, 2 ** 16, valueChanged=self.crop_left_onchange)
        self.crop_bottom_spinbox = SpinBox(None, 0, 2 ** 16, valueChanged=self.crop_bottom_onchange)
        self.crop_right_spinbox = SpinBox(None, 0, 2 ** 16, valueChanged=self.crop_right_onchange)
        self.crop_width_spinbox = SpinBox(None, 1, 2 ** 16, valueChanged=self.crop_width_onchange)
        self.crop_height_spinbox = SpinBox(None, 1, 2 ** 16, valueChanged=self.crop_height_onchange)

        self.crop_copycommand_button = PushButton('Copy cropping command', clicked=self.crop_copycommand_onclick)

        self.crop_mode_combox = ComboBox[str](
            self, model=GeneralModel[str](['relative', 'absolute']),
            currentIndex=0, sizeAdjustPolicy=QComboBox.AdjustToContents
        )
        self.crop_mode_combox.currentIndexChanged.connect(self.crop_mode_onchange)

        self.crop_active_switch.click()

        HBoxLayout(self.hlayout, [
            VBoxLayout([
                HBoxLayout([
                    QLabel('Top'), self.crop_top_spinbox, QSpacerItem(35, 10)
                ], alignment=Qt.AlignCenter, spacing=0),
                HBoxLayout([
                    QLabel('Left'), self.crop_left_spinbox,
                    self.crop_active_switch,
                    self.crop_right_spinbox, QLabel('Right')
                ], alignment=Qt.AlignCenter, spacing=5),
                HBoxLayout([
                    QLabel('Bottom'), self.crop_bottom_spinbox, QSpacerItem(51, 10)
                ], alignment=Qt.AlignCenter, spacing=0)
            ]),
            VBoxLayout([
                HBoxLayout([QLabel('Cropping Type:'), self.crop_mode_combox]),
                HBoxLayout([
                    QLabel('Width'), self.crop_width_spinbox,
                    QLabel('Height'), self.crop_height_spinbox
                ], spacing=0),
                HBoxLayout([self.crop_copycommand_button])
            ])
        ])

    def add_shortcuts(self) -> None:
        self.main.add_shortcut(Qt.CTRL + Qt.Key_R, self.main.reload_script)
        self.main.add_shortcut(Qt.ALT + Qt.Key_S, self.save_storage_button.click)
        self.main.add_shortcut(Qt.CTRL + Qt.Key_S, self.copy_frame_button.click)
        self.main.add_shortcut(Qt.SHIFT + Qt.Key_S, self.save_frame_as_button.click)
        self.main.add_shortcut(
            Qt.SHIFT + Qt.Key_F, lambda: self.view_mode_combox.setCurrentText(
                ViewMode.FFTSPECTRUM if self.main.current_viewmode != ViewMode.FFTSPECTRUM else ViewMode.NORMAL
            )
        )
        self.main.add_shortcut(
            Qt.SHIFT + Qt.Key_D, lambda: self.view_mode_combox.setCurrentText(
                ViewMode.DESCALING_HELP if self.main.current_viewmode != ViewMode.DESCALING_HELP else ViewMode.NORMAL
            )
        )

    def copy_frame_to_clipboard(self) -> None:
        self.main.clipboard.setPixmap(
            self.main.current_output.graphics_scene_item.pixmap()
        )
        self.main.show_message('Current frame successfully copied to clipboard')

    def on_autosave_interval_changed(self, new_value: Time | None) -> None:
        if new_value is None:
            return
        if new_value == Time(seconds=0):
            self.autosave_timer.stop()
        else:
            self.autosave_timer.start(round(float(new_value) * 1000))

    def on_save_frame_as_clicked(self, checked: bool | None = None) -> None:
        curr_out = self.main.current_output.source.clip
        fmt = curr_out.format
        assert fmt

        filter_str = ''.join([file_type + ';;' for file_type in self.save_file_types.keys()])[0:-2]

        template = self.main.toolbars.misc.save_template_lineedit.text()

        props = self.main.current_output.props

        heuristics = video_heuristics(self.main.current_output.source.clip, props, string_only=True)

        substitutions = {
            **props, **heuristics,
            'format': fmt.name,
            'fps_den': self.main.current_output.fps_den,
            'fps_num': self.main.current_output.fps_num,
            'width': self.main.current_output.width,
            'height': self.main.current_output.height,
            'script_name': self.main.script_path.stem,
            'index': self.main.current_output.index,
            'frame': self.main.current_output.last_showed_frame,
            'total_frames': self.main.current_output.total_frames
        }

        try:
            suggested_path_str = template.format(**substitutions)
        except KeyError:
            self.main.show_message('Save name template is invalid')
            return

        save_path_str, file_type = QFileDialog.getSaveFileName(
            self.main, 'Save as', suggested_path_str, filter_str
        )
        try:
            self.save_file_types[file_type](Path(save_path_str))
        except KeyError:
            pass

    def on_show_debug_changed(self, state: Qt.CheckState) -> None:
        if state == Qt.Checked:
            self.main.toolbars.debug.toggle_button.setVisible(True)
        elif state == Qt.Unchecked:
            if self.main.toolbars.debug.toggle_button.isChecked():
                self.main.toolbars.debug.toggle_button.click()
            self.main.toolbars.debug.toggle_button.setVisible(False)

    def save_as_png(self, path: Path) -> None:
        self.main.current_output.graphics_scene_item.pixmap().save(
            str(path), 'PNG', self.main.settings.png_compression_level
        )

    def on_current_output_changed(self, index: int, prev_index: int) -> None:
        if index != prev_index:
            self.update_crop(prev_index)

        curr = self.main.current_output
        crop = curr.crop_values

        self.crop_top_spinbox.setMaximum(curr.height - 1)
        self.crop_bottom_spinbox.setMaximum(curr.height - 1)
        self.crop_left_spinbox.setMaximum(curr.width - 1)
        self.crop_right_spinbox.setMaximum(curr.width - 1)
        self.crop_width_spinbox.setMaximum(curr.width)
        self.crop_height_spinbox.setMaximum(curr.height)

        qt_silent_call(self.crop_top_spinbox.setValue, crop.top)
        qt_silent_call(self.crop_bottom_spinbox.setValue, curr.height - crop.height - crop.top)
        qt_silent_call(self.crop_left_spinbox.setValue, crop.left)
        qt_silent_call(self.crop_right_spinbox.setValue, curr.width - crop.width - crop.left)
        qt_silent_call(self.crop_width_spinbox.setValue, crop.width)
        qt_silent_call(self.crop_height_spinbox.setValue, crop.height)

        self.crop_active_switch.setChecked(not crop.active)
        self.crop_active_switch.click()

        self.crop_mode_combox.setCurrentIndex(int(crop.is_absolute))

    def update_crop(self, index: int | None = None) -> None:
        if not hasattr(self.main, 'current_output'):
            return

        output = self.main.current_output if index is None else self.main.outputs[index]

        output.update_graphic_item(None, CroppingInfo(
            self.crop_top_spinbox.value(), self.crop_left_spinbox.value(),
            self.crop_width_spinbox.value(), self.crop_height_spinbox.value(),
            self.crop_active_switch.isChecked(), bool(self.crop_mode_combox.currentIndex())
        ))

    def crop_active_onchange(self, checked: bool) -> None:
        is_absolute = not not self.crop_mode_combox.currentIndex()

        self.crop_top_spinbox.setEnabled(checked)
        self.crop_left_spinbox.setEnabled(checked)

        self.crop_bottom_spinbox.setEnabled(checked and not is_absolute)
        self.crop_right_spinbox.setEnabled(checked and not is_absolute)

        self.crop_width_spinbox.setEnabled(checked and is_absolute)
        self.crop_height_spinbox.setEnabled(checked and is_absolute)

        self.crop_mode_combox.setEnabled(checked)

        self.crop_copycommand_button.setEnabled(checked)

        self.update_crop()

    def crop_mode_onchange(self, crop_mode_idx: int) -> None:
        is_absolute = bool(crop_mode_idx)

        self.crop_bottom_spinbox.setEnabled(not is_absolute)
        self.crop_right_spinbox.setEnabled(not is_absolute)

        self.crop_width_spinbox.setEnabled(is_absolute)
        self.crop_height_spinbox.setEnabled(is_absolute)

        self.update_crop()

    def crop_top_onchange(self, value: int) -> None:
        if not self.crop_active_switch.isChecked():
            return

        height = self.main.current_output.height
        offset = height - self.crop_bottom_spinbox.value()

        if offset - value < 1:
            qt_silent_call(self.crop_top_spinbox.setValue, offset - 1)
            return

        qt_silent_call(self.crop_height_spinbox.setValue, offset - value)

        self.update_crop()

    def crop_left_onchange(self, value: int) -> None:
        if not self.crop_active_switch.isChecked():
            return

        width = self.main.current_output.width
        offset = width - self.crop_right_spinbox.value()

        if offset - value < 1:
            qt_silent_call(self.crop_left_spinbox.setValue, offset - 1)
            return

        qt_silent_call(self.crop_width_spinbox.setValue, offset - value)

        self.update_crop()

    def crop_bottom_onchange(self, value: int) -> None:
        if not self.crop_active_switch.isChecked():
            return

        if self.crop_mode_combox.currentIndex():
            return

        height = self.main.current_output.height
        offset = height - self.crop_top_spinbox.value()

        if offset - value < 1:
            qt_silent_call(self.crop_bottom_spinbox.setValue, offset - 1)
            return

        qt_silent_call(self.crop_height_spinbox.setValue, offset - value)

        self.update_crop()

    def crop_right_onchange(self, value: int) -> None:
        if not self.crop_active_switch.isChecked():
            return

        if self.crop_mode_combox.currentIndex():
            return

        width = self.main.current_output.width
        offset = width - self.crop_left_spinbox.value()

        if offset - value < 1:
            qt_silent_call(self.crop_right_spinbox.setValue, offset - 1)
            return

        qt_silent_call(self.crop_width_spinbox.setValue, offset - value)

        self.update_crop()

    def crop_width_onchange(self, value: int) -> None:
        if not self.crop_active_switch.isChecked():
            return

        if self.crop_mode_combox.currentIndex():
            width = self.main.current_output.width
            offset = width - self.crop_left_spinbox.value()

            qt_silent_call(self.crop_right_spinbox.setValue, offset - value)

            if offset - value < 1:
                qt_silent_call(self.crop_left_spinbox.setValue, width - value)

        self.update_crop()

    def crop_height_onchange(self, value: int) -> None:
        if not self.crop_active_switch.isChecked():
            return

        if self.crop_mode_combox.currentIndex():
            height = self.main.current_output.height
            offset = height - self.crop_top_spinbox.value()

            qt_silent_call(self.crop_bottom_spinbox.setValue, offset - value)

            if offset - value < 1:
                qt_silent_call(self.crop_top_spinbox.setValue, height - value)

        self.update_crop()

    def crop_copycommand_onclick(self) -> None:
        is_absolute = self.crop_mode_combox.currentIndex()

        crop_top = self.crop_top_spinbox.value()
        crop_left = self.crop_left_spinbox.value()

        if not is_absolute:
            crop_bottom = self.crop_bottom_spinbox.value()
            crop_right = self.crop_right_spinbox.value()

            text = f'.std.Crop({crop_left}, {crop_right}, {crop_top}, {crop_bottom})'
        else:
            crop_width = self.crop_width_spinbox.value()
            crop_height = self.crop_height_spinbox.value()

            text = f'.std.CropAbs({crop_width}, {crop_height}, {crop_left}, {crop_top})'

        self.main.clipboard.setText(text)

    def __getstate__(self) -> Mapping[str, Any]:
        return super().__getstate__() | {
            'save_file_name_template': self.save_template_lineedit.text(),
            'show_debug': self.show_debug_checkbox.isChecked()
        }

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        try_load(state, 'save_file_name_template', str, self.save_template_lineedit.setText)
        try_load(state, 'show_debug', bool, self.show_debug_checkbox.setChecked)
        super().__setstate__(state)
