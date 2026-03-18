import pytest
from unittest.mock import patch
from pinappleclient.client import PinappleClient


class TestEncryptPins:
    @patch.object(PinappleClient, "get_token")
    @patch.object(PinappleClient, "_call_api")
    def test_encrypt_pins_success(self, mock_call_api, mock_get_token):
        mock_get_token.return_value = "test_token"
        mock_call_api.return_value = [
            {"pin": "123456", "encrypted_id": "abc123", "success": True}
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        result = client.encrypt_pins(pins=["123456"])

        assert len(result) == 1
        assert result[0]["pin"] == "123456"
        assert result[0]["encrypted_id"] == "abc123"
        assert result[0]["success"] is True

    @patch.object(PinappleClient, "get_token")
    @patch.object(PinappleClient, "_call_api")
    def test_encrypt_pins_multiple(self, mock_call_api, mock_get_token):
        mock_get_token.return_value = "test_token"
        mock_call_api.return_value = [
            {"pin": "123456", "encrypted_id": "abc123", "success": True},
            {"pin": "789012", "encrypted_id": "def456", "success": True},
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        result = client.encrypt_pins(pins=["123456", "789012"])

        assert len(result) == 2
        assert result[0]["pin"] == "123456"
        assert result[1]["pin"] == "789012"

    @patch.object(PinappleClient, "get_token")
    @patch.object(PinappleClient, "_call_api")
    def test_encrypt_pins_empty_list(self, mock_call_api, mock_get_token):
        mock_get_token.return_value = "test_token"
        mock_call_api.return_value = []

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        result = client.encrypt_pins(pins=[])

        assert len(result) == 0

    @patch.object(PinappleClient, "get_token")
    @patch.object(PinappleClient, "_call_api")
    def test_encrypt_pins_partial_failure(self, mock_call_api, mock_get_token):
        mock_get_token.return_value = "test_token"
        mock_call_api.return_value = [
            {"pin": "123456", "encrypted_id": "abc123", "success": True},
            {"pin": "invalid", "encrypted_id": None, "success": False},
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        result = client.encrypt_pins(pins=["123456", "invalid"])

        assert len(result) == 2
        assert result[0]["success"] is True
        assert result[1]["success"] is False

    @patch.object(PinappleClient, "get_token")
    @patch.object(PinappleClient, "_call_api")
    def test_encrypt_pins_api_error(self, mock_call_api, mock_get_token):
        mock_get_token.return_value = "test_token"
        mock_call_api.side_effect = Exception("API error")

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        with pytest.raises(Exception, match="API error"):
            client.encrypt_pins(pins=["123456"])


class TestDecryptPins:
    @patch.object(PinappleClient, "get_token")
    @patch.object(PinappleClient, "_call_api")
    def test_decrypt_pins_success(self, mock_call_api, mock_get_token):
        mock_get_token.return_value = "test_token"
        mock_call_api.return_value = [
            {"encrypted_string": "abc123", "decrypted_string": "123456"}
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        result = client.decrypt_pins(encrypted_strings=["abc123"])

        assert len(result) == 1
        assert result[0]["encrypted_string"] == "abc123"
        assert result[0]["decrypted_string"] == "123456"

    @patch.object(PinappleClient, "get_token")
    @patch.object(PinappleClient, "_call_api")
    def test_decrypt_pins_multiple(self, mock_call_api, mock_get_token):
        mock_get_token.return_value = "test_token"
        mock_call_api.return_value = [
            {"encrypted_string": "abc123", "decrypted_string": "123456"},
            {"encrypted_string": "def456", "decrypted_string": "789012"},
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        result = client.decrypt_pins(encrypted_strings=["abc123", "def456"])

        assert len(result) == 2
        assert result[0]["decrypted_string"] == "123456"
        assert result[1]["decrypted_string"] == "789012"

    @patch.object(PinappleClient, "get_token")
    @patch.object(PinappleClient, "_call_api")
    def test_decrypt_pins_empty_list(self, mock_call_api, mock_get_token):
        mock_get_token.return_value = "test_token"
        mock_call_api.return_value = []

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        result = client.decrypt_pins(encrypted_strings=[])

        assert len(result) == 0

    @patch.object(PinappleClient, "get_token")
    @patch.object(PinappleClient, "_call_api")
    def test_decrypt_pins_none_decrypted_string(self, mock_call_api, mock_get_token):
        mock_get_token.return_value = "test_token"
        mock_call_api.return_value = [
            {"encrypted_string": "abc123", "decrypted_string": None}
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        result = client.decrypt_pins(encrypted_strings=["abc123"])

        assert len(result) == 1
        assert result[0]["decrypted_string"] is None

    @patch.object(PinappleClient, "get_token")
    @patch.object(PinappleClient, "_call_api")
    def test_decrypt_pins_api_error(self, mock_call_api, mock_get_token):
        mock_get_token.return_value = "test_token"
        mock_call_api.side_effect = Exception("API error")

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        with pytest.raises(Exception, match="API error"):
            client.decrypt_pins(encrypted_strings=["abc123"])


class TestValidatePins:
    @patch("requests.Session.post")
    def test_validate_pins_success(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.json.return_value = [{"pin": "123456", "valid": True}]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        result = client.validate_pins(pins=["123456"])

        assert len(result) == 1
        assert result[0]["pin"] == "123456"
        assert result[0]["valid"] is True

    @patch("requests.Session.post")
    def test_validate_pins_multiple(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.json.return_value = [
            {"pin": "123456", "valid": True},
            {"pin": "invalid", "valid": False},
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        result = client.validate_pins(pins=["123456", "invalid"])

        assert len(result) == 2
        assert result[0]["valid"] is True
        assert result[1]["valid"] is False

    @patch("requests.Session.post")
    def test_validate_pins_empty_list(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.json.return_value = []

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        result = client.validate_pins(pins=[])

        assert len(result) == 0

    @patch("requests.Session.post")
    def test_validate_pins_http_error(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.raise_for_status.side_effect = Exception("HTTP error")

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        with pytest.raises(Exception, match="HTTP error"):
            client.validate_pins(pins=["123456"])


class TestEncryptPandasDataframe:
    @patch.object(PinappleClient, "encrypt_pins")
    def test_encrypt_pandas_dataframe_all_values(self, mock_encrypt):
        import pandas as pd

        mock_encrypt.return_value = [
            {"pin": "123456", "encrypted_id": "abc123", "success": True},
            {"pin": "789012", "encrypted_id": "def456", "success": True},
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        df = pd.DataFrame({"id": [1, 2], "pin": ["123456", "789012"]})

        result = client.encrypt_pandas_dataframe(df, "pin")

        assert result["pin"].iloc[0] == "abc123"
        assert result["pin"].iloc[1] == "def456"

    @patch.object(PinappleClient, "encrypt_pins")
    def test_encrypt_pandas_dataframe_with_nulls(self, mock_encrypt):
        import pandas as pd

        mock_encrypt.return_value = [
            {"pin": "123456", "encrypted_id": "abc123", "success": True}
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        df = pd.DataFrame({"id": [1, 2, 3], "pin": ["123456", None, "789012"]})

        result = client.encrypt_pandas_dataframe(df, "pin")

        assert result["pin"].iloc[0] == "abc123"
        assert pd.isna(result["pin"].iloc[1])

    @patch.object(PinappleClient, "encrypt_pins")
    def test_encrypt_pandas_dataframe_batching(self, mock_encrypt):
        import pandas as pd

        mock_encrypt.side_effect = [
            [{"pin": "123456", "encrypted_id": "abc123", "success": True}],
            [{"pin": "789012", "encrypted_id": "def456", "success": True}],
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        df = pd.DataFrame({"id": [1, 2], "pin": ["123456", "789012"]})

        result = client.encrypt_pandas_dataframe(df, "pin", batch_size=1)

        assert mock_encrypt.call_count == 2
        assert result["pin"].iloc[0] == "abc123"
        assert result["pin"].iloc[1] == "def456"

    @patch.object(PinappleClient, "encrypt_pins")
    def test_encrypt_pandas_dataframe_partial_success(self, mock_encrypt):
        import pandas as pd

        mock_encrypt.return_value = [
            {"pin": "123456", "encrypted_id": "abc123", "success": True},
            {"pin": "789012", "encrypted_id": None, "success": False},
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        df = pd.DataFrame({"id": [1, 2], "pin": ["123456", "789012"]})

        result = client.encrypt_pandas_dataframe(df, "pin")

        assert result["pin"].iloc[0] == "abc123"
        assert result["pin"].iloc[1] == "789012"

    @patch.object(PinappleClient, "encrypt_pins")
    def test_encrypt_pandas_dataframe_empty(self, mock_encrypt):
        import pandas as pd

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        df = pd.DataFrame({"id": [], "pin": []})
        result = client.encrypt_pandas_dataframe(df, "pin")

        assert len(result) == 0
        mock_encrypt.assert_not_called()


class TestEncryptPolarsDataframe:
    @patch.object(PinappleClient, "encrypt_pins")
    def test_encrypt_polars_dataframe_all_values(self, mock_encrypt):
        import polars as pl

        mock_encrypt.return_value = [
            {"pin": "123456", "encrypted_id": "abc123", "success": True},
            {"pin": "789012", "encrypted_id": "def456", "success": True},
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        df = pl.DataFrame({"id": [1, 2], "pin": ["123456", "789012"]})

        result = client.encrypt_polars_dataframe(df, "pin")

        assert result["pin"][0] == "abc123"
        assert result["pin"][1] == "def456"

    @patch.object(PinappleClient, "encrypt_pins")
    def test_encrypt_polars_dataframe_with_nulls(self, mock_encrypt):
        import polars as pl

        mock_encrypt.return_value = [
            {"pin": "123456", "encrypted_id": "abc123", "success": True}
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        df = pl.DataFrame({"id": [1, 2, 3], "pin": ["123456", None, "789012"]})

        result = client.encrypt_polars_dataframe(df, "pin")

        assert result["pin"][0] == "abc123"
        assert result["pin"][1] is None

    @patch.object(PinappleClient, "encrypt_pins")
    def test_encrypt_polars_dataframe_batching(self, mock_encrypt):
        import polars as pl

        mock_encrypt.side_effect = [
            [{"pin": "123456", "encrypted_id": "abc123", "success": True}],
            [{"pin": "789012", "encrypted_id": "def456", "success": True}],
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        df = pl.DataFrame({"id": [1, 2], "pin": ["123456", "789012"]})

        result = client.encrypt_polars_dataframe(df, "pin", batch_size=1)

        assert mock_encrypt.call_count == 2
        assert result["pin"][0] == "abc123"
        assert result["pin"][1] == "def456"

    @patch.object(PinappleClient, "encrypt_pins")
    def test_encrypt_polars_dataframe_empty(self, mock_encrypt):
        import polars as pl

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        df = pl.DataFrame({"id": [], "pin": []})
        result = client.encrypt_polars_dataframe(df, "pin")

        assert len(result) == 0
        mock_encrypt.assert_not_called()


class TestDecryptPandasDataframe:
    @patch.object(PinappleClient, "decrypt_pins")
    def test_decrypt_pandas_dataframe_all_values(self, mock_decrypt):
        import pandas as pd

        mock_decrypt.return_value = [
            {"encrypted_string": "abc123", "decrypted_string": "123456"},
            {"encrypted_string": "def456", "decrypted_string": "789012"},
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        df = pd.DataFrame({"id": [1, 2], "pin": ["abc123", "def456"]})

        result = client.decrypt_pandas_dataframe(df, "pin")

        assert result["pin"].iloc[0] == "123456"
        assert result["pin"].iloc[1] == "789012"

    @patch.object(PinappleClient, "decrypt_pins")
    def test_decrypt_pandas_dataframe_with_nulls(self, mock_decrypt):
        import pandas as pd

        mock_decrypt.return_value = [
            {"encrypted_string": "abc123", "decrypted_string": "123456"}
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        df = pd.DataFrame({"id": [1, 2, 3], "pin": ["abc123", None, "def456"]})

        result = client.decrypt_pandas_dataframe(df, "pin")

        assert result["pin"].iloc[0] == "123456"
        assert pd.isna(result["pin"].iloc[1])

    @patch.object(PinappleClient, "decrypt_pins")
    def test_decrypt_pandas_dataframe_batching(self, mock_decrypt):
        import pandas as pd

        mock_decrypt.side_effect = [
            [{"encrypted_string": "abc123", "decrypted_string": "123456"}],
            [{"encrypted_string": "def456", "decrypted_string": "789012"}],
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        df = pd.DataFrame({"id": [1, 2], "pin": ["abc123", "def456"]})

        result = client.decrypt_pandas_dataframe(df, "pin", batch_size=1)

        assert mock_decrypt.call_count == 2
        assert result["pin"].iloc[0] == "123456"
        assert result["pin"].iloc[1] == "789012"

    @patch.object(PinappleClient, "decrypt_pins")
    def test_decrypt_pandas_dataframe_empty(self, mock_decrypt):
        import pandas as pd

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        df = pd.DataFrame({"id": [], "pin": []})
        result = client.decrypt_pandas_dataframe(df, "pin")

        assert len(result) == 0
        mock_decrypt.assert_not_called()


class TestDecryptPolarsDataframe:
    @patch.object(PinappleClient, "decrypt_pins")
    def test_decrypt_polars_dataframe_all_values(self, mock_decrypt):
        import polars as pl

        mock_decrypt.return_value = [
            {"encrypted_string": "abc123", "decrypted_string": "123456"},
            {"encrypted_string": "def456", "decrypted_string": "789012"},
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        df = pl.DataFrame({"id": [1, 2], "pin": ["abc123", "def456"]})

        result = client.decrypt_polars_dataframe(df, "pin")

        assert result["pin"][0] == "123456"
        assert result["pin"][1] == "789012"

    @patch.object(PinappleClient, "decrypt_pins")
    def test_decrypt_polars_dataframe_with_nulls(self, mock_decrypt):
        import polars as pl

        mock_decrypt.return_value = [
            {"encrypted_string": "abc123", "decrypted_string": "123456"}
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        df = pl.DataFrame({"id": [1, 2, 3], "pin": ["abc123", None, "def456"]})

        result = client.decrypt_polars_dataframe(df, "pin")

        assert result["pin"][0] == "123456"
        assert result["pin"][1] is None

    @patch.object(PinappleClient, "decrypt_pins")
    def test_decrypt_polars_dataframe_batching(self, mock_decrypt):
        import polars as pl

        mock_decrypt.side_effect = [
            [{"encrypted_string": "abc123", "decrypted_string": "123456"}],
            [{"encrypted_string": "def456", "decrypted_string": "789012"}],
        ]

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        df = pl.DataFrame({"id": [1, 2], "pin": ["abc123", "def456"]})

        result = client.decrypt_polars_dataframe(df, "pin", batch_size=1)

        assert mock_decrypt.call_count == 2
        assert result["pin"][0] == "123456"
        assert result["pin"][1] == "789012"

    @patch.object(PinappleClient, "decrypt_pins")
    def test_decrypt_polars_dataframe_empty(self, mock_decrypt):
        import polars as pl

        client = PinappleClient(
            user="test_user", password="test_pass", api_url="http://localhost:8000"
        )

        df = pl.DataFrame({"id": [], "pin": []})
        result = client.decrypt_polars_dataframe(df, "pin")

        assert len(result) == 0
        mock_decrypt.assert_not_called()

    class TestEncryptPolarsDataframe:
        @patch.object(PinappleClient, "encrypt_pins")
        def test_encrypt_polars_dataframe_all_values(self, mock_encrypt):
            import polars as pl

            mock_encrypt.return_value = [
                {"pin": "123456", "encrypted_id": "abc123", "success": True},
                {"pin": "789012", "encrypted_id": "def456", "success": True},
            ]

            client = PinappleClient(
                user="test_user", password="test_pass", api_url="http://localhost:8000"
            )

            df = pl.DataFrame({"id": [1, 2], "pin": ["123456", "789012"]})

            result = client.encrypt_polars_dataframe(df, "pin")

            assert result["pin"][0] == "abc123"
            assert result["pin"][1] == "def456"

        @patch.object(PinappleClient, "encrypt_pins")
        def test_encrypt_polars_dataframe_with_nulls(self, mock_encrypt):
            import polars as pl

            mock_encrypt.return_value = [
                {"pin": "123456", "encrypted_id": "abc123", "success": True}
            ]

            client = PinappleClient(
                user="test_user", password="test_pass", api_url="http://localhost:8000"
            )

            df = pl.DataFrame({"id": [1, 2, 3], "pin": ["123456", None, "789012"]})

            result = client.encrypt_polars_dataframe(df, "pin")

            assert result["pin"][0] == "abc123"
            assert result["pin"][1] is None

        @patch.object(PinappleClient, "encrypt_pins")
        def test_encrypt_polars_dataframe_batching(self, mock_encrypt):
            import polars as pl

            mock_encrypt.side_effect = [
                [{"pin": "123456", "encrypted_id": "abc123", "success": True}],
                [{"pin": "789012", "encrypted_id": "def456", "success": True}],
            ]

            client = PinappleClient(
                user="test_user", password="test_pass", api_url="http://localhost:8000"
            )

            df = pl.DataFrame({"id": [1, 2], "pin": ["123456", "789012"]})

            result = client.encrypt_polars_dataframe(df, "pin", batch_size=1)

            assert mock_encrypt.call_count == 2
            assert result["pin"][0] == "abc123"
            assert result["pin"][1] == "def456"

        @patch.object(PinappleClient, "encrypt_pins")
        def test_encrypt_polars_dataframe_empty(self, mock_encrypt):
            import polars as pl

            client = PinappleClient(
                user="test_user", password="test_pass", api_url="http://localhost:8000"
            )

            df = pl.DataFrame({"id": [], "pin": []})
            result = client.encrypt_polars_dataframe(df, "pin")

            assert len(result) == 0
            mock_encrypt.assert_not_called()
