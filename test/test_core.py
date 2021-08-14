from dataclasses import dataclass
import unittest
from typing import List, NamedTuple, Optional

from jfjson import read, write


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
    def test_simple_read(self):
        self.assertEqual(read(dict(s="text"), C), C("text"))

    def test_read_default_values(self):
        self.assertEqual(read({"x": "", "z": 0.2}, T), T("", z=0.2))

    def test_(self):
        read({"b": {"cs": [{"s": "asdf"}]}}, A)


if __name__ == "__main__":
    from rich import inspect, print

    # read({"b": {"cs": [{"s": "asdf"}]}}, A)

    read({"s": "asdf"}, List[C])
