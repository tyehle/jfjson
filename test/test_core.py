from dataclasses import dataclass
from enum import Enum
from jfjson.core import JsonConversionError
import sys
import unittest
import textwrap
from typing import List, NamedTuple, Optional

from jfjson import dumps, read, write


class E(Enum):
    A = "a"
    B = 1


class C:
    s: str

    def __init__(self, s: str) -> None:
        self.s = s

    def __eq__(self, o: object) -> bool:
        return self.s == o.s if isinstance(o, C) else False


class T(NamedTuple):
    x: str
    y: int = 0
    z: Optional[float] = None


class B(NamedTuple):
    cs: List[C]
    t: T


@dataclass(frozen=True)
class A:
    b: B


@dataclass
class D:
    __slots__ = "x", "y"
    x: int
    y: int


class TestRead(unittest.TestCase):
    def test_simple_read(self) -> None:
        self.assertEqual(read(dict(s="text"), C), C("text"))

    def test_read_default_values(self) -> None:
        self.assertEqual(read({"x": "", "z": 0.2}, T), T("", z=0.2))

    def test_object_creation_error(self) -> None:
        with self.assertRaises(JsonConversionError) as context:
            read({"b": {"cs": [], "t": {"y": 2}}}, A)
        self.assertEqual(context.exception.loc, ".b.t")
        self.assertEqual(context.exception.msg, "Object creation failed T(**{'y': 2})")
        inner = context.exception.__context__
        assert inner is not None
        self.assertIsInstance(inner, TypeError)
        self.assertRegex(
            inner.args[0], r".* missing 1 required positional argument: 'x'"
        )

    def test_list_type_error(self) -> None:
        with self.assertRaises(JsonConversionError) as context:
            read({"s": "text"}, List[C])
        self.assertEqual(context.exception.loc, ".")
        self.assertEqual(
            context.exception.msg,
            "Found <class 'dict'>, but was expecting typing.List[test.test_core.C]",
        )

    def test_optional_list(self) -> None:
        with self.assertRaises(JsonConversionError) as context:
            read(["a", None, 12], List[Optional[str]])
        self.assertEqual(context.exception.loc, ".[2]")
        if sys.version_info < (3, 9):
            expected_type = "typing.Union[NoneType, str]"
        else:
            expected_type = "typing.Optional[str]"
        self.assertEqual(
            context.exception.msg,
            f"Found <class 'int'>, but was expecting {expected_type}",
        )

    def test_enum(self) -> None:
        self.assertEqual(read("a", E), E.A)
        self.assertEqual(read(1, E), E.B)
        with self.assertRaises(JsonConversionError) as context:
            read("b", E)
        self.assertEqual(context.exception.loc, ".")
        self.assertEqual(context.exception.msg, "Invalid enum")

        inner = context.exception.__context__
        assert isinstance(inner, ValueError)
        self.assertEqual(inner.args[0], "'b' is not a valid E")


class TestWrite(unittest.TestCase):
    def test_simple_write(self) -> None:
        self.assertEqual(write(C("text")), {"s": "text"})

    def test_leaf_write(self) -> None:
        self.assertEqual(write(None), None)
        self.assertEqual(write(12), 12)
        self.assertEqual(write("text"), "text")
        self.assertEqual(write(12.5), 12.5)
        self.assertEqual(write(False), False)

    def test_write_list(self) -> None:
        self.assertEqual(write(["a", 12]), ["a", 12])
        with self.assertRaises(JsonConversionError) as context:
            write(["a", b"bad"])
        self.assertEqual(context.exception.loc, ".[1]")
        self.assertEqual(context.exception.msg, "Cannot write b'bad'")

    def test_write_dict(self) -> None:
        with self.assertRaises(JsonConversionError) as context:
            write({"inner": {"a": 2, b"binary": 3, None: 4}})
        self.assertEqual(context.exception.loc, ".inner")
        self.assertEqual(
            context.exception.msg,
            "Json dict keys are always strings, but found [b'binary', None]",
        )

    def test_write_class(self) -> None:
        self.assertEqual(
            dumps(A(B([C("a"), C("b")], T("x"))), indent=4),
            textwrap.dedent(
                """\
                {
                    "b": {
                        "cs": [
                            {
                                "s": "a"
                            },
                            {
                                "s": "b"
                            }
                        ],
                        "t": {
                            "x": "x",
                            "y": 0,
                            "z": null
                        }
                    }
                }"""
            ),
        )

    def test_write_enum(self) -> None:
        self.assertEqual(write(E.A), "a")
        self.assertEqual(write(E.B), 1)
