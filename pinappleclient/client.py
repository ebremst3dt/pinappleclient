from dataclasses import dataclass
from typing import Optional, Dict, Any
import requests
import pandas as pd


@dataclass
class PinappleClient:
    user: str
    password: str
    api_url: str

    def __post_init__(self) -> None:
        self._token: Optional[str] = None

    def _call_api(
        self,
        endpoint: str,
        headers: Dict[str, str],
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        response = requests.post(
            f"{self.api_url}/{endpoint}",
            json=data if endpoint != "auth/token" else None,
            data=data if endpoint == "auth/token" else None,
            headers=headers,
        )

        try:
            return response.json()
        except Exception:
            raise Exception(
                f"{self.api_url}/{endpoint}: Non-JSON response: {response.text}"
            )

    def get_token(self) -> str:
        if self._token is None:
            token_response = self._call_api(
                endpoint="auth/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={"username": self.user, "password": self.password},
            )
            if "access_token" not in token_response:
                raise Exception(str(token_response))
            self._token = token_response["access_token"]
        return self._token

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

    def decrypt_pin(self, encrypted_data: Dict[str, Any]) -> Optional[str]:
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
