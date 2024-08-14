import datetime
from functools import cached_property
import json
import os
import typing

from zucacher.storemodel import IndexModel
from .utils import gen_token_hash
from .tokens import _Token


class Index:
    __data: IndexModel

    def __init__(self, path: str):
        self.__path = path

    @classmethod
    def auto(cls, path: str):
        obj = cls(path)
        obj.load()
        return obj

    @classmethod
    def differed_path(cls, cache_path: str, index_path: str):
        obj = cls(None)
        obj.__dict__["indexpath"] = index_path
        obj.__dict__["cachepath"] = cache_path
        obj.load()
        return obj

    @cached_property
    def basepath(self):
        os.makedirs(self.__path, exist_ok=True)
        assert os.path.isdir(self.__path)
        return self.__path

    @cached_property
    def indexpath(self):
        return os.path.join(self.basepath, "index")

    @cached_property
    def cachepath(self):
        os.makedirs(os.path.join(self.basepath, "cache"), exist_ok=True)
        return os.path.join(self.basepath, "cache")

    def load(self):
        if not os.path.exists(self.indexpath):
            self.__data = IndexModel(vars={}, tokens={}, files={})
            return

        with open(self.indexpath, "r") as f:
            self.__data = json.load(f)

    def save(self):
        with open(self.indexpath, "w") as f:
            json.dump(self.__data, f, indent=2)

    def add_new(
        self,
        token: _Token,
        file: typing.Union[str, typing.List[str]],
        lifetime: int = None,
        var: dict = None,
    ):
        thash = gen_token_hash(token)

        self.__data["tokens"][thash] = token

        if not var:
            var = {}
        if lifetime:
            var["lifetime"] = lifetime

        self.__data["vars"][thash] = var

        if not isinstance(file, list):
            file = [file]

        self.__data["files"][thash] = file

    def match_token(self, currentonly: bool = False, **kwargs):
        for token in self.__data["tokens"].values():
            if currentonly and "newer" in token:
                continue

            for k, v in kwargs.items():
                if k not in token or token[k] != v:
                    break
            else:
                return token
        return None

    def get_lifetime(self, token: typing.Union[str, _Token]):
        if isinstance(token, dict):
            thash = gen_token_hash(token)
        else:
            thash = token

        return self.__data["vars"].get(thash, {}).get("lifetime", None)

    def get_vars(self, token: typing.Union[str, _Token]):
        if isinstance(token, dict):
            thash = gen_token_hash(token)
        else:
            thash = token

        return self.__data["vars"][thash]

    def get_files(self, token: typing.Union[str, _Token]):
        if isinstance(token, dict):
            thash = gen_token_hash(token)
        else:
            thash = token
        return [
            os.path.abspath(os.path.join(self.cachepath, f[:2], f[2:]))
            for f in self.__data["files"][thash]
        ]

    def update_last_checked(self, token: typing.Union[str, _Token]):
        if isinstance(token, dict):
            thash = gen_token_hash(token)
        else:
            thash = token

        self.__data["vars"][thash]["last_checked"] = datetime.datetime.now().timestamp()

    def update_lifetime(self, token: typing.Union[str, _Token], lifetime: int = None):
        if isinstance(token, dict):
            thash = gen_token_hash(token)
        else:
            thash = token

        if lifetime:
            self.__data["vars"][thash]["lifetime"] = lifetime
        else:
            self.__data["vars"][thash].pop("lifetime", None)

    def exists(self, token: typing.Union[str, _Token]):
        if isinstance(token, dict):
            thash = gen_token_hash(token)
        else:
            thash = token

        return thash in self.__data["tokens"]

    def iscurrent(self, token: typing.Union[str, _Token]):
        """
        Checks if the given token is currently valid and not expired.

        Args:
            token (typing.Union[str, _Token]): The token to check.

        Returns:
            bool: True if the token is currently valid, False otherwise.
        """
        if not self.exists(token):
            return False

        token = self.__data["tokens"][token] if isinstance(token, str) else token
        return "newer" not in token

    def historize_token(self, token: typing.Union[str, _Token]):
        if isinstance(token, dict):
            thash = gen_token_hash(token)
        else:
            thash = token

        token = self.__data["tokens"][thash]

        historize_token = token.copy()
        historize_token["newer"] = thash
        hthash = gen_token_hash(historize_token)

        self.__data["tokens"][hthash] = historize_token
        self.__data["vars"][hthash] = self.__data["vars"].get(thash, {}).copy()
        self.__data["files"][hthash] = self.__data["files"].get(thash, []).copy()

        return hthash

    def update_hashes(self, token: typing.Union[str, _Token], hashes: typing.List[str]):
        if isinstance(token, dict):
            thash = gen_token_hash(token)
        else:
            thash = token

        self.__data["files"][thash] = hashes

    def tokens(self):
        for thash, token in self.__data["tokens"].items():
            yield thash, token

    def vars(self):
        for thash, var in self.__data["vars"].items():
            yield thash, var

    def files(self):
        for thash, files in self.__data["files"].items():
            yield thash, files
