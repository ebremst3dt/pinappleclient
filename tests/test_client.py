import base64
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import polars as pl
import pytest
import requests

from pinappleclient.client import PinappleClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_jwt(exp: int) -> str:
    """Build a minimal JWT with the given exp timestamp."""
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    payload = (
        base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode())
        .rstrip(b"=")
        .decode()
    )
    return f"{header}.{payload}.sig"


def _client(**kwargs) -> PinappleClient:
    return PinappleClient(user="u", password="p", api_url="http://api", **kwargs)


# ---------------------------------------------------------------------------
# get_token_expiration
# ---------------------------------------------------------------------------


class TestGetTokenExpiration:
    def test_no_token_returns_none(self):
        client = _client()
        assert client.get_token_expiration() is None

    def test_valid_token_returns_datetime(self):
        client = _client()
        future = int((datetime.now() + timedelta(hours=1)).timestamp())
        client._token = _make_jwt(future)
        exp = client.get_token_expiration()
        assert isinstance(exp, datetime)
        assert abs(exp.timestamp() - future) < 1

    def test_token_without_exp_returns_none(self):
        client = _client()
        payload = base64.urlsafe_b64encode(b'{"sub":"x"}').rstrip(b"=").decode()
        client._token = f"h.{payload}.s"
        assert client.get_token_expiration() is None

    def test_malformed_token_returns_none(self):
        client = _client()
        client._token = "not.a.jwt"
        assert client.get_token_expiration() is None


# ---------------------------------------------------------------------------
# should_refresh_token
# ---------------------------------------------------------------------------


class TestShouldRefreshToken:
    def test_no_token_should_refresh(self):
        assert _client().should_refresh_token() is True

    def test_token_expiring_within_window_should_refresh(self):
        client = _client(refresh_token_after_x_minutes=5)
        # expires in 2 minutes — inside the 5-minute window
        exp = int((datetime.now() + timedelta(minutes=2)).timestamp())
        client._token = _make_jwt(exp)
        assert client.should_refresh_token() is True

    def test_token_with_plenty_of_time_should_not_refresh(self):
        client = _client(refresh_token_after_x_minutes=5)
        exp = int((datetime.now() + timedelta(hours=1)).timestamp())
        client._token = _make_jwt(exp)
        assert client.should_refresh_token() is False

    def test_expired_token_should_refresh(self):
        client = _client()
        exp = int((datetime.now() - timedelta(minutes=1)).timestamp())
        client._token = _make_jwt(exp)
        assert client.should_refresh_token() is True


# ---------------------------------------------------------------------------
# get_token
# ---------------------------------------------------------------------------


class TestGetToken:
    def test_fetches_token_when_none(self):
        client = _client()
        future = int((datetime.now() + timedelta(hours=1)).timestamp())
        token = _make_jwt(future)
        with patch.object(
            client, "_call_api", return_value={"access_token": token}
        ) as mock_api:
            result = client.get_token()
        assert result == token
        mock_api.assert_called_once()

    def test_reuses_valid_token(self):
        client = _client(refresh_token_after_x_minutes=5)
        future = int((datetime.now() + timedelta(hours=1)).timestamp())
        client._token = _make_jwt(future)
        with patch.object(client, "_call_api") as mock_api:
            result = client.get_token()
        mock_api.assert_not_called()
        assert result == client._token

    def test_raises_on_missing_access_token(self):
        client = _client()
        with patch.object(client, "_call_api", return_value={"error": "bad creds"}):
            with pytest.raises(Exception, match="bad creds"):
                client.get_token()


# ---------------------------------------------------------------------------
# _call_api
# ---------------------------------------------------------------------------


class TestCallApi:
    def _post_mock(self, status_code: int, json_body=None, text=""):
        response = MagicMock()
        response.status_code = status_code
        response.text = text
        if json_body is not None:
            response.json.return_value = json_body
        else:
            response.json.side_effect = Exception("no json")
        response.raise_for_status = MagicMock()
        if status_code >= 400:
            http_err = requests.exceptions.HTTPError(response=response)
            response.raise_for_status.side_effect = http_err
        return response

    def test_successful_post(self):
        client = _client(max_retries=1)
        resp = self._post_mock(200, json_body={"ok": True})
        with patch.object(client._session, "post", return_value=resp):
            result = client._call_api("some/endpoint", headers={})
        assert result == {"ok": True}

    def test_http_error_raises(self):
        client = _client(max_retries=1)
        resp = self._post_mock(401, text="Unauthorized")
        with patch.object(client._session, "post", return_value=resp):
            with pytest.raises(Exception, match="HTTP 401"):
                client._call_api("some/endpoint", headers={})

    def test_non_json_response_raises(self):
        client = _client(max_retries=1)
        resp = self._post_mock(200, json_body=None, text="not json")
        with patch.object(client._session, "post", return_value=resp):
            with pytest.raises(Exception, match="Non-JSON response"):
                client._call_api("some/endpoint", headers={})

    def test_503_retries_then_raises(self):
        client = _client(max_retries=2, backoff_base=0.0)
        resp = self._post_mock(503)
        resp.raise_for_status = (
            MagicMock()
        )  # 503 is handled manually, not via raise_for_status
        with (
            patch.object(client._session, "post", return_value=resp),
            patch("time.sleep"),
        ):
            with pytest.raises(Exception, match="Database connection error"):
                client._call_api("some/endpoint", headers={})

    def test_connection_error_retries_then_raises(self):
        client = _client(max_retries=2, backoff_base=0.0)
        with (
            patch.object(
                client._session,
                "post",
                side_effect=requests.exceptions.ConnectionError("refused"),
            ),
            patch("time.sleep"),
        ):
            with pytest.raises(Exception, match="Failed after 2 attempts"):
                client._call_api("some/endpoint", headers={})

    def test_auth_endpoint_uses_form_data(self):
        client = _client(max_retries=1)
        resp = self._post_mock(200, json_body={"access_token": "t"})
        with patch.object(client._session, "post", return_value=resp) as mock_post:
            client._call_api(
                "auth/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={"username": "u", "password": "p"},
            )
        _, kwargs = mock_post.call_args
        assert kwargs["data"] == {"username": "u", "password": "p"}
        assert kwargs["json"] is None


