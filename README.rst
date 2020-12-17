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
    :target: https://github.com/nekitdev/enums.py
    :alt: Project Development Status

.. image:: https://img.shields.io/pypi/dm/enums.py.svg
    :target: https://pypi.python.org/pypi/enums.py
    :alt: Library Downloads/Month

.. image:: https://app.codacy.com/project/badge/Grade/5a7b36c3304d40818c5d8b4181fe8564
    :target: https://app.codacy.com/project/nekitdev/enums.py/dashboard
    :alt: Code Quality [Codacy]

.. image:: https://img.shields.io/coveralls/github/nekitdev/enums.py
    :target: https://coveralls.io/github/nekitdev/enums.py
    :alt: Code Coverage

.. image:: https://img.shields.io/endpoint.svg?url=https%3A%2F%2Fshieldsio-patreon.herokuapp.com%2Fnekit%2Fpledges
    :target: https://patreon.com/nekit
    :alt: Patreon Page [Support]

enums.py is a module that implements enhanced enums for Python.

**Incompatible with standard library enums!**

Below are many examples of using this module.

Importing
---------

Here are main classes and functions that are used in enums:

.. code-block:: python3

    from enums import Enum, Flag, IntEnum, IntFlag, Order, StrFormat, auto, unique

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

Enums with Arguments
--------------------

Enum members that have ``tuple`` values but do not subclass ``tuple``
are interpreted as values passed to ``__init__`` of their class:

.. code-block:: python3

    class Planet(Enum):
        MERCURY = (3.303e+23, 2.4397e6)
        VENUS   = (4.869e+24, 6.0518e6)
        EARTH   = (5.976e+24, 6.37814e6)
        MARS    = (6.421e+23, 3.3972e6)
        JUPITER = (1.9e+27,   7.1492e7)
        SATURN  = (5.688e+26, 6.0268e7)
        URANUS  = (8.686e+25, 2.5559e7)
        NEPTUNE = (1.024e+26, 2.4746e7)

        def __init__(self, mass: float, radius: float) -> None:
            self.mass = mass  # kg
            self.radius = radius  # m

        @property
        def surface_gravity(self) -> float:
            # universal gravitational constant
            G = 6.67300E-11  # m^3 kg^(-1) s^(-2)
            return G * self.mass / (self.radius * self.radius)

    print(Planet.EARTH.value)  # (5.976e+24, 6378140.0)
    print(Planet.EARTH.surface_gravity)  # 9.802652743337129

Iteration
---------

It is possible to iterate over unique enum members:

.. code-block:: python3

    Color = Enum("Color", RED=1, GREEN=2, BLUE=3)

    for color in Color:
        print(Color.title)

    # Red
    # Green
    # Blue

Or over all members, including aliases:

.. code-block:: python3

    Color = Enum("Color", RED=1, GREEN=2, BLUE=3, R=1, G=2, B=3)

    for name, color in Color.members.items():
        print(name, color.name)

    # RED RED
    # GREEN GREEN
    # BLUE BLUE
    # R RED
    # G GREEN
    # B BLUE

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

    Perm = Flag("Perm", "Z X W R", start=0)
    Perm.from_args("r", "w", "x")  # <Perm.R|W|X: 7>
    Perm.from_args(2, 4)  # <Perm.R|W: 6>

There is also ``Enum.from_value``, which tries to use ``Enum.from_name`` if given value is string,
and otherwise (and if failed), it attempts by-value lookup. Also, this function accepts ``default``
argument, such that ``Enum.from_value(default)`` will be called on fail if ``default`` was given.

Example:

.. code-block:: python3

    class Perm(Flag):
        Z, X, W, R = 0, 1, 2, 4

    Perm.from_value(8, default=0)  # <Perm.Z: 0>
    Perm.from_value("broken", "r")  # <Perm.R: 4>

Flag Enums
----------

``Flag`` is a special enum that focuses around supporting bitflags,
along with operations on them, such as **OR** ``|``, **AND** ``&``, **XOR** ``^`` and **NEG** ``~``.

.. code-block:: python3

    class Perm(Flag):
        Z = 0
        X = 1
        W = 2
        R = 4

    # <Perm.R|W: 6>
    RW = Perm.R | Perm.W

    # <Perm.R: 4>
    R = (Perm.R | Perm.W) & Perm.R

    # <Perm.W|X: 3>
    WX = Perm.W ^ Perm.X

    # <Perm.Z: 0>
    Z = Perm.X ^ Perm.X

    # <Perm.R|X: 5>
    RX = ~Perm.W

