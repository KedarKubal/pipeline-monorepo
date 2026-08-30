import httpx
import pytest
import respx

from src.flags_client import FlagsClient


@respx.mock
def test_is_enabled_returns_true_when_flag_on():
    respx.get("http://toggle:3000/api/flags/strict-email-validation").mock(
        return_value=httpx.Response(200, json={"enabled": True})
    )
    client = FlagsClient("http://toggle:3000")
    assert client.is_enabled("strict-email-validation") is True


@respx.mock
def test_is_enabled_fails_open_on_connection_error():
    respx.get("http://toggle:3000/api/flags/strict-email-validation").mock(
        side_effect=httpx.ConnectError("refused")
    )
    client = FlagsClient("http://toggle:3000")
    assert client.is_enabled("strict-email-validation", default=False) is False


@respx.mock
def test_is_enabled_caches_after_first_lookup():
    route = respx.get("http://toggle:3000/api/flags/x").mock(
        return_value=httpx.Response(200, json={"enabled": True})
    )
    client = FlagsClient("http://toggle:3000")
    client.is_enabled("x")
    client.is_enabled("x")
    assert route.call_count == 1
