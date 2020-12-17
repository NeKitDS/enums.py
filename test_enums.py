import pickle

import pytest

from enums import Enum, IntEnum, Flag, IntFlag, Order, StrFormat, auto, unique
import enums

# below are some enums used for testing


class Empty(Enum):
    pass


class Season(Enum):
    WINTER = 1
    SPRING = 2
    SUMMER = 3
    AUTUMN = 4
    FALL = AUTUMN  # alias


class Constant(float, Enum):
    E = 2.718281828459045
    PI = 3.141592653589793
    TAU = 6.283185307179586


class Grade(IntEnum):
    A = 5
    B = 4
    C = 3
    D = 2
    F = 1


class GermanNumber(str, Enum):
    one = "eins"
    two = "zwei"
    three = "drei"


class Perm(Flag):
    Z = 0  # zero
    X = 1  # execute
    W = 2  # write
    R = 4  # read


class IntPerm(IntFlag):
    Z = 0  # zero
    X = 1  # execute
    W = 2  # write
    R = 4  # read


class Color(Flag):
    BLACK = 0
    RED = 1
    GREEN = 2
    BLUE = 4

    YELLOW = RED | GREEN
    CYAN = GREEN | BLUE
    MAGENTA = RED | BLUE

    WHITE = RED | GREEN | BLUE


class Sign(Order, Enum):
    MINUS = -1
    ZERO = 0
    PLUS = 1


class AlkaliMetal(StrFormat, IntEnum):
    Li = 3
    Na = 11
    K = 19
    Rb = 37
    Cs = 55
    Fr = 87


class AutoMissing(Enum, auto_on_missing=True, start=1):
    FIRST, SECOND, THIRD  # 1, 2, 3  # noqa: F821


class PickleClass:
    pass  # to be used for pickle test


def format_is_value(format_string: str, member: Enum) -> bool:
    return format_string.format(member) == format_string.format(member.value)