Integers can be used instead of enum members:

.. code-block:: python3

    RWX = Perm.Z | 1 | 2 | 4

Flag Combinations
-----------------

Flag members have ``Flag.decompose()`` method, which will include all named flags and all named combinations of flags that are in their value.

``str()`` and ``repr()`` on flags will use ``Flag.decompose()`` for composite flags that do not have names.

.. code-block:: python3

    class Color(StrFormat, Enum):
        RED = 1
        GREEN = 2
        BLUE = 4
        YELLOW = RED | GREEN
        MAGENTA = RED | BLUE
        CYAN = GREEN | BLUE

    # named combination
    print(repr(Color(3)))  # <Color.YELLOW: 3>

    # unnamed combination
    print(repr(Color(7)))  # <Color.CYAN|MAGENTA|BLUE|YELLOW|GREEN|RED: 7>

Type Restriction and Inheritance
--------------------------------

Enum members can be restricted to have values of the same type:

.. code-block:: python3

    class OnlyInt(IntEnum):
        SOME = 1
        OTHER = "2"  # will be casted
        BROKEN = "broken"  # error will be raised on creation

As well as inherit behavior from that type:

.. code-block:: python3

    class Access(IntFlag):
        NONE = 0
        SIMPLE = 1
        MAIN = 2

    FULL = Access.SIMPLE | Access.MAIN
    assert FULL > Access.MAIN
    print(FULL.bit_length())  # 2

Because ``IntEnum`` and ``IntFlag`` are subclasses of ``int``, they lose their membership when ``int`` operations are used with them:

.. code-block:: python3

    Access = IntFlag("Access", "NONE SIMPLE MAIN", start=0)

    print(repr(Access.NONE | Access.SIMPLE | Access.MAIN))  # <Access.MAIN|SIMPLE: 3>

    print(Access.SIMPLE + Access.MAIN)  # 3

Method Resolution Order
-----------------------

``enums.py`` requires the following definiton of new ``Enum`` subclass:

.. code-block:: python3

    EnumName([mixin_type, ...] [data_type] enum_type)

For example:

.. code-block:: python3

    class Value(Order, Enum):
        """Generic value that supports ordering."""

    class FloatValue(float, Value):
        """Float value that inherits Value."""

Here, ``FloatValue`` bases are going to be transformed into:

.. code-block:: python3

    Value, float, Order, Enum

Which allows us to preserve functions defined in enums or flags,
while still having *mixins* work nicely with overriding them.

Traits
------

``enums.py`` implements special *mixins*, called *Traits*.
Each Trait implements some functionality for enums, but does not subclass Enum.
Therefore they are pretty much useless on their own.

StrFormat
~~~~~~~~~

Default ``__format__`` of ``Enum`` will attempt to use ``__format__`` of member data type, if given:

.. code-block:: python3

    class Foo(IntEnum):
        BAR = 42

    print(f"{Foo.BAR}")  # 42

``StrFormat`` overwrites that behavior and uses ``str(member).__format__(format_spec)`` instead:

.. code-block:: python3

    class Foo(StrFormat, IntEnum):
        BAR = 42

    print(f"{Foo.BAR}")  # Foo.BAR

Order
~~~~~

``Order`` Trait implements ordering (``==``, ``!=``, ``<``, ``>``, ``<=`` and ``>=``) for Enum members.
This function will attempt to find member by value.

Example:

.. code-block:: python3

    class Grade(Order, Enum):
        A = 5
        B = 4
        C = 3
        D = 2
        F = 1

    print(Grade.A > Grade.C)  # True
    print(Grade.F <= Grade.D)  # True

    print(Grade.B == 4)  # True
    print(Grade.F >= 0)  # True

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

Class Keyword Arguments
-----------------------

Enum class knows 3 class keyword arguments:

- *auto_on_missing: bool*;
- *ignore: Union[str, Iterable[str]]*;
- *start: T*.

auto_on_missing
~~~~~~~~~~~~~~~

Boolean flag, if set to ``True`` (default is ``False``), allows to do something like:

.. code-block:: python3

    class Color(Enum, auto_on_missing=True):
        RED  # 1
        GREEN  # 2
        BLUE  # 3

    print(repr(Color.RED))  # <Color.RED: 1>

ignore
~~~~~~

Works same as putting ``enum_ignore`` inside the class (default is ``()`` (empty tuple)):