# ---------------------------------------------------------------------------
# encrypt_pins / decrypt_pins
# ---------------------------------------------------------------------------


class TestPinMethods:
    def _authed_client(self):
        client = _client()
        future = int((datetime.now() + timedelta(hours=1)).timestamp())
        client._token = _make_jwt(future)
        return client

    def test_encrypt_pins_calls_correct_endpoint(self):
        client = self._authed_client()
        expected = [{"pin": "1234", "encrypted_id": "enc_1234"}]
        with patch.object(client, "_call_api", return_value=expected) as mock_api:
            result = client.encrypt_pins(["1234"])
        assert result == expected
        mock_api.assert_called_once()
        assert mock_api.call_args.kwargs["endpoint"] == "v2/encrypt"

    def test_decrypt_pins_calls_correct_endpoint(self):
        client = self._authed_client()
        expected = [{"encrypted_string": "enc_1234", "decrypted_string": "1234"}]
        with patch.object(client, "_call_api", return_value=expected) as mock_api:
            result = client.decrypt_pins(["enc_1234"])
        assert result == expected
        mock_api.assert_called_once()
        assert mock_api.call_args.kwargs["endpoint"] == "v2/decrypt"


# ---------------------------------------------------------------------------
# DataFrame methods
# ---------------------------------------------------------------------------


class TestPandasDataframe:
    def _authed_client(self):
        client = _client()
        future = int((datetime.now() + timedelta(hours=1)).timestamp())
        client._token = _make_jwt(future)
        return client

    def test_encrypt_pandas_dataframe(self):
        client = self._authed_client()
        df = pd.DataFrame({"pin": ["1111", "2222", None]})
        encrypt_response = [
            {"pin": "1111", "encrypted_id": "ENC_1111"},
            {"pin": "2222", "encrypted_id": "ENC_2222"},
        ]
        with patch.object(client, "encrypt_pins", return_value=encrypt_response):
            result = client.encrypt_pandas_dataframe(df, "pin")
        assert result.loc[0, "pin"] == "ENC_1111"
        assert result.loc[1, "pin"] == "ENC_2222"
        assert pd.isna(result.loc[2, "pin"])

    def test_decrypt_pandas_dataframe(self):
        client = self._authed_client()
        df = pd.DataFrame({"pin": ["ENC_1111", "ENC_2222"]})
        decrypt_response = [
            {"encrypted_string": "ENC_1111", "decrypted_string": "1111"},
            {"encrypted_string": "ENC_2222", "decrypted_string": "2222"},
        ]
        with patch.object(client, "decrypt_pins", return_value=decrypt_response):
            result = client.decrypt_pandas_dataframe(df, "pin")
        assert result.loc[0, "pin"] == "1111"
        assert result.loc[1, "pin"] == "2222"

    def test_encrypt_pandas_batches(self):
        client = self._authed_client()
        df = pd.DataFrame({"pin": [str(i) for i in range(5)]})
        encrypt_response = [
            {"pin": str(i), "encrypted_id": f"ENC_{i}"} for i in range(5)
        ]

        calls = []

        def fake_encrypt(pins):
            calls.append(pins)
            return [r for r in encrypt_response if r["pin"] in pins]

        with patch.object(client, "encrypt_pins", side_effect=fake_encrypt):
            client.encrypt_pandas_dataframe(df, "pin", batch_size=2)

        assert len(calls) == 3  # 5 rows / batch_size=2 → 3 batches


class TestPolarsDataframe:
    def _authed_client(self):
        client = _client()
        future = int((datetime.now() + timedelta(hours=1)).timestamp())
        client._token = _make_jwt(future)
        return client

    def test_encrypt_polars_dataframe(self):
        client = self._authed_client()
        df = pl.DataFrame({"pin": ["1111", "2222", None]})
        encrypt_response = [
            {"pin": "1111", "encrypted_id": "ENC_1111"},
            {"pin": "2222", "encrypted_id": "ENC_2222"},
        ]
        with patch.object(client, "encrypt_pins", return_value=encrypt_response):
            result = client.encrypt_polars_dataframe(df, "pin")
        pins = result["pin"].to_list()
        assert pins[0] == "ENC_1111"
        assert pins[1] == "ENC_2222"
        assert pins[2] is None

    def test_decrypt_polars_dataframe(self):
        client = self._authed_client()
        df = pl.DataFrame({"pin": ["ENC_1111", "ENC_2222"]})
        decrypt_response = [
            {"encrypted_string": "ENC_1111", "decrypted_string": "1111"},
            {"encrypted_string": "ENC_2222", "decrypted_string": "2222"},
        ]
        with patch.object(client, "decrypt_pins", return_value=decrypt_response):
            result = client.decrypt_polars_dataframe(df, "pin")
        assert result["pin"].to_list() == ["1111", "2222"]


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


class TestContextManager:
    def test_context_manager_closes_session(self):
        with _client() as client:
            client._session = MagicMock()
            session_mock = client._session
        session_mock.close.assert_called_once()
