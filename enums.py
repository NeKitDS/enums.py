# -*- encoding: utf-8 -*-

# type: ignore  # way too magical to be understood by type checkers

"""Enhanced Enum Implementation for Python.

Less sophisticated, less restrictive, more magical and funky!

Example

>>> from enums import Enum

>>> class Color(Enum):
...     RED = 1
...     GREEN = 2
...     BLUE = 3

>>> Color.RED  # attribute access
<Color.RED: 1>
>>> Color["GREEN"]  # subscript access
<Color.GREEN: 2>
>>> Color(3)  # call access
<Color.BLUE: 3>

>>> Color.update(ALPHA=0)  # updating
>>> color = Color.from_name("alpha")
>>> print(color.name)
ALPHA
>>> print(color.value)
0
>>> print(color.title)
Alpha

MIT License

Copyright (c) 2020 nekitdev

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

__title__ = "enums"
__author__ = "nekitdev"
__copyright__ = "Copyright 2020 nekitdev"
__license__ = "MIT"
__version__ = "0.3.0"

import sys
from types import DynamicClassAttribute as dynamic_attribute, FrameType, MappingProxyType
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

try:
    from typing import NoReturn  # this may error on earlier versions

except ImportError:  # pragma: no cover
    NoReturn = None

__all__ = (
    "EnumMeta",
    "Enum",
    "IntEnum",
    "Flag",
    "IntFlag",
    "Trait",
    "Order",
    "StrFormat",
    "auto",
    "unique",
    "enum_generate_next_value",
)

DEFAULT_DOCUMENTATION = "An enumeration."
DEFAULT_DIR_INCLUDE = ["__class__", "__doc__", "__module__", "__members__"]  # some dir() dunders
DESCRIPTOR_ATTRIBUTES = ("__get__", "__set__", "__delete__")  # attributes that define a descriptor
ENUM_DEFINITION = "EnumName([mixin_type, ...] [data_type] enum_type)"  # enum subclass definition
INVALID_ENUM_NAMES = {"mro", ""}  # any others?
OBJECT_DIR = object.__dir__  # function to use for fetching dirs
OBJECT_NEW = object.__new__  # default new function used to create enum values
USELESS_NEW = {None, None.__new__, object.__new__}  # Enum's new is added here when it is defined

E = TypeVar("E", bound="Enum")  # used for enum typing
T = TypeVar("T")  # used for general typing
U = TypeVar("U")  # used for general typing

Enum: Type[E] = None  # we define Enum here as None, because it is used in EnumMeta before creation


class Singleton:
    instance = None

    def __repr__(self) -> str:  # pragma: no cover
        return str(self.__class__.__name__)

    @classmethod
    def __new__(cls, *args, **kwargs) -> "Singleton":
        if cls.instance is None:
            cls.instance = super().__new__(cls)

        return cls.instance


class Null(Singleton):
    pass


null = Null()


class auto:
    value = null


def _lower_name(name: str) -> str:  # turn "SomeName" or "some_name" into "somename"
    return name.lower().replace("_", "")


def _starts_and_ends_with(string: str, char: str, times: int = 1, strict: bool = True) -> bool:
    if len(char) != 1:
        raise ValueError(f"Expected char to be a string of length 1, got {char!r}.")

    if not times:
        return True  # all strings start and end with empty strings

    part = char * times
    part_len = len(part)

    main_check = len(string) > part_len and string[:part_len] == part and string[-part_len:] == part

    if strict:
        return main_check and string[part_len] != char and string[~part_len] != char  # ~x = -x-1

    return main_check


def _is_special(string: str) -> bool:
    return string.startswith(("_", "enum_"))


try:
    _get_frame = sys._getframe

except AttributeError:  # pragma: no cover
    class _GetFrame(Exception):
        pass

    def _get_frame(level: int = 0) -> Optional[FrameType]:
        try:
            raise _GetFrame()

        except _GetFrame as error:
            traceback = error.__traceback__

            if traceback is None:
                raise ValueError("No traceback to get the frame from.")

            current_frame = traceback.tb_frame

            if current_frame is None:
                raise ValueError("Can not get current frame.")

            frame = current_frame.f_back

            if frame is None:
                raise ValueError("Can not get caller frame.")

            if level:
                for _ in range(level):
                    frame = frame.f_back

                    if frame is None:
                        raise ValueError("Call stack is not deep enough.") from None

            return frame


def _is_strict_dunder(string: str) -> bool:
    return _starts_and_ends_with(string, "_", times=2, strict=True)


def _is_descriptor(some_object: Any) -> bool:
    for attribute in DESCRIPTOR_ATTRIBUTES:
        if hasattr(some_object, attribute):
            return True

    return False


def _find_data_type(bases: Tuple[Type[T], ...]) -> Type[T]:
    for chain in bases:
        for base in chain.__mro__:
            if base is object:  # not useful in our case
                continue

            elif "__new__" in base.__dict__:
                if issubclass(base, Enum):  # not looking for enums
                    continue
                return base

    return object  # nothing found, so return object class


def _make_class_unpicklable(cls: Type[T]) -> None:
    def _break_on_reduce_attempt(instance: T, protocol: int) -> NoReturn:
        raise TypeError(f"{instance} can not be pickled.")

    cls.__reduce_ex__ = _break_on_reduce_attempt
    cls.__module__ = "<unknown>"


def _make_readable(entity: T, on_undefined: U = "undefined") -> str:
    if entity is None:
        entity = on_undefined

    name = str(entity)

    if name.isupper():
        name = name.replace("_", " ").title()

    return name


def _create_enum_member(
    member_name: Optional[str],
    member_type: Type[T],
    value: U,
    enum_class: Type[E],
    new_function: Callable[..., T],
    use_args: bool,
    dynamic_attributes: Iterable[str],
) -> E:
    """Create and add enum member. Setting name to None has special meaning;
    This will attempt to add to value -> member map only;
    Special case is intended for creation of composite flags.
    """
    # double check if already defined, and raise error in that case
    if member_name is not None:
        if member_name in enum_class._member_map:
            raise ValueError(
                f"{member_name!r} already defined as: {enum_class._member_map[member_name]!r}."
            )

    if not isinstance(value, tuple):  # wrap in tuple if not already one
        args = (value,)
    else:  # do nothing otherwise
        args = value

    if member_type is tuple:  # special case for tuple enums
        args = (args,)  # wrap args again another time

    if use_args:
        enum_member = new_function(enum_class, *args)

        if not hasattr(enum_member, "_value"):  # if value was not defined already
            if member_type is not object:
                value = member_type(*args)

            enum_member._value = value

    else:
        enum_member = new_function(enum_class)

        if not hasattr(enum_member, "_value"):  # if value was not defined previously
            enum_member._value = value

    enum_class._member_values.append(value)

    enum_member._name = member_name
    enum_member.__objclass__ = enum_class
    enum_member.__init__(*args)

    if member_name is not None:
        for name, canonical_member in enum_class._member_map.items():
            if canonical_member._value == enum_member._value:
                enum_member = canonical_member
                break

        else:
            # aliases should not appear in member names (only in __members__)
            enum_class._member_names.append(member_name)

        # boost performance for any member that would not shadow DynamicClassAttribute
        if member_name not in dynamic_attributes:
            setattr(enum_class, member_name, enum_member)

        # now add to member map
        enum_class._member_map[member_name] = enum_member

    try:
        # see if member with this value exists (we reach here with member_name=None)
        previous_member = enum_class._value_map.get(value)

        # see if member exists and has name set to None
        if previous_member is not None and previous_member._name is None:
            previous_member._name = enum_member._name  # if so, update name
            enum_member = previous_member

        # attempt to add value to value -> member map in order to make lookups constant, O(1)
        # if value is not hashable, this will fail and our lookups will be linear, O(n)
        enum_class._value_map.setdefault(value, enum_member)  # in order to support threading

    except TypeError:  # not hashable
        pass

    return enum_member  # return member in case something wants to use it


def enum_generate_next_value(
    name: str, start: Optional[T], count: int, member_values: List[T]
) -> T:  # pragma: no cover
    """Empty function that shows signature of enum_generate_next_value() functions.

    name: str -> Name of enum entry which value should be generated.
    start: Optional[T] -> Passed as None if auto() is being used.
    count: int -> Amount of already existing unique members at the time of the call.
    member_values: List[T] -> List of previous member values.
    """
    raise NotImplementedError


def incremental_next_value(name: str, start: Optional[T], count: int, member_values: List[T]) -> T:
    """Implementation of enum_generate_next_value()
    that automatically increments last possible member value.

    If not possible to generate new value, returns start (1 by default).
    """
    if start is None:
        start = 1

    for member_value in reversed(member_values):  # find value we can increment
        try:
            return member_value + 1
        except TypeError:  # unsupported operand type(s) for +: T, int  # pragma: no cover
            pass

    else:
        return start


def strict_bit_next_value(name: str, start: Optional[T], count: int, member_values: List[T]) -> T:
    """Implementation of enum_generate_next_value()
    that automatically generates next power of two after previous value.

    If not possible to generate new value, returns start (1 by default).
    """
    if start is None:
        start = 1

    for member_value in reversed(member_values):
        try:
            high_bit = _high_bit(member_value)
        except Exception:  # noqa
            raise ValueError(f"Invalid flag value: {member_value!r}.") from None

        return 2 ** (high_bit + 1)

    else:
        return start


class EnumDict(Dict[str, U]):
    def __init__(self) -> None:
        super().__init__()

        self._auto_on_missing: bool = False
        self._start: Optional[T] = None
        self._enum_generate_next_value: Optional[Callable[..., T]] = None
        self._member_names: List[str] = []
        self._member_values: List[T] = []
        self._ignore: List[str] = []

    def __setitem__(self, key: str, value: T) -> None:
        if key == "enum_auto_on_missing":
            self._auto_on_missing = value

        elif key == "enum_ignore":
            if isinstance(value, str):  # process enum_ignore if given a string
                value = filter(bool, value.replace(",", " ").split())

            self._ignore = list(value)

        elif key == "enum_generate_next_value":  # setting enum_generate_next_value() function
            self._enum_generate_next_value = value

        elif key == "enum_start":
            self._start = value

        elif key in self._member_names:
            # something overrides enum?
            raise ValueError(f"Attempt to reuse key: {key!r}.")

        elif _is_strict_dunder(key) or _is_descriptor(value) or key in self._ignore:
            pass

        else:
            if key in self:
                # enum overrides something?
                raise ValueError(f"{key!r} already defined as: {self[key]!r}.")

            if isinstance(value, auto):
                if value.value is null:  # if null => generate next value
                    if self._enum_generate_next_value is None:
                        raise RuntimeError(
                            "Attempt to use auto value while "
                            "enum_generate_next_value was not defined."
                        )
                    value.value = self._enum_generate_next_value(
                        key, self._start, len(self._member_names), self._member_values.copy()
                    )
                value = value.value

            self._member_names.append(key)
            self._member_values.append(value)

        super().__setitem__(key, value)

    def __missing__(self, key: str) -> None:
        if _is_strict_dunder(key) or not self._auto_on_missing:
            raise KeyError(key)

        self[key] = auto()


class EnumMeta(type):
    @classmethod
    def __prepare__(
        meta_cls,
        cls: str,
        bases: Tuple[Type[T], ...],
        *,
        auto_on_missing: bool = False,
        ignore: Optional[Union[str, Iterable[str]]] = None,
        start: Optional[U] = None,
        **kwargs,
    ) -> EnumDict:
        """Prepare class initialization."""
        enum_dict = EnumDict()

        _, enum_type = meta_cls._get_member_and_enum_type(bases)

        for key, value in dict(
            enum_auto_on_missing=auto_on_missing,
            enum_generate_next_value=getattr(enum_type, "enum_generate_next_value", None),
            enum_ignore=(ignore or []),
            enum_start=start,
        ).items():
            enum_dict[key] = value

        return enum_dict

    def __new__(
        meta_cls,
        cls: str,
        bases: Tuple[Type[T], ...],
        cls_dict: EnumDict,
        *,
        # these are used by our meta_cls.__prepare__(...)
        auto_on_missing: bool = False,
        ignore: Optional[Union[str, Iterable[str]]] = None,
        start: Optional[U] = None,
    ) -> Type[E]:
        """Initialize new class. This function is *very* magical."""
        # add enum_ignore to self
        enum_ignore = list(cls_dict.get("enum_ignore", []))
        enum_ignore.append("enum_ignore")

        for key in enum_ignore:  # remove all keys in enum_ignore
            cls_dict.pop(key, None)

        member_type, enum_type = meta_cls._get_member_and_enum_type(bases)
        new_func, new_member_save, new_use_args = meta_cls._find_new(
            cls_dict, member_type, enum_type
        )

        # save all members into separate mapping
        enum_members = {name: cls_dict[name] for name in cls_dict._member_names}
        # remove enum members so they don't get baked into new class
        for name in cls_dict._member_names:
            del cls_dict[name]

        # check for invalid names
        invalid_names = set(enum_members) & INVALID_ENUM_NAMES

        if invalid_names:
            raise ValueError("Invalid member names: {}".format(", ".join(invalid_names)))

        # add default documentation if we need to
        cls_dict.setdefault("__doc__", DEFAULT_DOCUMENTATION)

        # create dummy enum class to manipulate MRO
        dummy_enum_class = super().__new__(meta_cls, cls, bases, EnumDict())

        mro = list(dummy_enum_class.mro())

        try:
            mro.remove(dummy_enum_class)

        except ValueError:  # pragma: no cover
            pass

        try:
            if mro.index(member_type) < mro.index(enum_type):
                # we need to preserve enum_type functions
                mro.remove(enum_type)
                mro.insert(mro.index(member_type), enum_type)

        except ValueError:  # pragma: no cover
            pass

        bases = tuple(mro)  # now back to tuple

        # create our new class
        enum_class = super().__new__(meta_cls, cls, bases, cls_dict)

        # add member names list and member type, along with new_func and new_use_args
        enum_class._member_names: List[str] = []  # list of member names
        enum_class._member_values: List[T] = []  # list of member values
        enum_class._member_type = member_type  # member type
        enum_class._new_function = new_func
        enum_class._use_args = new_use_args

        # add member maps
        enum_class._member_map: Dict[str, E] = {}  # name -> member map
        enum_class._value_map: Dict[T, E] = {}  # value -> member map for hashable values

        # save DynamicClassAttribute attributes from super classes so we know if
        # we can take the shortcut of storing members in the class dict
        dynamic_attributes: Set[str] = {
            key
            for subclass in enum_class.mro()
            for key, value in subclass.__dict__.items()
            if isinstance(value, dynamic_attribute)
        }
        enum_class._dynamic_attributes = dynamic_attributes

        for member_name in cls_dict._member_names:  # create our fellow enum members
            _create_enum_member(
                member_name=member_name,
                member_type=member_type,
                value=enum_members[member_name],
                enum_class=enum_class,
                new_function=new_func,
                use_args=new_use_args,
                dynamic_attributes=dynamic_attributes,
            )

        if Enum is not None:  # if enum was created (this will be false on initial run)
            if new_member_save:  # save as new_member if needed
                enum_class.__new_member__ = new_func
            enum_class.__new__ = Enum.__new__

        return enum_class  # finally! ;)

    def __call__(
        cls,
        value: Any,
        names: Union[str, Dict[str, U], List[str], Tuple[str, ...]] = (),
        module: Optional[str] = None,
        qualname: Optional[str] = None,
        type: Optional[Type[T]] = None,
        start: Optional[T] = None,
        **members: Dict[str, U],
    ) -> Union[E, Type[E]]:
        """With value argument only, search member by value.
        Otherwise, functional API: create new enum class.
        """
        if not members and not names and not type:
            return cls.__new__(cls, value)

        return cls.create(
            value, names, module=module, qualname=qualname, type=type, start=start, **members
        )

    def create(
        cls,
        class_name: str,
        names: Union[str, Dict[str, U], List[str], Tuple[str, ...]] = (),
        *,
        module: Optional[str] = None,
        qualname: Optional[str] = None,
        type: Optional[Type[T]] = None,
        start: Optional[T] = None,
        **members: Dict[str, U],
    ) -> Type[E]:
        """Convenient implementation of creating a new enum."""
        meta_cls = cls.__class__

        bases = (cls,) if type is None else (type, cls)

        _, enum_type = cls._get_member_and_enum_type(bases)
        cls_dict = meta_cls.__prepare__(class_name, bases)

        if isinstance(names, str):  # parse names if required
            names = list(filter(bool, names.replace(",", " ").split()))

        if isinstance(names, (tuple, list)) and names and isinstance(names[0], str):
            original_names, names = names, []
            member_values = []

            for count, name in enumerate(original_names):
                # generate values
                value = enum_type.enum_generate_next_value(name, start, count, member_values.copy())
                member_values.append(value)
                names.append((name, value))

        for item in names:  # either mapping or (name, value) pair
            if isinstance(item, str):
                member_name, member_value = item, names[item]
            else:
                member_name, member_value = item

            cls_dict[member_name] = member_value

        for member_name, member_value in members.items():
            cls_dict[member_name] = member_value

        enum_class = meta_cls.__new__(meta_cls, class_name, bases, cls_dict)

        if module is None:
            try:
                module = _get_frame(2).f_globals.get("__name__")

            except (AttributeError, ValueError):  # pragma: no cover
                pass

        if module is None:  # pragma: no cover
            _make_class_unpicklable(enum_class)

        else:
            enum_class.__module__ = module

        if qualname is not None:
            enum_class.__qualname__ = qualname

        return enum_class

    def __bool__(cls) -> bool:
        return True  # classes/types should always return True

    def __contains__(cls, member: E) -> bool:
        if not isinstance(member, Enum):
            raise TypeError(
                "Unsupported operand type(s) for 'in': '{other_name}' and '{self_name}'".format(
                    other_name=type(member).__qualname__, self_name=cls.__class__.__qualname__
                )
            )

        return isinstance(member, cls) and member._name in cls._member_map

    def __delattr__(cls, name: str) -> None:
        if name in cls._member_map:
            raise AttributeError(f"Can not delete Enum member: {name!r}.")

        super().__delattr__(name)

    def __getattr__(cls, name: str) -> E:
        if _is_strict_dunder(name):
            raise AttributeError(name)

        try:
            return cls._member_map[name]

        except KeyError:
            raise AttributeError(name) from None

    def __getitem__(cls, name: str) -> E:
        return cls._member_map[name]

    def __iter__(cls) -> Iterator[E]:
        """Same as cls.get_members()."""
        return cls.get_members()

    def __reversed__(cls) -> Iterator[E]:
        """Same as cls.get_members(reverse=True)."""
        return cls.get_members(reverse=True)

    def __len__(cls) -> int:
        """Return count of unique members (no aliases)."""
        return len(cls._member_names)

    def __repr__(cls) -> str:
        """Standard-like enum class representation."""
        return f"<enum {cls.__name__!r}>"

    def __setattr__(cls, name: str, value: T) -> None:
        """Set new attribute, blocking member reassign attempts.
        To add new fields, consider using Enum.add_member or Enum.update.
        """
        member_map = cls.__dict__.get("_member_map", {})  # this is used to prevent recursion

        if name in member_map:
            raise AttributeError(f"Attempt to reassign enum member: {member_map[name]}.")

        super().__setattr__(name, value)

    def __dir__(cls) -> List[str]:
        added_behavior = [key for key in OBJECT_DIR(cls) if not _is_special(key)]
        return DEFAULT_DIR_INCLUDE + added_behavior

    @staticmethod
    def _get_member_and_enum_type(bases: Tuple[Type[T], ...]) -> Tuple[Type[T], Type[E]]:
        """Find data type and first enum type that are subclassed."""
        if not bases:  # no bases => nothing to search => return defaults
            return object, Enum

        enum_type = bases[-1]

        if Enum and not issubclass(enum_type, Enum):
            raise TypeError(f"New enumerations should be created as {ENUM_DEFINITION}.")

        if enum_type._member_map:
            raise TypeError("Enumerations can not be extended.")

        member_type = _find_data_type(bases)

        return member_type, enum_type

    @staticmethod
    def _find_new(
        cls_dict: EnumDict, member_type: Type[T], enum_type: Type[E]
    ) -> Tuple[Callable[..., U], bool, bool]:  # new_func, new_member_save, new_use_args
        """Find __new__ function to create member types with."""
        new_func = cls_dict.get("__new__")

        if new_func is None:
            new_member_save = False

            for method in ("__new_member__", "__new__"):  # check for __new_member__ first
                for possible in (member_type, enum_type):
                    target = getattr(possible, method, None)

                    if target not in USELESS_NEW:
                        new_func = target
                        break

                if new_func is not None:  # assigned in inner loop, break from outer loop
                    break

            else:
                new_func = OBJECT_NEW

        else:
            new_member_save = True

        new_use_args = new_func is not OBJECT_NEW

        return new_func, new_member_save, new_use_args

    def add_member(cls, name: str, value: T) -> E:
        """Add new member to the enum. auto() is allowed."""
        if isinstance(value, auto):
            if value.value is null:  # if null => generate next value
                value.value = cls.enum_generate_next_value(
                    name, None, len(cls._member_names), cls._member_values.copy()
                )
            value = value.value

        return _create_enum_member(
            member_name=name,
            member_type=cls._member_type,
            value=value,
            enum_class=cls,
            new_function=cls._new_function,
            use_args=cls._use_args,
            dynamic_attributes=cls._dynamic_attributes,
        )

    def update(cls, **name_to_value: Dict[str, T]) -> None:
        """Add new member to enum for each name and value in args."""
        for name, value in name_to_value.items():
            cls.add_member(name, value)

    def get_members(cls, reverse: bool = False) -> Iterator[E]:
        """Return iterator over unique members (without aliases), optionally reversing it."""
        names = cls._member_names

        if reverse:
            names = reversed(names)

        return (cls._member_map[name] for name in names)

    @property
    def members(cls) -> Dict[str, E]:
        """Return mapping proxy for member map (includes aliases).
        Order is guaranteed from Python 3.7 (CPython 3.6) only.
        """
        return MappingProxyType(cls._member_map)

    __members__ = members

    @property
    def lower_names(cls) -> Dict[str, E]:
        """Create mapping of lower_name -> member for CI (case insensetive) comparison/lookup."""
        return {_lower_name(name): member for name, member in cls.members.items()}

    def from_name(cls, name: str) -> None:
        """CI (case insensetive) member by name lookup."""
        return cls.lower_names[_lower_name(name)]

    def from_value(cls, value: T, default: U = null) -> E:
        """Lookup member by name and value. On failure, call from_value(default)."""
        if isinstance(value, str):
            try:
                return cls.from_name(value)
            except KeyError:
                pass

        try:
            return cls(value)

        except Exception:  # noqa
            if default is null:
                raise

            return cls.from_value(default)

    def as_dict(cls) -> Dict[str, T]:
        """Return lower_name -> member_value mapping overall all members."""
        return {name.lower(): member.value for name, member in cls.members.items()}


class Enum(metaclass=EnumMeta):
    """Generic enumeration.

    Derive from this class to define new enumerations.
    """

    def __new__(cls, value: T) -> E:
        """Implement member by value lookup."""
        # all enum instances are created during class construction without calling this method;
        # this method is called by the metaclass' __call__ and pickle

        if type(value) is cls:
            return value

        try:
            return cls._value_map[value]

        except KeyError:
            # not found, no need to do long O(n) search
            pass

        except TypeError:
            # not there, then do long search, O(n) behavior
            for member in cls._member_map.values():
                if member._value == value:
                    return member

        # still not found => try enum_missing hook
        try:
            exception = None
            result = cls.enum_missing(value)

        except AttributeError:
            result = None

        except Exception as error:
            exception = error
            result = None

        if isinstance(result, cls):
            return result

        else:
            error_invalid = ValueError(f"{value!r} is not a valid {cls.__name__}.")

            if result is None and exception is None:  # no result, no error
                raise error_invalid

            elif exception is None:
                exception = ValueError(
                    f"Error in {cls.__name__}.enum_missing: "
                    f"returned {result} instead of None or a valid member."
                )

            raise error_invalid from exception

    enum_generate_next_value = staticmethod(incremental_next_value)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}.{self._name}: {self._value}>"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}.{self._name}"

    def __format__(self, format_spec: str) -> str:
        # pure enum
        if self._member_type is object:
            cls, value = str, str(self)

        # mix-in enum
        else:
            cls, value = self._member_type, self._value

        return cls.__format__(value, format_spec)

    def __hash__(self) -> int:
        return hash(self._name)

    def __reduce_ex__(self, protocol: int) -> Tuple[Type[E], T]:
        return self.__class__, (self._value,)

    def __dir__(self) -> List[str]:
        added_behavior = [
            key for key in OBJECT_DIR(self) if not _is_special(key) and key not in self._member_map
        ]
        return DEFAULT_DIR_INCLUDE + added_behavior

    @dynamic_attribute
    def title(self) -> str:
        """Title (human-readable name) of the Enum member."""
        return _make_readable(self._name)

    @dynamic_attribute
    def name(self) -> Optional[str]:
        """Name of the Enum member."""
        return self._name

    @dynamic_attribute
    def value(self) -> T:
        """Value of the Enum member."""
        return self._value


USELESS_NEW.add(Enum.__new__)


class IntEnum(int, Enum):
    """Generic enumeration for integer-based values."""


def unique(enumeration: Type[Enum]) -> Type[Enum]:
    """Class decorator for enumerations ensuring unique member values."""
    duplicates = []

    for name, member in enumeration.members.items():
        if name != member.name:
            duplicates.append((name, member.name))

    if duplicates:
        alias_details = ", ".join(f"{alias} -> {name}" for alias, name in duplicates)

        raise ValueError(f"Duplicates found in {enumeration!r}: {alias_details}.")

    return enumeration


class Flag(Enum):
    """Support for bit flags."""

    enum_generate_next_value = staticmethod(strict_bit_next_value)

    @classmethod
    def enum_missing(cls, value: T) -> Enum:
        """Create composite members on missing enums."""
        original_value = value

        if value < 0:
            value = ~value

        possible_member = cls._create_composite_member(value)

        if original_value < 0:
            possible_member = ~possible_member

        return possible_member

    @classmethod
    def _create_composite_member(cls, value: T) -> Enum:
        """Generate member composed of other members."""
        composite_member = cls._value_map.get(value)

        if composite_member is None:
            _, extra_flags = _decompose(cls, value)

            if extra_flags:
                raise ValueError(f"{value!r} is not a valid {cls.__name__}.")

            composite_member = _create_enum_member(
                member_name=None,
                member_type=cls._member_type,
                value=value,
                enum_class=cls,
                new_function=cls._new_function,
                use_args=cls._use_args,
                dynamic_attributes=cls._dynamic_attributes,
            )

        return composite_member

    def __contains__(self, other: Enum) -> bool:
        if not isinstance(other, self.__class__):
            raise TypeError(
                "Unsupported operand type(s) for 'in': '{other_name}' and '{self_name}'".format(
                    other_name=type(other).__qualname__, self_name=self.__class__.__qualname__
                )
            )

        return other._value & self._value == other._value

    def __repr__(self) -> str:
        if self._name is None:
            return f"<{self.__class__.__name__}.{self.composite_name}: {self._value}>"

        return f"<{self.__class__.__name__}.{self._name}: {self._value}>"

    def __str__(self) -> str:
        if self._name is None:
            return f"{self.__class__.__name__}.{self.composite_name}"

        return f"{self.__class__.__name__}.{self._name}"

    @classmethod
    def from_args(cls, *args) -> Enum:
        result = cls(0)

        for arg in args:
            result |= cls.from_value(arg)

        return result

    def decompose(self, reverse: bool = False) -> List[Enum]:
        """Decompose composite flag into all flags it can contain."""
        members, _ = _decompose(self.__class__, self._value)

        if reverse:
            members.reverse()

        return members

    @dynamic_attribute
    def composite_name(self) -> str:
        """Composite name of the composite Flag."""
        return "|".join(map(str, ((member._name or member._value) for member in self.decompose())))

    @dynamic_attribute
    def title(self) -> str:
        """Title of the Flag, which accounts for composites."""
        return ", ".join(
            map(_make_readable, ((member._name or member._value) for member in self.decompose()))
        )

    def __bool__(self) -> bool:
        return bool(self._value)

    def __or__(self, other: Union[T, Enum]) -> Enum:
        cls = self.__class__

        try:
            other = cls(other)

        except Exception:  # noqa  # pragma: no cover
            return NotImplemented

        return cls(self._value | other._value)

    def __and__(self, other: Union[T, Enum]) -> Enum:
        cls = self.__class__

        try:
            other = cls(other)

        except Exception:  # noqa  # pragma: no cover
            return NotImplemented

        return cls(self._value & other._value)

    def __xor__(self, other: Union[T, Enum]) -> Enum:
        cls = self.__class__

        try:
            other = cls(other)

        except Exception:  # noqa  # pragma: no cover
            return NotImplemented

        return cls(self._value ^ other._value)

    def __invert__(self) -> Enum:
        cls = self.__class__
        members = self.decompose()
        inverted = cls(0)

        for member in cls.get_members():
            if member not in members and not (member._value & self._value):
                inverted = inverted | member

        return cls(inverted)

    __ior__ = __or__
    __iand__ = __and__
    __ixor__ = __xor__

    __ror__ = __or__
    __rand__ = __and__
    __rxor__ = __xor__


class IntFlag(int, Flag):
    """Support for integer-based bit flags."""

    @classmethod
    def enum_missing(cls, value: int) -> Flag:
        if not isinstance(value, int):
            raise ValueError(f"{value!r} is not a valid {cls.__name__}.")

        return cls._create_composite_member(value)

    @classmethod
    def _create_composite_member(cls, value: int) -> Flag:
        composite_member = cls._value_map.get(value)

        if composite_member is None:
            need_to_create = [value]

            _, extra_flags = _decompose(cls, value)  # get unaccounted for bits

            while extra_flags:

                bit = _high_bit(extra_flags)
                flag_value = 2 ** bit

                if flag_value not in cls._value_map and flag_value not in need_to_create:
                    need_to_create.append(flag_value)

                if extra_flags == -flag_value:
                    extra_flags = 0
                else:
                    extra_flags ^= flag_value

            for value in reversed(need_to_create):
                composite_member = _create_enum_member(
                    member_name=None,
                    member_type=cls._member_type,
                    value=value,
                    enum_class=cls,
                    new_function=cls._new_function,
                    use_args=cls._use_args,
                    dynamic_attributes=cls._dynamic_attributes,
                )

        return composite_member

    def __invert__(self) -> Flag:
        return self.__class__(~self._value)


def _decompose(flag: Type[Flag], value: int) -> Tuple[List[Flag], int]:
    """Decompose given flag into flag members that value is composed of.
    Returns (flags, not_covered) tuple, where not_covered represents
    value that was not covered by any flag members.
    """
    not_covered = value
    is_not_negative = value >= 0

    members = []

    for member in flag:
        member_value = member._value
        if member_value and member_value & value == member_value:
            members.append(member)
            not_covered &= ~member_value

    if is_not_negative:
        temporary = not_covered

        while temporary:
            flag_value = 2 ** _high_bit(temporary)

            if flag_value in flag._value_map:
                members.append(flag._value_map[flag_value])
                not_covered &= ~flag_value

            temporary &= ~flag_value

    if not members and value in flag._value_map:
        members.append(flag._value_map[value])

    members.sort(key=lambda member: member._value, reverse=True)

    if len(members) > 1 and members[0].value == value:  # pragma: no cover
        # do not need the value member itself
        members.pop(0)

    return members, not_covered


def _high_bit(value: int) -> int:
    """Return index of the highest bit, and -1 if value is 0."""
    return value.bit_length() - 1


class Trait:
    """Base class to indicate traits (aka mixins) for enums."""


class StrFormat(Trait):
    """Trait that calls str(member) when formatting."""

    def __format__(self, format_spec: str) -> str:
        return str(self).__format__(format_spec)


class Order(Trait):
    """Trait that implements ordering (==, !=, <, >, <= and >=) for enums."""

    def __hash__(self) -> int:  # need to redefine because we implement == and !=
        return hash(self._name)

    def __eq__(self, other: Union[T, Enum]) -> bool:
        try:
            other = self.__class__(other)
        except Exception:  # noqa  # pragma: no cover
            return NotImplemented
        return self._value == other._value

    def __ne__(self, other: Union[T, Enum]) -> bool:
        try:
            other = self.__class__(other)
        except Exception:  # noqa  # pragma: no cover
            return NotImplemented
        return self._value != other._value

    def __lt__(self, other: Union[T, Enum]) -> bool:
        try:
            other = self.__class__(other)
        except Exception:  # noqa  # pragma: no cover
            return NotImplemented
        return self._value < other._value

    def __gt__(self, other: Union[T, Enum]) -> bool:
        try:
            other = self.__class__(other)
        except Exception:  # noqa  # pragma: no cover
            return NotImplemented
        return self._value > other._value

    def __le__(self, other: Union[T, Enum]) -> bool:
        return self < other or self == other

    def __ge__(self, other: Union[T, Enum]) -> bool:
        return self > other or self == other


if __name__ == "__main__":  # pragma: no cover
    import doctest

    doctest.testmod()  # test docstring on top of the module
