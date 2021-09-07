from enum import Enum, EnumMeta
import json
from typing import Any, BinaryIO, Dict, IO, TextIO, Tuple, Union


class JsonConversionError(ValueError):
    """Subclass of ValueError with additional properties.

    Attributes:
        msg: The unformatted error message
        loc: The position in the json object where conversion failed
    """

    msg: str
    loc: str

    def __init__(self, msg: str, loc: str) -> None:
        errmsg = f"{msg}: at location {loc}"
        ValueError.__init__(self, errmsg)
        self.msg = msg
        self.loc = loc

    # for pickle
    def __reduce__(self) -> Tuple[type, Tuple[str, str]]:
        return self.__class__, (self.msg, self.loc)


# ---------- Reading ---------- #


def read_class_instance(obj: Dict[str, Any], target: type, loc: str) -> Any:
    if not isinstance(target, type):
        raise JsonConversionError(f"Target must be a type, but was f{target}", loc)

    attrs = getattr(target, "__annotations__", dict())

    extra_attrs = [key for key in obj if key not in attrs]
    if extra_attrs:
        raise JsonConversionError(
            f"Unknown attributes. Was expecting {list(attrs.keys())}, but found {extra_attrs}",
            loc,
        )

    # make sure our location ends with a .
    sub_loc = loc if loc.endswith(".") else loc + "."
    kwargs = {
        key: read_rec(value, attrs[key], sub_loc + key) for key, value in obj.items()
    }

    # Emit some better error messages if this doesn't go well
    try:
        return target(**kwargs)
    except Exception:
        raise JsonConversionError(
            f"Object creation failed {target.__name__}(**{kwargs})", loc
        )


def valid_type_for_dict(t: type) -> bool:
    """If the given type is a valid target when reading a dict."""
    return (
        t not in (type(None), str, int, float, bool)
        and getattr(t, "__origin__", None) is not list
    )


def read_rec(obj: Any, target: type, loc: str) -> Any:
    """A recursive version of read for internal use.

    Args:
        obj: The json object to convert
        target: The type to convert to
        loc: The location in the original json object where we are now working

    Raises:
        JsonConversionError: If there are problems reading the json as the given type

    Returns:
        The new object of the target type
    """
    # special case: do no type checking or additional parsing
    if target is Any:
        return obj

    # base type if the target type is a container
    type_args = getattr(target, "__args__", None)
    origin = getattr(target, "__origin__", target)

    type_err = JsonConversionError(
        f"Found {type(obj)}, but was expecting {target}", loc
    )

    # special handling for reading an enum
    if type(target) is EnumMeta:
        try:
            return target(obj)
        except ValueError:
            raise JsonConversionError("Invalid enum", loc)

    if obj is None:
        is_optional = origin is Union and type(None) in type_args
        if origin is not type(None) and not is_optional:  # noqa
            raise type_err
        return obj

    if isinstance(obj, (str, int, float, bool)):
        allowed_types = type_args if origin is Union else (origin,)
        if type(obj) not in allowed_types:
            raise type_err
        return obj

    if isinstance(obj, list):
        if origin is Union:
            possibilities = [
                t for t in type_args if getattr(t, "__origin__", None) is list
            ]
            if not possibilities:
                raise JsonConversionError(
                    f"Found {type(obj)}, but was expecting one of {type_args}", loc
                )
            if len(possibilities) > 1:
                raise JsonConversionError(
                    f"Ambiguous list type {possibilities} when reading {obj}", loc
                )
            target = possibilities[0]
            type_args = getattr(target, "__args__", None)
            origin = getattr(target, "__origin__", target)
        inner_type = type_args[0]
        return [read_rec(o, inner_type, loc + f"[{i}]") for i, o in enumerate(obj)]

    if isinstance(obj, dict):
        targets = type_args if origin is Union else (target,)
        possibilities = [t for t in targets if valid_type_for_dict(t)]
        if not possibilities:
            str_targets = " or ".join(str(t) for t in targets)
            raise JsonConversionError(
                f"Found {type(obj)}, but was expecting {str_targets}", loc
            )
        if len(possibilities) > 1:
            raise JsonConversionError(
                f"Ambiguous dict type when {possibilities} reading {obj}", loc
            )
        target = possibilities[0]
        type_args = getattr(target, "__args__", None)
        origin = getattr(target, "__origin__", target)

        if origin is dict:
            key_type, value_type = type_args
            if type_args != str:
                raise JsonConversionError(
                    f"Json dict keys are always strings, but type annotation was {key_type}",
                    loc,
                )
            loc = loc if loc.endswith(".") else loc + "."
            return {
                key: read_rec(value, value_type, loc + key)
                for key, value in obj.items()
            }

        return read_class_instance(obj, target, loc)

    raise JsonConversionError(f"Invalid json: {obj}", loc)


def read(obj: Any, target: type) -> Any:
    """Read some decoded json as an object of the given type.

    Args:
        obj: The decoded json to convert
        target: The type to convert to

    Raises:
        JsonConversionError

    Returns:
        The new object of the given type
    """
    return read_rec(obj, target, loc=".")


def load(fh: Union[TextIO, BinaryIO], target: type, **kwargs: Any) -> Any:
    """Wraps the standard json load and read in a single call.

    Args:
        fh: The file handle to read json from
        target: The type of object to create
        **kwargs: Additional arguments passed through to the call to json.load

    Returns:
        The new object of the given type
    """
    return read(json.load(fh, **kwargs), target)


def loads(s: Union[str, bytes], target: type, **kwargs: Any) -> Any:
    """Wraps the standard json loads and read in a single call.

    Args:
        s: The string to read json from
        target: The type of object to create
        **kwargs: Additional arguments passed through to the call to json.loads

    Returns:
        The new object of the given type
    """
    return read(json.loads(s, **kwargs), target)


# ---------- Writing ---------- #


def write_class_instance(obj: Any, loc: str) -> Any:
    if hasattr(obj, "__dict__"):
        return write_rec(obj.__dict__, loc)

    # NamedTuple doesn't have __dict__, but _asdict() instead
    if hasattr(obj, "_asdict"):
        return write_rec(obj._asdict(), loc)

    raise JsonConversionError(f"Cannot write {obj}", loc)


def write_rec(obj: Any, loc: str) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, Enum):
        return obj.value

    if isinstance(obj, list):
        return [write_rec(elem, loc + f"[{i}]") for i, elem in enumerate(obj)]

    if isinstance(obj, dict):
        bad_keys = [key for key in obj if not isinstance(key, str)]
        if bad_keys:
            raise JsonConversionError(
                f"Json dict keys are always strings, but found {bad_keys}", loc
            )
        loc = loc if loc.endswith(".") else loc + "."
        return {key: write_rec(value, loc + key) for key, value in obj.items()}

    return write_class_instance(obj, loc)


def write(obj: Any) -> Any:
    return write_rec(obj, ".")


def dump(obj: Any, fp: IO[str], **kwargs: Any) -> None:
    json.dump(write(obj), fp, **kwargs)


def dumps(obj: Any, **kwargs: Any) -> str:
    return json.dumps(write(obj), **kwargs)
