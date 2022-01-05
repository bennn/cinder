# pyre-strict
from __future__ import annotations

import array
import functools
import random
import time
from asyncio import iscoroutinefunction
from functools import wraps
from types import FunctionType, Union as typesUnion
from typing import (
    _GenericAlias,
    Dict,
    Iterable,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Tuple,
    Union,
    final,
    _tp_cache,
)
from weakref import WeakValueDictionary

from .enum import Enum
from .type_code import (
    type_code,
    TYPED_INT8,
    TYPED_INT16,
    TYPED_INT32,
    TYPED_INT64,
    TYPED_UINT8,
    TYPED_UINT16,
    TYPED_UINT32,
    TYPED_UINT64,
    TYPED_DOUBLE,
    TYPED_SINGLE,
    TYPED_BOOL,
    TYPED_CHAR,
)

try:
    import _static
except ImportError:

    def is_type_static(_t):
        return False

    def set_type_static(_t):
        return _t

    def set_type_static_final(_t):
        return _t

    def set_type_final(_t):
        return _t

    _static = None
    chkdict = dict
    chklist = list

    def make_recreate_cm(_typ):
        def _recreate_cm(self):
            return self

        return _recreate_cm


else:
    chkdict = _static.chkdict
    chklist = _static.chklist
    is_type_static = _static.is_type_static
    set_type_static = _static.set_type_static
    set_type_static_final = _static.set_type_static_final
    set_type_final = _static.set_type_final
    make_recreate_cm = _static.make_recreate_cm

try:
    from _static import (
        TYPED_INT8,
        TYPED_INT16,
        TYPED_INT32,
        TYPED_INT64,
        TYPED_UINT8,
        TYPED_UINT16,
        TYPED_UINT32,
        TYPED_UINT64,
        TYPED_DOUBLE,
        TYPED_SINGLE,
        TYPED_BOOL,
        TYPED_CHAR,
        RAND_MAX,
        rand,
        posix_clock_gettime_ns,
    )
except ImportError:
    RAND_MAX = (1 << 31) - 1

    def rand():
        return random.randint(0, RAND_MAX)

    def posix_clock_gettime_ns():
        return time.clock_gettime_ns(time.CLOCK_MONOTONIC)


try:
    import cinder
except ImportError:
    cinder = None


pydict = dict
PyDict = Dict

clen = len


@set_type_final
@type_code(TYPED_UINT64)
class size_t(int):
    pass


@set_type_final
@type_code(TYPED_INT64)
class ssize_t(int):
    pass


@set_type_final
@type_code(TYPED_INT8)
class int8(int):
    pass


byte = int8


@set_type_final
@type_code(TYPED_INT16)
class int16(int):
    pass


@set_type_final
@type_code(TYPED_INT32)
class int32(int):
    pass


@set_type_final
@type_code(TYPED_INT64)
class int64(int):
    pass


@set_type_final
@type_code(TYPED_UINT8)
class uint8(int):
    pass


@set_type_final
@type_code(TYPED_UINT16)
class uint16(int):
    pass


@set_type_final
@type_code(TYPED_UINT32)
class uint32(int):
    pass


@set_type_final
@type_code(TYPED_UINT64)
class uint64(int):
    pass


@set_type_final
@type_code(TYPED_SINGLE)
class single(float):
    pass


@set_type_final
@type_code(TYPED_DOUBLE)
class double(float):
    pass


@set_type_final
@type_code(TYPED_CHAR)
class char(int):
    pass


@set_type_final
@type_code(TYPED_BOOL)
class cbool(int):
    pass


ArrayElement = TypeVar(
    "ArrayElement",
    int8,
    int16,
    int32,
    int64,
    uint8,
    uint16,
    uint32,
    uint64,
    char,
    float,
    double,
)

_TYPE_SIZES = {tc: array.array(tc).itemsize for tc in array.typecodes}

# These should be in sync with the array module
_TYPE_CODES = {
    int8: "b",
    uint8: "B",
    int16: "h",
    uint16: "H",
    # apparently, l is equivalent to q for us, but that may not be true everywhere.
    int32: "i" if _TYPE_SIZES["i"] == 4 else "l",
    uint32: "I" if _TYPE_SIZES["I"] == 4 else "L",
    int64: "q",
    uint64: "Q",
    float: "f",
    double: "d",
    char: "B",
}

TVarOrType = Union[TypeVar, Type[object]]


