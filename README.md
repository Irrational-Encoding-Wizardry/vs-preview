# Standalone previewer for VapourSynth scripts

Fork of Endilll's [vapoursynth-preview](https://github.com/Endilll/vapoursynth-preview) (not maintained anymore)

This program is meant to be paired with a code editor with integrated terminal like Visual Studio Code.

# Prerequisites

1. [Python](https://www.Python.org/downloads) (3.9+ required)
    * Make sure to install Python to your `PATH`.
1. [VapourSynth](https://github.com/vapoursynth/vapoursynth/releases) (R57+ required, R58+ required for audio)

**Note:** If you're on Python 3.10, you'll need VapourSynth R58.

# Installation

Install latest stable via pypi:
```bash
pip install vspreview
```


Install latest git:
```bash
pip install -U git+https://github.com/Irrational-Encoding-Wizardry/vs-preview.git
```

# Usage

It can be used by running `vspreview script.vpy` or your preferred way in [your IDE](#ide-integration).

[Keyboard Shortcuts](https://github.com/Irrational-Encoding-Wizardry/vs-preview/tree/master/docs/shortcuts.md)

[Saved Frame Filename Variables](https://github.com/Irrational-Encoding-Wizardry/vs-preview/tree/master/docs/save_frame_placeholders.md)

# IDE Integration

* [Notepad++](https://github.com/Irrational-Encoding-Wizardry/vs-preview/tree/master/docs/installation/install_notepad++.rst)
* [Vim](https://github.com/Irrational-Encoding-Wizardry/vs-preview/tree/master/docs/installation/install_vim.rst)
* [Visual Studio Code](https://github.com/Irrational-Encoding-Wizardry/vs-preview/tree/master/docs/installation/install_vscode.rst)
