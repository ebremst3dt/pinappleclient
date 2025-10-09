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

                try:
                    return response.json()
                except Exception:
                    raise Exception(
                        f"{self.api_url}/{endpoint}: Non-JSON response: {response.text}"
                    )

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

    def encrypt_pin_strict(self, pin: str) -> Optional[str]:
        token = self.get_token()
        encrypted_response = self._call_api(
            endpoint="encrypt/strict",
            headers={
                "Authorization": f"bearer {token}",
                "Content-Type": "application/json",
            },
            data={"input_string": pin},
        )

        if "encrypted_string" not in encrypted_response:
            raise Exception(str(encrypted_response))

        return encrypted_response["encrypted_string"]

    def encrypt_pin_loose(self, pin: str) -> Optional[str]:
        token = self.get_token()
        encrypted_response = self._call_api(
            endpoint="encrypt/loose",
            headers={
                "Authorization": f"bearer {token}",
                "Content-Type": "application/json",
            },
            data={"input_string": pin},
        )

        if "encrypted_string" not in encrypted_response:
            raise Exception(str(encrypted_response))

        return encrypted_response["encrypted_string"]

    def encrypt_pin_strict_then_loose(self, pin: str) -> Optional[str]:
        token = self.get_token()
        encrypted_response_strict = self._call_api(
            endpoint="encrypt/strict",
            headers={
                "Authorization": f"bearer {token}",
                "Content-Type": "application/json",
            },
            data={"input_string": pin},
        )

        if "encrypted_string" not in encrypted_response_strict:
            encrypted_response_loose = self._call_api(
                endpoint="encrypt/loose",
                headers={
                    "Authorization": f"bearer {token}",
                    "Content-Type": "application/json",
                },
                data={"input_string": pin},
            )
            if "encrypted_string" not in encrypted_response_loose:
                raise Exception(str(encrypted_response_loose))

            return encrypted_response_loose["encrypted_string"]

        return encrypted_response_strict["encrypted_string"]

    def decrypt_pin(self, encrypted_data: dict[str, Any]) -> Optional[str]:
        token = self.get_token()
        decrypted_response = self._call_api(
            endpoint="decrypt",
            headers={
                "Authorization": f"bearer {token}",
                "Content-Type": "application/json",
            },
            data=encrypted_data,
        )

        if "decrypted_string" not in decrypted_response:
            raise Exception(str(decrypted_response))

        return decrypted_response["decrypted_string"]

    def encrypt_dataframe(
        self,
        df: pd.DataFrame,
        column: str,
        strict: bool = True,
        strict_then_loose: bool = False,
    ) -> pd.DataFrame:
        encrypt_func = self.encrypt_pin_strict if strict else self.encrypt_pin_loose

        if strict_then_loose:
            encrypt_func = self.encrypt_pin_strict_then_loose

        mask = pd.notna(df[column])
        print(f"Running {mask.sum()} rows through encryption.")
        df.loc[mask, column] = df.loc[mask, column].apply(encrypt_func)
        return df

    def encrypt_pin_strict_bulk(self, pins: list[str]) -> list[dict[str, Any]]:
        token = self.get_token()
        encrypted_response = self._call_api(
            endpoint="encrypt/strict/bulk",
            headers={
                "Authorization": f"bearer {token}",
                "Content-Type": "application/json",
            },
            data={"pins": pins},
        )

        if not isinstance(encrypted_response, list):
            raise Exception(str(encrypted_response))

        return encrypted_response

    def encrypt_pin_loose_bulk(self, pins: list[str]) -> list[dict[str, Any]]:
        token = self.get_token()
        encrypted_response = self._call_api(
            endpoint="encrypt/loose/bulk",
            headers={
                "Authorization": f"bearer {token}",
                "Content-Type": "application/json",
            },
            data={"pins": pins},
        )

        if not isinstance(encrypted_response, list):
            raise Exception(str(encrypted_response))

        return encrypted_response

    def encrypt_pin_strict_then_loose_bulk(
        self, pins: list[str]
    ) -> list[dict[str, Any]]:
        results_strict = self.encrypt_pin_strict_bulk(pins=pins)

        failed_pins = [r["pin"] for r in results_strict if not r["success"]]

        if not failed_pins:
            return results_strict

        results_loose = self.encrypt_pin_loose_bulk(pins=failed_pins)

        loose_lookup = {r["pin"]: r for r in results_loose}

        final_results = []
        for result in results_strict:
            if result["success"]:
                final_results.append(result)
            else:
                final_results.append(loose_lookup[result["pin"]])

        return final_results

    def encrypt_dataframe_bulk(
        self,
        df: pd.DataFrame,
        column: str,
        strict: bool = True,
        strict_then_loose: bool = False,
        batch_size: int = 100,
    ) -> pd.DataFrame:
        mask = pd.notna(df[column])
        pins_to_encrypt = df.loc[mask, column].astype(str).tolist()

        print(f"Running {len(pins_to_encrypt)} rows through bulk encryption.")

        all_results = []
        for i in range(0, len(pins_to_encrypt), batch_size):
            batch = pins_to_encrypt[i : i + batch_size]

            if strict_then_loose:
                results = self.encrypt_pin_strict_then_loose_bulk(pins=batch)
            elif strict:
                results = self.encrypt_pin_strict_bulk(pins=batch)
            else:
                results = self.encrypt_pin_loose_bulk(pins=batch)

            all_results.extend(results)

        pin_to_encrypted = {
            r["pin"]: r["encrypted_id"] for r in all_results if r["success"]
        }

        df.loc[mask, column] = df.loc[mask, column].astype(str).map(pin_to_encrypted)

        return df