def _subs_tvars(
    tp: Tuple[TVarOrType, ...],
    tvars: Tuple[TVarOrType, ...],
    subs: Tuple[TVarOrType, ...],
) -> Type[object]:
    """Substitute type variables 'tvars' with substitutions 'subs'.
    These two must have the same length.
    """
    if not hasattr(tp, "__args__"):
        return tp

    new_args = list(tp.__args__)
    for a, arg in enumerate(tp.__args__):
        if isinstance(arg, TypeVar):
            for i, tvar in enumerate(tvars):
                if arg == tvar:
                    if (
                        tvar.__constraints__
                        and not isinstance(subs[i], TypeVar)
                        and not issubclass(subs[i], tvar.__constraints__)
                    ):
                        raise TypeError(
                            f"Invalid type for {tvar.__name__}: {subs[i].__name__} when instantiating {tp.__name__}"
                        )

                    new_args[a] = subs[i]
        else:
            new_args[a] = _subs_tvars(arg, tvars, subs)

    return _replace_types(tp, tuple(new_args))


def _collect_type_vars(types: Tuple[TVarOrType, ...]) -> Tuple[TypeVar, ...]:
    """Collect all type variable contained in types in order of
    first appearance (lexicographic order). For example::

        _collect_type_vars((T, List[S, T])) == (T, S)
    """
    tvars = []
    for t in types:
        if isinstance(t, TypeVar) and t not in tvars:
            tvars.append(t)
        if hasattr(t, "__parameters__"):
            tvars.extend([t for t in t.__parameters__ if t not in tvars])
    return tuple(tvars)


def make_generic_type(
    gen_type: Type[object], params: Tuple[Type[object], ...]
) -> Type[object]:
    if len(params) != len(gen_type.__parameters__):
        raise TypeError(f"Incorrect number of type arguments for {gen_type.__name__}")

    # Substitute params into __args__ replacing instances of __parameters__
    return _subs_tvars(
        gen_type,
        gen_type.__parameters__,
        params,
    )


def _replace_types(
    gen_type: Type[object], subs: Tuple[Type[object], ...]
) -> Type[object]:
    existing_inst = gen_type.__origin__.__insts__.get(subs)

    if existing_inst is not None:
        return existing_inst

    # Check if we have a full instantation, and verify the constraints
    new_dict = dict(gen_type.__dict__)
    has_params = False
    for sub in subs:
        if isinstance(sub, TypeVar) or hasattr(sub, "__parameters__"):
            has_params = True
            continue

    # Remove the existing StaticGeneric base...
    bases = tuple(
        base for base in gen_type.__orig_bases__ if not isinstance(base, StaticGeneric)
    )

    new_dict["__args__"] = subs
    if not has_params:
        # Instantiated types don't have generic parameters anymore.
        del new_dict["__parameters__"]
    else:
        new_vars = _collect_type_vars(subs)
        new_gen = StaticGeneric()
        new_gen.__parameters__ = new_vars
        new_dict["__orig_bases__"] = bases + (new_gen,)
        bases += (StaticGeneric,)
        new_dict["__parameters__"] = new_vars

    # Eventually we'll want to have some processing of the members here to
    # bind the generics through.  That may be an actual process which creates
    # new objects with the generics bound, or a virtual process.  For now
    # we just propagate the members to the new type.
    param_names = ", ".join(param.__name__ for param in subs)

    res = type(f"{gen_type.__origin__.__name__}[{param_names}]", bases, new_dict)
    res.__origin__ = gen_type

    if not has_params:
        # specialize the type
        for name, value in new_dict.items():
            if isinstance(value, FunctionType):
                if hasattr(value, "__runtime_impl__"):
                    setattr(
                        res,
                        name,
                        _static.specialize_function(res, value.__qualname__, subs),
                    )

    if cinder is not None:
        cinder.freeze_type(res)

    gen_type.__origin__.__insts__[subs] = res
    return res


def _runtime_impl(f):
    """marks a generic function as being runtime-implemented"""
    f.__runtime_impl__ = True
    return f


