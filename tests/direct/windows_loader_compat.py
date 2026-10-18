"""Narrow Windows cleanup workaround for genlayer-test Direct Mode loading."""
import os
import tempfile

_original_unlink = os.unlink
_deferred = []
_temp_root = os.path.abspath(tempfile.gettempdir()).casefold()


def _unlink_or_defer(path, *args, **kwargs):
    try:
        return _original_unlink(path, *args, **kwargs)
    except PermissionError as error:
        candidate = os.path.abspath(os.fspath(path))
        if (os.name == "nt" and getattr(error, "winerror", None) == 32
                and os.path.dirname(candidate).casefold() == _temp_root
                and os.path.basename(candidate).startswith("tmp")):
            if candidate not in _deferred:
                _deferred.append(candidate)
            return None
        raise


if os.name == "nt":
    os.unlink = _unlink_or_defer


def pytest_sessionfinish(session, exitstatus):
    if os.name == "nt":
        os.unlink = _original_unlink
        for path in _deferred:
            try:
                _original_unlink(path)
            except FileNotFoundError:
                pass