class TestHelpers:
    DESCRIPTOR_ATTRIBUTES = ("__get__", "__set__", "__delete__")  # attributes of descriptors
    VALUE = 13  # any value to use as placeholder

    def test_is_descriptor(self) -> None:
        for attribute in self.DESCRIPTOR_ATTRIBUTES:

            class SomeClass:
                pass  # we can not use object() because setattr() will fail

            some_object = SomeClass()

            assert not enums._is_descriptor(some_object)
            setattr(some_object, attribute, self.VALUE)  # set some value
            assert enums._is_descriptor(some_object)

    LOWER_NAME = "test"  # everything in TO_LOWER_NAME should be converted to this
    TO_LOWER_NAME = (
        "TEST",
        "Test",
        "test",
        "_test",
        "__test",
        "test_",
        "test__",
        "__test__",
    )  # everything should be converted to LOWER_NAME

    def test_lower_name(self) -> None:
        for name in self.TO_LOWER_NAME:
            assert enums._lower_name(name) == self.LOWER_NAME

    CHAR = "_"  # char to use in starts_and_ends_with()
    NAME = "nekit"  # name to test with starts_and_ends_with()
    EMPTY_CHAR = ""  # too short? haha
    LONG_CHAR = "__"  # too long

    def test_starts_and_ends_with_check(self) -> None:
        with pytest.raises(ValueError):  # length < 1
            enums._starts_and_ends_with(self.NAME, self.EMPTY_CHAR)

        with pytest.raises(ValueError):  # length > 1
            enums._starts_and_ends_with(self.NAME, self.LONG_CHAR)

    def test_starts_and_ends_with(self) -> None:
        assert enums._starts_and_ends_with(self.NAME, self.CHAR, times=0, strict=True)

        for times in range(1, 5):
            char = self.CHAR
            part = char * times

            valid_strict_name = part + self.NAME + part

            valid_non_strict_name_start = char + valid_strict_name
            valid_non_strict_name_end = valid_strict_name + char

            invalid_name_start = valid_strict_name[1:]
            invalid_name_end = valid_strict_name[:-1]

            assert enums._starts_and_ends_with(valid_strict_name, char, times=times, strict=True)

            for non_strict_name in (valid_non_strict_name_start, valid_non_strict_name_end):
                assert not enums._starts_and_ends_with(
                    non_strict_name, char, times=times, strict=True
                )
                assert enums._starts_and_ends_with(non_strict_name, char, times=times, strict=False)

            for invalid_name in (invalid_name_start, invalid_name_end):
                assert not enums._starts_and_ends_with(  # does not matter if strict or not
                    invalid_name, char, times=times, strict=True
                )

    SPECIAL = ("enum_something", "_private", "__protected")
    NOT_SPECIAL = ("not_special", "enumeration")  # we check for "enum_" start

    def test_is_special(self) -> None:
        for special in self.SPECIAL:
            assert enums._is_special(special)

        for not_special in self.NOT_SPECIAL:
            assert not enums._is_special(not_special)

    STRICT_DUNDERS = ("__dunder__", "__other_dunder__")
    NOT_DUNDERS_OR_NOT_STRICT = (
        "name",
        "_private",
        "__protected",
        "weird_",
        "___private_dunder__",
        "__weird_dunder___",
        "_",
        "__",
        "___",
        "____",
    )

    def test_is_strict_dunder(self) -> None:
        for strict_dunder in self.STRICT_DUNDERS:
            assert enums._is_strict_dunder(strict_dunder)

        for not_dunder_or_not_strict in self.NOT_DUNDERS_OR_NOT_STRICT:
            assert not enums._is_strict_dunder(not_dunder_or_not_strict)

    # pairs (bases, expected_type)
    EMPTY = ((), object)
    WITH_DATA_TYPE = ((object, int, Enum), int)
    WITHOUT_DATA_TYPE = ((object, Enum), object)

    def test_find_data_type(self) -> None:
        for (bases, expected_type) in (self.EMPTY, self.WITH_DATA_TYPE, self.WITHOUT_DATA_TYPE):
            assert enums._find_data_type(bases) is expected_type

    def test_make_class_unpicklable(self) -> None:
        pickle_object = PickleClass()

        pickle.dumps(pickle_object)  # can be pickled

        enums._make_class_unpicklable(PickleClass)

        with pytest.raises(TypeError):
            pickle.dumps(pickle_object)  # can NOT be pickled

    OBJECT_TO_READABLE = {
        None: "undefined",
        "UPPER_CASE": "Upper Case",
        "TitleCase": "TitleCase",
        "lower_case": "lower_case",
    }

    def test_make_readable(self) -> None:
        for key, value in self.OBJECT_TO_READABLE.items():
            assert enums._make_readable(key) == value


class TestEnumCreate:
    def test_create_normal(self) -> None:
        class Color(Enum):
            RED = auto()
            GREEN = auto()
            BLUE = auto()

    def test_create_using_string(self) -> None:
        Enum("Color", "RED GREEN BLUE")

    def test_create_using_sequence(self) -> None:
        Enum("Color", ["RED", "GREEN", "BLUE"])

    def test_create_using_mapping(self) -> None:
        Enum("Color", {"RED": auto(), "GREEN": auto(), "BLUE": auto()})

    def test_create_using_members(self) -> None:
        Enum("Color", RED=auto(), GREEN=auto(), BLUE=auto())

    def test_create_arguments(self) -> None:
        Enum(
            "Color",
            start=1,
            module=__name__,
            qualname="Color",
            RED=auto(),
            GREEN=auto(),
            BLUE=auto(),
        )

    def test_unique(self) -> None:
        @unique
        class Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3

        with pytest.raises(ValueError):
            @unique
            class OtherColor(Enum):
                RED = 1
                GREEN = 2
                BLUE = 3
                R, G, B = RED, GREEN, BLUE

    def test_invalid_definition(self) -> None:
        with pytest.raises(TypeError):
            class Broken(float, Enum, int):
                pass  # pragma: no cover

    def test_break_on_extend_attempt(self) -> None:
        with pytest.raises(TypeError):
            class ExtendPerm(Perm):
                pass  # pragma: no cover

    def test_tuple_enum(self) -> None:
        class Point(tuple, Enum):
            ORIGIN = (0, 0)
            POINT_1_1 = (1, 1)

        assert Point.ORIGIN == (0, 0)
        assert Point.POINT_1_1 == (1, 1)

    def test_init(self) -> None:
        class Point(Enum):
            def __init__(self, x: int, y: int) -> None:
                self.x = x
                self.y = y

            @property
            def distance_from_origin(self) -> float:
                return (self.x ** 2 + self.y ** 2) ** 0.5

            ORIGIN = (0, 0)
            POINT_3_4 = (3, 4)

        assert Point.ORIGIN != (0, 0)
        assert Point.POINT_3_4 != (3, 4)

        assert Point.ORIGIN.distance_from_origin == 0.0
        assert Point.POINT_3_4.distance_from_origin == 5.0

    def test_new(self) -> None:
        class Number(int, Enum):
            __new__ = int.__new__  # idk

            ZERO = 0
            ONE = 1
            TWO = 2
            THREE = 3

    def test_not_hashable(self) -> None:
        class ListEnum(list, Enum):
            empty = []

        assert ListEnum([]) is ListEnum.empty


