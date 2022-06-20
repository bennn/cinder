from __future__ import annotations

import ast
from ast import AST, Call, Index, Name, Subscript
from typing import Any, Optional, Tuple, Union

READONLY_CALL: str = "readonly"
READONLY_FUNC: str = "readonly_func"
READONLY_CLOSURE: str = "readonly_closure"

READONLY_DECORATORS = ("readonly_func", "readonly_closure")


def is_readonly_wrapped(node: AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    return isinstance(node.func, Name) and node.func.id == READONLY_CALL


def is_tuple_wrapped(node: AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    return isinstance(node.func, Name) and node.func.id == "tuple"


def is_readonly_func(node: AST) -> bool:
    return isinstance(node, Name) and node.id == READONLY_FUNC


def is_readonly_closure(node: AST) -> bool:
    return isinstance(node, Name) and node.id == READONLY_CLOSURE
