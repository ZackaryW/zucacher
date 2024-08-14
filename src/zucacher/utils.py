from functools import lru_cache
from hashlib import sha256
from .tokens import _Token
import json


@lru_cache(maxsize=512)
def _internal_caching(string: str):
    return sha256(string.encode()).hexdigest()


def gen_token_hash(token: _Token):
    return _internal_caching(json.dumps(sorted(token)))
