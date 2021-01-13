.. _installation:

Installation
============

Requirements:
 * Python 3.8, 3.9


Install via pip
---------------

The simplest way to install the package is via ``pip``.


PyPI
~~~~

Install latest release from PyPI:

.. code-block::

    pip install discord-interactions.py


GitHub
~~~~~~

Install latest code directly from GitHub:

.. code-block::

    pip install git+https://github.com/LiBa001/discord-interactions.py

.. note::
    Installing from GitHub requires you to have Git installed on your computer.


----

If ``pip`` cannot be found (i.e. it's not in your system ``PATH``), use:

.. code-block::

    python -m pip install …

.. note::
    To install for a specific Python version use ``python3.x``.

    E.g. to install for Python 3.8, use ``python3.8 -m pip install …``

And if you're on Windows, it might me:

.. code-block::

    py -m pip install …


Install from source
-------------------

You can also manually clone the code from GitHub and then install it.

.. code-block:: bash

    git clone https://github.com/LiBa001/discord-interactions.py
    cd discord-interactions.py
    python3.8 setup.py install