class StaticGeneric:
    """Base type used to mark static-Generic classes.  Instantations of these
    classes share different generic types and the generic type arguments can
    be accessed via __args___"""

    @_tp_cache
    def __class_getitem__(
        cls, elem_type: Tuple[Union[TypeVar, Type[object]]]
    ) -> Union[StaticGeneric, Type[object]]:
        if not isinstance(elem_type, tuple):
            # we specifically recurse to hit the type cache
            return cls[
                elem_type,
            ]

        if cls is StaticGeneric:
            res = StaticGeneric()
            res.__parameters__ = elem_type
            return res

        return set_type_static_final(make_generic_type(cls, elem_type))

    def __init_subclass__(cls) -> None:
        type_vars = _collect_type_vars(cls.__orig_bases__)
        cls.__origin__ = cls
        cls.__parameters__ = type_vars
        if not hasattr(cls, "__args__"):
            cls.__args__ = type_vars
        cls.__insts__ = WeakValueDictionary()

    def __mro_entries__(self, bases) -> Tuple[Type[object, ...]]:
        return (StaticGeneric,)

    def __repr__(self) -> str:
        return (
            "<StaticGeneric: "
            + ", ".join([param.__name__ for param in self.__parameters__])
            + ">"
        )


@set_type_final
class Array(array.array, StaticGeneric[ArrayElement]):
    __slots__ = ()

    def __new__(cls, initializer: int | Iterable[ArrayElement]):
        if hasattr(cls, "__parameters__"):
            raise TypeError("Cannot create plain Array")

        typecode = _TYPE_CODES[cls.__args__[0]]
        if isinstance(initializer, int):
            res = array.array.__new__(cls, typecode, [0])
            res *= initializer
            return res
        else:
            return array.array.__new__(cls, typecode, initializer)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return type(self)(array.array.__getitem__(self, index))

        return array.array.__getitem__(self, index)

    def __deepcopy__(self, memo):
        return type(self)(self)


@set_type_final
class Vector(array.array, StaticGeneric[ArrayElement]):
    """Vector is a resizable array of primitive elements"""

    __slots__ = ()

    def __new__(cls, initializer: int | Iterable[ArrayElement] | None = None):
        if hasattr(cls, "__parameters__"):
            raise TypeError("Cannot create plain Vector")

        typecode = _TYPE_CODES[cls.__args__[0]]
        if isinstance(initializer, int):
            # specifing size
            res = array.array.__new__(cls, typecode, [0])
            res *= initializer
            return res
        elif initializer is not None:
            return array.array.__new__(cls, typecode, initializer)
        else:
            return array.array.__new__(cls, typecode)

    if _static is not None:

        @_runtime_impl
        def append(self, value: ArrayElement) -> None:
            super().append(value)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return type(self)(array.array.__getitem__(self, index))

        return array.array.__getitem__(self, index)

    def __deepcopy__(self, memo):
        return type(self)(self)


def box(o):
    return o


def unbox(o):
    return o


def allow_weakrefs(klass):
    return klass


def dynamic_return(func):
    return func


def inline(func):
    return func


def _donotcompile(func):
    return func


def cast(typ, val):
    union_args = None
    if type(typ) is _GenericAlias:
        typ, args = typ.__origin__, typ.__args__
        if typ is Union:
            union_args = args
    elif type(typ) is typesUnion:
        union_args = typ.__args__
    if union_args:
        typ = None
        if len(union_args) == 2:
            if union_args[0] is type(None):
                typ = union_args[1]
            elif union_args[1] is type(None):
                typ = union_args[0]
        if typ is None:
            raise ValueError("cast expects type or Optional[T]")
        if val is None:
            return None

    inst_type = type(val)
    if typ not in inst_type.__mro__:
        raise TypeError(f"expected {typ.__name__}, got {type(val).__name__}")

    return val


def prod_assert(value: bool, message: Optional[str] = None):
    if not value:
        raise AssertionError(message) if message else AssertionError()


CheckedDict = chkdict
CheckedList = chklist


async def _return_none():
    """This exists solely as a helper for the ContextDecorator C implementation"""
    pass


class ContextDecorator:
    def __enter__(self) -> None:
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> bool:
        return False

    @final
    def __call__(self, func):
        if not iscoroutinefunction(func):

            @functools.wraps(func)
            def _no_profile_inner(*args, **kwds):
                with self._recreate_cm():
                    return func(*args, **kwds)

        else:

            @functools.wraps(func)
            async def _no_profile_inner(*args, **kwds):
                with self._recreate_cm():
                    return await func(*args, **kwds)

        # This will replace the vector call entry point with a C implementation.
        # We still want to return a function object because various things check
        # for functions or if an object is a co-routine.
        return _static.make_context_decorator_wrapper(self, _no_profile_inner, func)


ContextDecorator._recreate_cm = make_recreate_cm(ContextDecorator)
set_type_static(ContextDecorator)