class TestEnum:
    def test_enum_to_enum(self) -> None:
        assert Season(Season.WINTER) is Season.WINTER

    def test_value_to_enum(self) -> None:
        assert Season(2) is Season.SPRING

    def test_name_to_enum(self) -> None:
        assert Season["SUMMER"] is Season.SUMMER

    def test_enum_from_name(self) -> None:
        assert Season.from_name("autumn") is Season.AUTUMN

        with pytest.raises(KeyError):
            Season.from_name("broken")

    def test_enum_from_value(self) -> None:
        assert Season.from_value(1) is Season.from_value("winter")

        with pytest.raises(ValueError):
            Season.from_value("broken")

        assert Season.from_value("broken", "winter") is Season.WINTER

    def test_enum_name_title_value(self) -> None:
        assert Season.SPRING.name == "SPRING"
        assert Season.SPRING.title == "Spring"
        assert Season.SPRING.value == 2

        with pytest.raises(AttributeError):
            Season.SPRING.name = "PRIMAVERA"
        with pytest.raises(AttributeError):
            Season.SPRING.title = "Primavera"
        with pytest.raises(AttributeError):
            Season.SPRING.value = 2

    def test_change_member(self) -> None:
        with pytest.raises(AttributeError):
            Season.SPRING = "spring"

    def test_delete_attribute(self) -> None:
        class Foo(Enum):
            def bar(self) -> None:  # pragma: no cover
                pass

        assert hasattr(Foo, "bar")
        del Foo.bar
        assert not hasattr(Foo, "bar")

    def test_delete_member(self) -> None:
        with pytest.raises(AttributeError):
            del Season.SUMMER

    def test_iter_and_reverse(self) -> None:
        assert list(reversed(list(Season))) == list(reversed(Season))

    def test_class_bool(self) -> None:
        assert bool(Season)  # explicit bool() call here

    def test_member_bool(self) -> None:
        for member in GermanNumber:
            assert bool(member)  # explicit bool() call here

    def test_contains(self) -> None:
        assert Season.AUTUMN in Season

        with pytest.raises(TypeError):
            "AUTUMN" in Constant

        with pytest.raises(TypeError):
            4 in Constant

    def test_comparison(self) -> None:
        with pytest.raises(TypeError):
            Season.WINTER < Season.SUMMER

        assert Grade.A > Grade.F
        assert Constant.E < Constant.PI < Constant.TAU

        SeasonMimic = Enum("Season", "WINTER SPRING SUMMER AUTUMN")
        assert Season.SPRING != SeasonMimic.SPRING

    def test_length(self) -> None:
        assert len(Season) == 4

    def test_aliases(self) -> None:
        assert Season.AUTUMN is Season.FALL

    def test_reassign_fail(self) -> None:
        with pytest.raises(ValueError):
            class Variable(Enum):
                x = 1
                y = 2
                x = 3

        with pytest.raises(ValueError):
            class OtherVariable(Enum):
                x = 1

                def x(self) -> str:  # pragma: no cover
                    return "x"

        with pytest.raises(ValueError):
            class AnotherVariable(Enum):
                def x(self) -> str:  # pragma: no cover
                    return "x"

                x = 1  # noqa

    def test_missing_auto(self) -> None:
        with pytest.raises(RuntimeError):
            class Test(Enum):
                enum_generate_next_value = None
                test = auto()

    def test_invalid_member_names(self) -> None:
        with pytest.raises(ValueError):
            class InvalidName(Enum):
                mro = "mro"

    FORMAT_SPECS = ("{}", "{:}", "{:20}", "{:20}", "{:^20}", "{:>20}", "{:<20}")

    def test_format(self) -> None:
        for format_spec in self.FORMAT_SPECS:
            assert format_is_value(format_spec, Constant.PI)
            assert not format_is_value(format_spec, AlkaliMetal.Fr)

    def test_dir(self) -> None:
        assert dir(Grade) and dir(Grade.C)

    def test_repr(self) -> None:
        assert repr(Empty)

    def test_as_dict(self) -> None:
        assert Grade.as_dict() == {"a": 5, "b": 4, "c": 3, "d": 2, "f": 1}

    def test_member_str(self) -> None:
        assert str(Grade.A) == "Grade.A"

    def test_class_repr(self) -> None:
        assert repr(Grade) == f"<enum {Grade.__name__!r}>"

    def test_member_repr(self) -> None:
        assert repr(Grade.F) == "<Grade.F: 1>"

    def test_pickle(self) -> None:
        assert pickle.loads(pickle.dumps(Constant.TAU)) is Constant.TAU

    def test_hash(self) -> None:
        assert hash(Constant.E) == hash(Constant.E.name)