.. code-block:: python3

    class Time(Enum, ignore=("time_vars", "day")):
        time_vars = vars()
        for day in range(366):
            time_vars[f"day_{day}"] = day

    print(repr(Time.day_365))  # <Time.day_365: 365>

start
~~~~~

Just like ``enum_start``, defines a *start* value that should be used for enum members (default is ``None``):

.. code-block:: python3

    class Perm(Flag, auto_on_missing=True, start=0):
        Z, X, W, R  # 0, 1, 2, 4

    print(repr(Perm.R | Perm.W))  # <Perm.R|W: 6>

Special Names
-------------

``enums.py`` uses special names for managing behavior:

- *enum_missing: classmethod function(cls: Type[Enum], value: T) -> Enum*

- *enum_ignore: Union[str, Iterable[str]]*

- *enum_generate_next_value: function(name: str, start: Optional[T], count: int, member_values: List[T]) -> T*

- *enum_auto_on_missing: bool*

- *enum_start: T*

- *_name: str*

- *_value: T*

enum_missing
~~~~~~~~~~~~

Class method that should be used in order to process values that are not present in the enumeration:

.. code-block:: python3

    from typing import Union

    class Speed(Enum):
        SLOW = 1
        NORMAL = 2
        FAST = 3

        @classmethod
        def enum_missing(cls, value: Union[float, int]) -> Enum:
            if value < 1:
                return cls.SLOW
            elif value > 3:
                return cls.FAST
            else:
                return cls.NORMAL

    print(repr(Speed(5)))  # <Speed.FAST: 3>

enum_ignore
~~~~~~~~~~~

Iterable of strings or a string that contains names of class members that should be ignored when creating enum members:

.. code-block:: python3

    class Time(IntEnum):
        enum_ignore = ["Time", "second"]  # or "Time, second" or "Time second" or "Time,second"

        Time = vars()

        for second in range(60):
            Time[f"s_{second}"] = second

    print(repr(Time.s_59))  # <Time.s_59: 59>
    print(repr(Time.s_0)) # <Time.s_0: 0>

enum_generate_next_value
~~~~~~~~~~~~~~~~~~~~~~~~

Static method that takes member name, start value (default is None, unless specified otherwise),
count of unique members already created and list of all member values (including aliases).

This method should output value for new enum member:

.. code-block:: python3

    from typing import List, Optional, T

    class CountEnum(Enum):
        @staticmethod
        def enum_generate_next_value(
            name: str, start: Optional[T], count: int, values: List[T]
        ) -> T:
            """Return count of unique members, + 1."""
            return count + 1

    class Mark(CountEnum):
        F = auto()  # 1
        D = auto()  # 2
        C = auto()  # 3
        B = auto()  # 4
        A = auto()  # 5

enum_auto_on_missing
~~~~~~~~~~~~~~~~~~~~

Boolean that indicates whether auto() should be used to generate values for missing names:

.. code-block:: python3

    class Color(Enum):
        enum_auto_on_missing = True
        RED, GREEN, BLUE  # 1, 2, 3

enum_start
~~~~~~~~~~

Variable that indicates what value should be passed as *start* to *enum_generate_next_value*.

_name
~~~~~

Private attribute, name of the enum member. Ideally it should *never* be modified.

_value
~~~~~~

Private attribute, value of the enum member. Again, it better *not* be modified.

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

    $ git clone https://github.com/nekitdev/enums.py
    $ cd enums.py
    $ python -m pip install -U .

Testing
-------

In order to test the library, you need to have *coverage*, *flake8* and *pytest* packages.

They can be installed like so:

.. code:: sh

    $ cd enums.py
    $ python -m pip install .[test]

Then linting and running tests with coverage:

.. code:: sh

    $ flake8
    $ coverage run -m pytest test_enums.py

Changlelog
----------

- **0.1.0** - Initial release, almost full support of standard enum module;

- **0.1.1** - Make bitwise operations in Flag smarter;

- **0.1.2** - Add IntEnum and IntFlag;

- **0.1.3** - Add Traits and fix bugs;

- **0.1.4** - Add nice dir() implementation for both Enum class and members;

- **0.1.5** - Fix small bugs;

- **0.2.0** - Fix IntEnum to be almost even with standard library, fix bugs and add tests.

- **0.3.0** - Fix MRO resolution and add small enhancements.

Authors
-------

This project is mainly developed by `nekitdev <https://github.com/nekitdev>`_.
