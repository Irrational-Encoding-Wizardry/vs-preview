vs-preview Documentation
------------------------

About
-----

``vs-preview`` is a standalone previewer for VapourSynth scripts.
It's meant to be paired with an IDE that has an integrated terminal,
like Visual Studio Code.
``vs-preview`` is the de facto VapourSynth previewer featuring many core features
to help make writing your VapourSynth scripts as easy as possible.

Features
^^^^^^^^

* Simple design that is easy to understand for newer users
* Seamless integration with any IDE (code editor) that has an integrated terminal
* Video previewer to easily check your VapourSynth filtering
* Video playback (with audio support!)
* AviSynth support
* Supports multiple output nodes, quickly check different filtered outputs
* Scening tools to help faciliate easier scene-filtering
* Built-in cropping tool
* Viewing modes to help your filtering, like FFTSpectrum
* Descaling menu to help with all your descaling needs
* Bookmarking to easily jump between frames
* Pipette tool
* Comparison output, upload comparisons to `slow.pics <https://slow.pics/>`_ straight from your previewer
* Benchmarking

and much, much more!

.. automodule:: vspreview
    :members:
    :undoc-members:
    :show-inheritance:


.. toctree::
    :maxdepth: 4
    :caption: How to use

    installation/install_vspreview
    installation/install_vscode
    installation/install_vim

.. toctree::
    :maxdepth: 4
    :caption: Accessibility

    accessibility/keybinds.rst
    accessibility/placeholders.rst

.. toctree::
    :maxdepth: 4
    :caption: Toolbars

    toolbars/main
    toolbars/playback
    toolbars/scening


Special Credits
---------------
| A special thanks to everyone who has contributed to ``vs-preview``.
| `A comprehensive list of contributors can be found here. <https://github.com/Irrational-Encoding-Wizardry/vs-preview/graphs/contributors>`_


.. toctree::
    :maxdepth: 4
    :caption: Changelogs

    changelogs/changelogs
