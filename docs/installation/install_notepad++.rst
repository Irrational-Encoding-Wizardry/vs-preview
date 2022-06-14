With Notepad++
--------------

``vs-preview`` is intended to work with an IDE that can use an integrated terminal.
One IDE that can do that is Notepad++.

Requirements
^^^^^^^^^^^^

The following programs must be installed before you begin:

* `Notepad++ <https://notepad-plus-plus.org/downloads/>`_

Configuring Notepad++
^^^^^^^^^^^^^^^^^^^^^

1. Associate ``.vpy``` files with Notepad++
    1. Right-click a ``.vpy`` file and press ``Open with > Choose another app``
    2. Check "Always use this app to open .vpy files"
    3. Scroll down and click "More apps", then "Look for another app on this PC"
    4. Browse to your Notepad++ install location and press "Open"

.. note::

   To get correct syntax highlighting, go to ``Settings > Style Configurator`` and add ``.vpy`` to the Python extensions.

Running your script
^^^^^^^^^^^^^^^^^^^

.. note::

    The easiest way to run your .vpy file in Notepad is by creating a Run preset.

1. Go to ``Run > Run`` or press ``F5``.
2. Add ``vspreview "$(FULL_CURRENT_PATH)"`` and save it as ``vspreview``, with whatever shortcut you like.

You can now open the VapourSynth script you want to run in Notepad++
and run ``vs-preview`` by pressing your shortcut.

If everything works properly,
it should open up a terminal at the bottom of the screen
and start printing something like this:

.. code-block:: powershell

    2021-03-19 03:43:03.324: INFO: QSS file successfuly loaded.
    2021-03-19 03:43:03.328: INFO: Found application patches to be applied.
    2021-03-19 03:43:04.207: INFO: No storage found. Using defaults.

If there's an error with your script,
it will print it in the terminal.
If your script is fine,
it will open ``vs-preview`` with the current script.
