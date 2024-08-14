import datetime
import logging
import os
import shutil
import typing

from zucacher.utils import gen_token_hash
from .index import Index
from .tokens import _Token, Ext, get_token_type
import tempfile
from zuu.stdpkg.hashlib import hash_file


class Cacher(Ext):
    def __init__(self, index: Index = None, path: str = None):
        assert not (index and path), "Either index or path must be provided, not both"
        self.__index = index or Index.auto(path)

    @property
    def index(self):
        return self.__index

    def check_expired(self, token: _Token):
        var = self.__index.get_vars(token)
        lifetime = var.get("lifetime", None)
        if lifetime is None:
            return False

        last_checked = var.get("last_checked", None)
        if last_checked is None:
            return True

        now = datetime.datetime.now()
        last_checked = datetime.datetime.fromtimestamp(last_checked)
        res = now > last_checked + datetime.timedelta(seconds=lifetime)
        if res:
            return True

        mtype = get_token_type(token)
        additional_check_method = getattr(self, f"check_expired_{mtype.__name__}", None)
        if additional_check_method:
            res = additional_check_method(token)

        return res

    def fetch(self, token: _Token):
        mtype = get_token_type(token)
        hashes = []
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = getattr(self, f"fetch_{mtype.__name__}")(token, tmpdir)
            for path in paths:
                fhash = hash_file(path)
                os.makedirs(
                    os.path.join(self.__index.cachepath, fhash[:2]), exist_ok=True
                )
                shutil.copy(
                    path, os.path.join(self.__index.cachepath, fhash[:2], fhash[2:])
                )
                hashes.append(fhash)

        return hashes

    def register(self, token: _Token, lifetime: int = None, var: dict = None):
        if self.__index.exists(token):
            return False

        hashes = self.fetch(token)
        self.index.add_new(token, hashes, lifetime, var)
        return True

    def check(self, token: _Token, save: bool = True):
        if not self.__index.exists(token):
            raise ValueError("Token does not exist")

        if not self.check_expired(token):
            logging.info(f"Token {gen_token_hash(token)[:8]} is not expired")
            return

        logging.info(f"Token {gen_token_hash(token)[:8]} is expired")

        hashes = self.fetch(token)
        self.index.historize_token(token)
        self.index.update_hashes(token, hashes)
        if save:
            self.index.save()

    def check_all(self, save: bool = True):
        for _, token in self.__index.tokens():
            self.check(token, save=False)

        if save:
            self.index.save()

    def at(
        self,
        token: _Token,
        lifetime=None,
        var=None,
        save: typing.Union[typing.List[str], bool] = None,
        cwd : str = None
    ):
        if not self.__index.exists(token):
            self.register(token, lifetime, var)
        else:
            self.check(token)
        self.index.save()
        filepathes = self.index.get_files(token)
        if save:
            if save is True:
                method = f"getfilename_{get_token_type(token).__name__}"
                save = getattr(self, method)(token)
            if cwd:
                currentcwd = os.getcwd()
                os.chdir(cwd)

            for i in range(len(filepathes)):
                shutil.copy(filepathes[i], save[i])

            if cwd:
                os.chdir(currentcwd)

        else:
            return filepathes