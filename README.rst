enums.py
========

*Less sophisticated, less restrictive, more magical and funky!*

.. image:: https://img.shields.io/pypi/l/enums.py.svg
    :target: https://opensource.org/licenses/MIT
    :alt: Project License

.. image:: https://img.shields.io/pypi/v/enums.py.svg
    :target: https://pypi.python.org/pypi/enums.py
    :alt: PyPI Library Version

.. image:: https://img.shields.io/pypi/pyversions/enums.py.svg
    :target: https://pypi.python.org/pypi/enums.py
    :alt: Required Python Versions

.. image:: https://img.shields.io/pypi/status/enums.py.svg
    :target: https://github.com/NeKitDS/enums.py/
    :alt: Project Development Status

.. image:: https://img.shields.io/pypi/dm/enums.py.svg
    :target: https://pypi.python.org/pypi/enums.py
    :alt: Library Downloads/Month

.. image:: https://img.shields.io/endpoint.svg?url=https%3A%2F%2Fshieldsio-patreon.herokuapp.com%2Fnekit%2Fpledges
    :target: https://patreon.com/nekit
    :alt: Patreon Page [Support]

enums.py is a module that implements enhanced enums for Python.

Below are many examples of using this module.

Importing Functions
-------------------

Here are main classes that are used in enums:

.. code-block:: python3

    from enums import Enum, Flag, auto, unique

Creating Enums
--------------

There are many ways to create enums.

This can be done in classical way:

.. code-block:: python3

    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

Like standard ``enum`` module, ``enums.py`` has ``auto`` class:

.. code-block:: python3

    class Color(Enum):
        RED = auto()
        GREEN = auto()
        BLUE = auto()

Enums can be created without explicit ``class`` usage:

.. code-block:: python3

    Color = Enum("Color", ["RED", "GREEN", "BLUE"])

Strings can also be used here:

.. code-block:: python3

    Color = Enum("Color", "RED GREEN BLUE")

You can also use keyword arguments in order to define members:

.. code-block:: python3

    Color = Enum("Color", RED=1, GREEN=2, BLUE=3)

Same with ``auto()``, of course:

.. code-block:: python3

    Color = Enum("Color", RED=auto(), GREEN=auto(), BLUE=auto())

All code snippets above produce Enum ``Color`` in the end, which has 3 members:

- ``<Color.RED: 1>``
- ``<Color.GREEN: 2>``
- ``<Color.BLUE: 3>``

Member Attributes
-----------------

Enum members have several useful attributes:

- *name*, which represents their actual name;
- *value*, which contains their value;
- *title*, which is more human-readable version of their *name*.

.. code-block:: python3

    print(Color.BLUE.name)  # BLUE
    print(Color.BLUE.value)  # 3
    print(Color.BLUE.title)  # Blue

Advanced Name/Value to Enum
---------------------------

Enums can be created from case insensetive strings:

.. code-block:: python3

    class Test(Enum):
        WEIRDTEST = 13

    test = Test.from_name("weird_test")

**Note that if two members have same case insensetive name version, last in wins!**

**Also keep in mind** ``Enum.from_name`` **will not work with composite flags!**

You can use ``Flag.from_args`` to create composite flag from multiple values/names:

.. code-block:: python3

    FileMode = Flag("FileMode", "NULL READ WRITE EXECUTE", start=0)
    FileMode.from_args("read", "write", "execute")  # <FileMode.READ|WRITE|EXECUTE: 7>
    FileMode.from_args(1, 2)  # <FileMode.READ|WRITE: 3>

There is also ``Enum.from_value``, which tries to use ``Enum.from_name`` if given value is string,
and otherwise (and if failed), it attempts by-value lookup. Also, this function accepts ``default``
argument, such that ``Enum.from_value(default)`` will be called on fail if ``default`` was given.

Example:

.. code-block:: python3

    class FileMode(Flag):
        NULL, READ, WRITE, EXECUTE = 0, 1, 2, 4

    FileMode.from_value(8, default=0)  # <FileMode.NULL: 0>
    FileMode.from_value("broken", "read")  # <FileMode.READ: 1>

Flag Enums
----------

``Flag`` is a special enum that focuses around supporting bitflags,
along with operations on them, such as **OR** ``|``, **AND** ``&``, **XOR** ``^`` and **NEG** ``~``.

.. code-block:: python3

    class FileMode(Flag):
        NULL = 0
        READ = 1
        WRITE = 2
        EXECUTE = 4

    # <FileMode.READ|WRITE: 3>
    READ_WRITE = FileMode.READ | FileMode.WRITE

    # <FileMode.READ: 1>
    READ = (FileMode.READ | FileMode.WRITE) & FileMode.READ

    # <FileMode.WRITE|EXECUTE: 6>
    WRITE_EXECUTE = FileMode.WRITE ^ FileMode.EXECUTE)

    # <FileMode.NULL: 0>
    NULL = FileMode.EXECUTE ^ FileMode.EXECUTE

    # <FileMode.READ|EXECUTE: 5>
    READ_EXECUTE = ~FileMode.WRITE

Integers can be used instead of enum members:

.. code-block:: python3

    READ_WRITE_EXECUTE = FileMode.NULL | 1 | 2 | 4

Type Restriction
----------------

Enum members can be restricted to have values of the same type:

.. code-block:: python3

    class OnlyInt(int, Enum):
        SOME = 1
        OTHER = "2"  # will be casted
        BROKEN = "broken"  # error will be raised on creation

Unique Enums
------------

Enum members can have aliases, for example:

.. code-block:: python3

    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3
        R, G, B = RED, GREEN, BLUE  # aliases

``enums.py`` has ``unique`` class decorator, that can be used
to check/identify that enum does not have aliases.

That is, the following snippet will error:

.. code-block:: python3

    @unique
    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3
        R, G, B = RED, GREEN, BLUE  # aliases

With the following exception:

.. code-block:: python3

    ValueError: Duplicates found in <enum 'Color'>: R -> RED, G -> GREEN, B -> BLUE.

Updating (Mutating) Enums
-------------------------

Unlike in standard ``enum`` module, enumerations can be mutated:

.. code-block:: python3

    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    Color.add_member("ALPHA", 0)  # <Color.ALPHA: 0>

Or using ``Enum.update()`` for several members:

.. code-block:: python3

    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    Color.update(ALPHA=0, BROKEN=-1)

Installing
----------

**Python 3.6 or higher is required**

To install the library, you can just run the following command:

.. code:: sh

    # Linux/OS X
    python3 -m pip install -U enums.py

    # Windows
    py -3 -m pip install -U enums.py

In order to install the library from source, you can do the following:

.. code:: sh

    $ git clone https://github.com/NeKitDS/enums.py
    $ cd enums.py
    $ python -m pip install -U .

Authors
-------

This project is mainly developed by `NeKitDS <https://github.com/NeKitDS>`_.
