Download vs-preview
-------------------

Requirements
^^^^^^^^^^^^

Before you begin using ``vs-preview``,
make sure you have the following programs installed:

* `Python 3.9 <https://www.python.org/downloads/>`_ or higher
* `VapourSynth 57 <https://github.com/vapoursynth/vapoursynth/releases/>`_ or higher
* `Git <https://git-scm.com/downloads/>`_ (Optional)

Downloading
^^^^^^^^^^^

To install ``vs-preview`` stable,
run the following command in a terminal:

.. code-block:: bash

    pip install vspreview -U

To install the nightly build,
run the following command instead.
Note that these may be unstable!

.. code-block:: bash

    pip install git+https://github.com/Irrational-Encoding-Wizardry/vs-preview.git -U

Updating
^^^^^^^^

You can update ``vs-preview`` by running the same command used to install it.
If you find it doesn't update when it should,
try running the following command instead:

.. code-block:: bash

    pip install vspreview -U --force-reinstall

Or this command for the nightly build:

.. code-block:: bash

    pip install git+https://github.com/Irrational-Encoding-Wizardry/vs-preview.git -U --force-reinstall