class TestSpecial:
    def test_enum_auto_on_missing(self) -> None:
        class Color(Enum):
            enum_auto_on_missing = True
            RED, GREEN, BLUE  # 1, 2, 3  # noqa: F82

    def test_enum_ignore(self) -> None:
        class Color(Enum):
            enum_ignore = "IGNORE, NEKIT"
            RED = 1
            GREEN = 2
            BLUE = 3
            IGNORE = NEKIT = 13

        assert not isinstance(Color.IGNORE, Color)

    def test_enum_missing(self) -> None:
        class Color(Enum):
            UNKNOWN = 0
            RED = 1
            GREEN = 2
            BLUE = 3

            @classmethod
            def enum_missing(cls, value: int) -> Enum:
                return cls.UNKNOWN

        assert Color(-1) is Color.UNKNOWN

    def test_garbage_enum_missing(self) -> None:
        class ReturnsWrong(Enum):
            @classmethod
            def enum_missing(cls, value: object) -> object:
                return value

        with pytest.raises(ValueError):
            ReturnsWrong(0)

        class Fails(Enum):
            @classmethod
            def enum_missing(cls, value: object) -> object:
                raise RuntimeError("enum_missing failed...")

        with pytest.raises(ValueError):
            Fails(0)

    def test_enum_start(self) -> None:
        class Number(Enum):
            enum_start = 0
            ZERO = auto()

        assert Number(0) is Number.ZERO


