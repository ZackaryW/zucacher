from typing import TypedDict
import typing
from .tokens import _Token


class Var(TypedDict, total=False):
    lifetime: typing.NotRequired[int]
    last_checked: typing.NotRequired[int]


class IndexModel(TypedDict):
    vars: typing.Dict[str, Var]
    tokens: typing.Dict[str, _Token]

    # reversed [thash, list[sha256]]
    files: typing.Dict[str, typing.List[str]]
