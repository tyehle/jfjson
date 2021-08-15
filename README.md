# jfjson
[![Build](https://github.com/tyehle/jfjson/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/tyehle/jfjson/actions/workflows/build.yml)

Just fucking json!

Converts json to python objects using type annotations.

```python
@dataclass
class Record:
    name: str
    pos: int
    age: float

jfjson.loads('[{"name": "you", "pos": 42, "age": 5.2}]', List[Record])
# [Record(name='you', pos=42, age=5.2)]
```

It also does data validation and type checking
```python
jfjson.loads('["a", null, 12]', List[Optional[str]])
# jfjson.core.JsonConversionError: Found <class 'int'>, but was expecting typing.Optional[str]: at location .[2]
```

Also knows how to write any class that has a `__dict__` attribute or `_asdict()` function.

```python
@dataclass
class Record:
    name: str
    pos: int
    age: float

jfjson.dumps([Record(name='you', pos=42, age=5.2)])
# '[{"name": "you", "pos": 42, "age": 5.2}]'
```