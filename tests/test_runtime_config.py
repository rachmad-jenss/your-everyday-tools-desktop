import pytest


def test_flask_debug_is_opt_in(monkeypatch):
    from app import _debug_enabled

    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    assert _debug_enabled() is False

    monkeypatch.setenv("FLASK_DEBUG", "1")
    assert _debug_enabled() is True

    monkeypatch.setenv("FLASK_DEBUG", "true")
    assert _debug_enabled() is False