class TestFlag:
    VALUES = (
        Perm.R | Perm.W | Perm.X,
        Perm.R | Perm.W,
        Perm.R | Perm.X,
        Perm.R,
        Perm.W | Perm.X,
        Perm.W,
        Perm.X,
        Perm.Z,
    )

    STR_MAP = {
        Perm.R: "Perm.R",
        Perm.W: "Perm.W",
        Perm.X: "Perm.X",
        Perm.Z: "Perm.Z",
        Perm.R | Perm.W: "Perm.R|W",
        Perm.R | Perm.W | Perm.X: "Perm.R|W|X",
        Perm(0): "Perm.Z",
        ~Perm.R: "Perm.W|X",
        ~Perm.W: "Perm.R|X",
        ~Perm.X: "Perm.R|W",
        ~Perm.Z: "Perm.R|W|X",
        Perm(~0): "Perm.R|W|X",
    }

    def test_str(self) -> None:
        for member, string in self.STR_MAP.items():
            assert str(member) == string

    REPR_MAP = {
        Perm.R: "<Perm.R: 4>",
        Perm.W: "<Perm.W: 2>",
        Perm.X: "<Perm.X: 1>",
        Perm.Z: "<Perm.Z: 0>",
        Perm.R | Perm.W: "<Perm.R|W: 6>",
        Perm.R | Perm.W | Perm.X: "<Perm.R|W|X: 7>",
        Perm(0): "<Perm.Z: 0>",
        ~Perm.R: "<Perm.W|X: 3>",
        ~Perm.W: "<Perm.R|X: 5>",
        ~Perm.X: "<Perm.R|W: 6>",
        ~Perm.Z: "<Perm.R|W|X: 7>",
        Perm(~0): "<Perm.R|W|X: 7>",
    }

    def test_repr(self) -> None:
        for member, string in self.REPR_MAP.items():
            assert repr(member) == string

    def test_bool(self) -> None:
        assert Perm.R | Perm.W | Perm.X
        assert not Perm.Z

    def test_title(self) -> None:
        assert (Perm.R | Perm.W | Perm.X).title == "R, W, X"

    def test_from_args(self) -> None:
        assert Perm.from_args("r", "w", "x") is Perm.R | Perm.W | Perm.X
        assert Perm.from_args(2, 4) is Perm.R | Perm.W

    def test_or(self) -> None:
        for member in self.VALUES:
            for other in self.VALUES:
                assert member | other is Perm(member.value | other.value)
                assert member | other.value is Perm(member.value | other.value)
                assert member.value | other is Perm(member.value | other.value)

    def test_and(self) -> None:
        for member in self.VALUES:
            for other in self.VALUES:
                assert member & other is Perm(member.value & other.value)
                assert member & other.value is Perm(member.value & other.value)
                assert member.value & other is Perm(member.value & other.value)

    def test_xor(self) -> None:
        for member in self.VALUES:
            for other in self.VALUES:
                assert member ^ other is Perm(member.value ^ other.value)
                assert member ^ other.value is Perm(member.value ^ other.value)
                assert member.value ^ other is Perm(member.value ^ other.value)

    def test_invert(self) -> None:
        for member in self.VALUES:
            assert isinstance(~member, Perm)
            assert ~~member is member

    def test_contains(self) -> None:
        assert Perm.R in (Perm.R | Perm.W)
        assert Perm.X not in (Perm.R | Perm.W)

        with pytest.raises(TypeError):
            "R" in Perm.R

        with pytest.raises(TypeError):
            4 in Perm.R

    def test_decompose(self) -> None:
        RWX = Perm.from_args("r", "w", "x")

        decomposed = [Perm.R, Perm.W, Perm.X]

        assert RWX.decompose() == list(reversed(RWX.decompose(reverse=True))) == decomposed

    def test_auto(self) -> None:
        class AutoFlag(Flag):
            one = auto()
            two = auto()
            four = auto()

        assert list(AutoFlag.as_dict().values()) == [1, 2, 4]

    def test_garbage_auto(self) -> None:
        with pytest.raises(ValueError):
            class GarbageAuto(Flag):
                one = "garbage"
                two = auto()

    def test_fail_on_not_covered(self) -> None:
        with pytest.raises(ValueError):
            Perm(8)


