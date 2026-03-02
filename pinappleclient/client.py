import base64
from dataclasses import dataclass, field
from datetime import datetime
import time
import json
from typing import Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import polars as pl
import threading


@dataclass
class PinappleClient:
    user: str
    password: str
    api_url: str
    refresh_token_after_x_minutes: int = 5
    timeout: int = 30
    max_retries: int = 3
    backoff_base: float = 2.0
    _session: requests.Session = field(default=None, init=False, repr=False)
    _token: Optional[str] = field(default=None, init=False, repr=False)
    _lock: threading.Lock = field(
        default_factory=threading.Lock, init=False, repr=False
    )

    def __post_init__(self) -> None:
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=0,
            connect=self.max_retries,
            read=self.max_retries,
            backoff_factor=self.backoff_base,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def close(self) -> None:
        if self._session:
            self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_token_expiration(self) -> Optional[datetime]:
        if self._token is None:
            return None

        try:
            payload_b64 = self._token.split(".")[1]
            payload_b64 += "=" * (4 - len(payload_b64) % 4)
            payload = json.loads(base64.b64decode(payload_b64))

            exp_timestamp = payload.get("exp")
            if exp_timestamp is None:
                return None

            return datetime.fromtimestamp(exp_timestamp)
        except Exception:
            return None

    def should_refresh_token(self) -> bool:
        exp_time = self.get_token_expiration()
        if exp_time is None:
            return True

        time_until_exp = (exp_time - datetime.now()).total_seconds()
        return time_until_exp <= (self.refresh_token_after_x_minutes * 60)

    def get_token(self) -> str:
        with self._lock:
            if self._token is None or self.should_refresh_token():
                token_response = self._call_api(
                    endpoint="auth/token",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={"username": self.user, "password": self.password},
                )
                if "access_token" not in token_response:
                    raise Exception(str(token_response))
                self._token = token_response["access_token"]
        return self._token

    def _call_api(
        self,
        endpoint: str,
        headers: dict[str, str],
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        for attempt in range(self.max_retries):
            try:
                response = self._session.post(
                    f"{self.api_url}/{endpoint}",
                    json=data if endpoint != "auth/token" else None,
                    data=data if endpoint == "auth/token" else None,
                    headers=headers,
                    timeout=self.timeout,
                )

                if response.status_code == 503:
                    if attempt == self.max_retries - 1:
                        raise Exception(
                            f"Failed after {self.max_retries} attempts: Database connection error"
                        )

                    wait_time = self.backoff_base ** (attempt + 1)
                    print(
                        f"Attempt {attempt + 1} failed: Database error. Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()

                try:
                    return response.json()
                except Exception:
                    raise Exception(
                        f"{self.api_url}/{endpoint}: Non-JSON response: {response.text}"
                    )

            except requests.exceptions.HTTPError as e:
                raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
            ) as e:
                if attempt == self.max_retries - 1:
                    raise Exception(
                        f"Failed after {self.max_retries} attempts: {str(e)}"
                    )

                wait_time = self.backoff_base ** (attempt + 1)
                print(
                    f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)

        raise Exception(f"Exhausted all retries for {endpoint}")

    def encrypt_pins(self, pins: list[str]) -> list[dict[str, Any]]:
        token = self.get_token()
        return self._call_api(
            endpoint="v2/encrypt",
            headers={
                "Authorization": f"bearer {token}",
                "Content-Type": "application/json",
            },
            data={"pins": pins},
        )

    def decrypt_pins(self, encrypted_strings: list[str]) -> list[dict[str, str | bool]]:
        token = self.get_token()
        return self._call_api(
            endpoint="v2/decrypt",
            headers={
                "Authorization": f"bearer {token}",
                "Content-Type": "application/json",
            },
            data={"encrypted_strings": encrypted_strings},
        )

    def validate_pins(self, pins: list[str]) -> list[dict]:
        response = self._session.post(
            f"{self.api_url}/v2/validate", json={"pins": pins}
        )
        response.raise_for_status()
        return response.json()

    def encrypt_pandas_dataframe(
        self,
        df: pd.DataFrame,
        column_name: str,
        batch_size: int = 100,
    ) -> pd.DataFrame:
        mask = pd.notna(df[column_name])
        pins_to_encrypt = df.loc[mask, column_name].astype(str).tolist()

        print(f"Encrypting {len(pins_to_encrypt)} rows (pandas)")

        all_results = []
        for i in range(0, len(pins_to_encrypt), batch_size):
            batch = pins_to_encrypt[i : i + batch_size]
            results = self.encrypt_pins(pins=batch)
            all_results.extend(results)

        pin_to_encrypted = {r["pin"]: r["encrypted_id"] for r in all_results}

        df.loc[mask, column_name] = (
            df.loc[mask, column_name]
            .astype(str)
            .map(pin_to_encrypted)
            .fillna(df.loc[mask, column_name])
        )

        return df

    def encrypt_polars_dataframe(
        self,
        df: pl.DataFrame,
        column_name: str,
        batch_size: int = 100,
    ) -> pl.DataFrame:
        mask = df[column_name].is_not_null()
        pins_to_encrypt = df.filter(mask)[column_name].cast(pl.Utf8).to_list()

        print(f"Encrypting {len(pins_to_encrypt)} rows (polars)")

        all_results = []
        for i in range(0, len(pins_to_encrypt), batch_size):
            batch = pins_to_encrypt[i : i + batch_size]
            results = self.encrypt_pins(pins=batch)
            all_results.extend(results)

        pin_to_encrypted = {r["pin"]: r["encrypted_id"] for r in all_results}

        df = df.with_columns(
            pl.when(mask)
            .then(
                pl.col(column_name)
                .cast(pl.Utf8)
                .replace_strict(
                    pin_to_encrypted, default=pl.col(column_name), return_dtype=pl.Utf8
                )
            )
            .otherwise(pl.col(column_name))
            .alias(column_name)
        )

        return df

    def decrypt_pandas_dataframe(
        self,
        df: pd.DataFrame,
        column_name: str,
        batch_size: int = 100,
    ) -> pd.DataFrame:
        mask = pd.notna(df[column_name])
        encrypted_to_decrypt = df.loc[mask, column_name].astype(str).tolist()

        print(f"Decrypting {len(encrypted_to_decrypt)} rows (pandas)")

        all_results = []
        for i in range(0, len(encrypted_to_decrypt), batch_size):
            batch = encrypted_to_decrypt[i : i + batch_size]
            results = self.decrypt_pins(encrypted_strings=batch)
            all_results.extend(results)

        encrypted_to_pin = {
            r["encrypted_string"]: r["decrypted_string"]
            for r in all_results
            if r["decrypted_string"] is not None
        }

        df.loc[mask, column_name] = (
            df.loc[mask, column_name].astype(str).map(encrypted_to_pin)
        )

        return df

    def decrypt_polars_dataframe(
        self,
        df: pl.DataFrame,
        column_name: str,
        batch_size: int = 100,
    ) -> pl.DataFrame:
        mask = df[column_name].is_not_null()
        encrypted_to_decrypt = df.filter(mask)[column_name].cast(pl.Utf8).to_list()

        print(f"Decrypting {len(encrypted_to_decrypt)} rows (polars)")

        all_results = []
        for i in range(0, len(encrypted_to_decrypt), batch_size):
            batch = encrypted_to_decrypt[i : i + batch_size]
            results = self.decrypt_pins(encrypted_strings=batch)
            all_results.extend(results)

        encrypted_to_pin = {
            r["encrypted_string"]: r["decrypted_string"]
            for r in all_results
            if r["decrypted_string"] is not None
        }

        df = df.with_columns(
            pl.when(mask)
            .then(
                pl.col(column_name)
                .cast(pl.Utf8)
                .replace_strict(encrypted_to_pin, default=None)
            )
            .otherwise(pl.col(column_name))
            .alias(column_name)
        )

        return df
