import contextlib
import importlib.abc
import importlib.util
import sys
import types
import urllib.error
import urllib.request

from typing import cast, Union


__all__ = ['UrlMetaFinder', 'github_repo', 'bitbucket_repo']


def check(url: str) -> bool:
    try:
        request = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(request):
            return True
    except (urllib.error.HTTPError, urllib.error.URLError):
        return False


class UrlModuleLoader(importlib.abc.SourceLoader):

    def __init__(self, baseurl: str) -> None:
        self._baseurl = baseurl

    def get_data(self, path: Union[bytes, str]) -> bytes:
        path = cast(str, path)
        try:
            with urllib.request.urlopen(path) as page:
                return page.read()
        except (urllib.error.HTTPError, urllib.error.URLError):
            raise ImportError(f"Can't load {path}")

    def get_filename(self, fullname: str) -> str:
        if fullname.startswith(self._baseurl):
            return fullname
        return self._baseurl + '/' + fullname.split('.')[-1] + '.py'

    def is_package(self, fullname: str) -> bool:
        return False

    def module_repr(self, module: types.ModuleType) -> str:
        return f'<urlmodule {module.__name__} from {module.__file__}>'


class UrlPackageLoader(UrlModuleLoader):

    def get_filename(self, fullname: str) -> str:
        if fullname.startswith(self._baseurl):
            return fullname
        return self._baseurl + '/' + fullname.split('.')[-1] + '/__init__.py'

    def is_package(self, fullname: str) -> bool:
        return True


class UrlMetaFinder(importlib.abc.MetaPathFinder):
    
    def __init__(self, module: str, base_url: str) -> None:
        self.module = module
        self.base_url = base_url

    def find_spec(self, fullname, path, target=None):
        if path is None:
            base_url = self.base_url
        else:
            if not path[0].startswith(self.base_url):
                return None
            base_url = path[0]

        if self.module:
            base_url = f"{base_url}/{self.module}"

        parts = fullname.split('.')
        basename = parts[-1]

        loader = None
        module_url = f"{base_url}/{basename}.py"
        package_url = f"{base_url}/{basename}/__init__.py"
        
        if check(module_url):
            loader = UrlModuleLoader(base_url)
        elif check(package_url):
            loader = UrlPackageLoader(base_url)
        else:
            return None

        origin = base_url
        return importlib.util.spec_from_loader(fullname, loader, origin=origin)


@contextlib.contextmanager
def github_repo(username: str, repo: str, *, module: str='', branch: str='master') -> None:
    try:
        github_raw_url = f"https://raw.githubusercontent.com/{username}/{repo}/{branch}"
        git_finder = UrlMetaFinder(module, github_raw_url)
        sys.meta_path.append(git_finder)
        yield
    finally:
        sys.meta_path.remove(git_finder)


@contextlib.contextmanager
def bitbucket_repo(username: str, repo: str, *, module: str='', branch: str='master') -> None:
    try:
        bitbucket_raw_url = f"https://bitbucket.org/{username}/{repo}/raw/{branch}"
        bitbucket_finder = UrlMetaFinder(module, bitbucket_raw_url)
        sys.meta_path.append(bitbucket_finder)
        yield
    finally:
        sys.meta_path.remove(bitbucket_finder)