class TestIntFlag:
    VALUES = (
        IntPerm.R | IntPerm.W | IntPerm.X,
        IntPerm.R | IntPerm.W,
        IntPerm.R | IntPerm.X,
        IntPerm.R,
        IntPerm.W | IntPerm.X,
        IntPerm.W,
        IntPerm.X,
        IntPerm.Z,
    )

    def test_type(self) -> None:
        for perm in IntPerm:
            assert isinstance(perm, IntPerm)

        assert isinstance(IntPerm.R | IntPerm.W, IntPerm)
        assert IntPerm.X >= 1  # inherited from int

    STR_MAP = {
        IntPerm.R: "IntPerm.R",
        IntPerm.W: "IntPerm.W",
        IntPerm.X: "IntPerm.X",
        IntPerm.Z: "IntPerm.Z",
        IntPerm.R | IntPerm.W: "IntPerm.R|W",
        IntPerm.R | IntPerm.W | IntPerm.X: "IntPerm.R|W|X",
        IntPerm.R | 8: "IntPerm.8|R",
        IntPerm(0): "IntPerm.Z",
        IntPerm(8): "IntPerm.8",
        ~IntPerm.R: "IntPerm.W|X",
        ~IntPerm.W: "IntPerm.R|X",
        ~IntPerm.X: "IntPerm.R|W",
        ~(IntPerm.R | IntPerm.W | IntPerm.X): "IntPerm.-8",
        IntPerm(~0): "IntPerm.R|W|X",
        IntPerm(~8): "IntPerm.R|W|X",
    }

    def test_str(self) -> None:
        for member, string in self.STR_MAP.items():
            assert str(member) == string

    REPR_MAP = {
        IntPerm.R: "<IntPerm.R: 4>",
        IntPerm.W: "<IntPerm.W: 2>",
        IntPerm.X: "<IntPerm.X: 1>",
        IntPerm.Z: "<IntPerm.Z: 0>",
        IntPerm.R | IntPerm.W: "<IntPerm.R|W: 6>",
        IntPerm.R | IntPerm.W | IntPerm.X: "<IntPerm.R|W|X: 7>",
        IntPerm.R | 8: "<IntPerm.8|R: 12>",
        IntPerm(0): "<IntPerm.Z: 0>",
        IntPerm(8): "<IntPerm.8: 8>",
        ~IntPerm.R: "<IntPerm.W|X: -5>",
        ~IntPerm.W: "<IntPerm.R|X: -3>",
        ~IntPerm.X: "<IntPerm.R|W: -2>",
        ~(IntPerm.R | IntPerm.W | IntPerm.X): "<IntPerm.-8: -8>",
        IntPerm(~0): "<IntPerm.R|W|X: -1>",
        IntPerm(~8): "<IntPerm.R|W|X: -9>",
    }

    def test_repr(self) -> None:
        for member, string in self.REPR_MAP.items():
            assert repr(member) == string

    def test_fail_on_wrong_type(self) -> None:
        with pytest.raises(ValueError):
            IntPerm(1.3)

    def test_invert(self) -> None:
        for member in self.VALUES:
            assert ~member == ~member.value
            assert ~(member.value) == ~member.value
            assert isinstance(~member, IntPerm)
            assert ~~member is member


class TestMutation:
    def test_update_works(self) -> None:
        class Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3

        Color.update(BLACK=0)

        assert Color(0) == Color.BLACK

    def test_update_with_auto(self) -> None:
        class Color(Enum):
            pass

        Color.update(RED=auto(), GREEN=auto(), BLUE=auto())

        assert Color.GREEN.value == 2

    def test_error_if_exists(self) -> None:
        class Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3

        with pytest.raises(ValueError):
            Color.add_member("RED", 0)

    def test_flag_update(self) -> None:
        class NewPerm(Flag):
            R = 4
            W = 2
            X = 1

        RWX = NewPerm.R | NewPerm.W | NewPerm.X

        assert repr(RWX) == "<NewPerm.R|W|X: 7>"

        NewPerm.update(Z=0, WX=3, RX=5, RW=6, RWX=7)

        assert repr(RWX) == "<NewPerm.RWX: 7>"

        assert NewPerm(0).name == "Z"


class TestOrder:
    def test_order(self) -> None:
        assert Sign.PLUS >= Sign.ZERO >= Sign.MINUS
        assert Sign.MINUS <= Sign.ZERO <= Sign.PLUS

        assert Sign.MINUS != Sign.PLUS
        assert Sign.ZERO == 0

    def test_hash(self) -> None:
        assert hash(Sign.ZERO) == hash(Sign.ZERO.name)
