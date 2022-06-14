With Visual Studio Code
-----------------------

``vs-preview`` is intended to work with an IDE that can use an integrated terminal.
One IDE that can do that is Microsoft's free code editor, `Visual Studio Code <https://code.visualstudio.com>`_.

Requirements
^^^^^^^^^^^^

The following programs must be installed before you begin:

* `Visual Studio Code <https://code.visualstudio.com/download>`_

Configuring Visual Studio Code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. If you have not already, install the `Python Extension <https://marketplace.visualstudio.com/items?itemName=ms-python.python>`_
2. Associate ``.vpy`` files with Python
    1. Open Visual Studio Code's setting menu via ``File > Preferences > Settings`` or the ``Ctrl +`` hotkey
    2. Search for ``files.associations``
    3. Click the "Add Item" button
    4. Fill in ``*.vpy`` for the "Item" field
    5. Fill in ``python`` for the "Value" field
    6. Click the "OK" button

Configuring the launch file
^^^^^^^^^^^^^^^^^^^^^^^^^^^

To easily run ``vs-preview`` on your script,
we'll create a "launch" file.

1. Open Visual Studio Code
2. Press F1 and search for ``Preferences: Open Keyboard Shortcuts (JSON)``
3. Paste the following code in the file, within the curly braces:

.. code-block:: json

    // Binding for previewing a VapourSynth filterchain using vs-preview
    {
        "key": "F5",
        "command": "workbench.action.terminal.sendSequence",
        "args": {
            "text": "python -m vspreview \"${file}\"\u000D"
        },
        "when": "resourceExtname == '.vpy'"
    }

You can change the "key" to whatever keybind you prefer.

Running your scripts
^^^^^^^^^^^^^^^^^^^^

You can now open the VapourSynth script you want to run in Visual Studio Code
and run ``vs-preview`` by pressing ``F5`` or the ▷ button in "Run and Debug".

If everything works properly,
it should open up a terminal at the bottom of the screen
and start printing something like this:

.. code-block:: powershell

     PS G:\project>& 'D:\Python39\python.exe' 'c:\Users\...\debugpy\launcher' '62134' '--' '~/vapoursynth-preview/run.py' 'G:\project\episode_1_720p.vpy'
    2021-03-19 03:43:03.324: INFO: QSS file successfuly loaded.
    2021-03-19 03:43:03.328: INFO: Found application patches to be applied.
    2021-03-19 03:43:04.207: INFO: No storage found. Using defaults.

If there's an error with your script,
it will print it in the terminal.
If your script is fine,
it will open ``vs-preview`` with the current script.
