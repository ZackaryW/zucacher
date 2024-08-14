import os
from typing import TypedDict
import typing
import tempfile
from zuu.app.github import download_github_raw_content


class _Token(TypedDict):
    newer: typing.Optional[str]


class GithubRepoFile(_Token):
    org: str
    repo: str
    branch: typing.Optional[str]
    path: str


class GithubGist(_Token):
    id: str
    filename: typing.Optional[typing.Union[str, typing.List[str]]]


class GithubRelease(_Token):
    org: str
    repo: str
    tag: str
    filename: str


types = [GithubRepoFile, GithubGist, GithubRelease]


def get_token_type(token: _Token) -> typing.Type[_Token]:
    if "path" in token:
        return GithubRepoFile
    elif "id" in token:
        return GithubGist
    elif "tag" in token:
        return GithubRelease
    else:
        raise ValueError("Invalid token")


class Ext:
    def fetch_GithubRepoFile(
        self, token: GithubRepoFile, tmpdir: tempfile.TemporaryDirectory
    ):
        url = f"{token['org']}/{token['repo']}/{token.get("branch", "main")}/{token['path']}"
        download_github_raw_content(
            url,
            f"{tmpdir}/{os.path.basename(token['path'])}",
        )
        return [f"{tmpdir}/{os.path.basename(token['path'])}"]

    def getfilename_GithubRepoFile(self, token: GithubRepoFile):
        return [token["path"]]