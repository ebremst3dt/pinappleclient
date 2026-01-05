from pinappleclient.client import PinappleClient
import pandas as pd
import polars as pl

pins_to_process = ["19920622-2359", "987654321", "19920682-2356", "!@#$%^&*()"]

with PinappleClient(
    user="blorgh123", password="wee123", api_url="http://localhost:8000"
) as client:
    print("=" * 80)
    print("TESTING ENCRYPT_PINS")
    print("=" * 80)
    encrypted_result = client.encrypt_pins(pins=pins_to_process)
    print(f"Encrypted result: {encrypted_result}")
    print()

    encrypted_strings = [r["encrypted_id"] for r in encrypted_result]
    print(f"Extracted encrypted strings: {encrypted_strings}")
    print()

    print("=" * 80)
    print("TESTING DECRYPT_PINS")
    print("=" * 80)
    decrypted_result = client.decrypt_pins(encrypted_strings=encrypted_strings)
    print(f"Decrypted result: {decrypted_result}")
    print()

    print("=" * 80)
    print("TESTING VALIDATE_PINS")
    print("=" * 80)
    validate_result = client.validate_pins(pins=encrypted_strings)
    for result in validate_result:
        print(f"Validation result: {result}")
    print()

    print("=" * 80)
    print("TESTING PANDAS DATAFRAME ENCRYPTION")
    print("=" * 80)
    df_pandas = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "pin": ["19920622-2359", "987654321", None, "19920682-2356", "!@#$%^&*()"],
            "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        }
    )
    print("BEFORE encryption:")
    print(df_pandas)
    print()

    encrypted_df_pandas = client.encrypt_pandas_dataframe(
        df_pandas.copy(), "pin", batch_size=2
    )
    print("AFTER encryption:")
    print(encrypted_df_pandas)
    print()

    print("=" * 80)
    print("TESTING PANDAS DATAFRAME DECRYPTION")
    print("=" * 80)
    print("BEFORE decryption:")
    print(encrypted_df_pandas)
    print()

    decrypted_df_pandas = client.decrypt_pandas_dataframe(
        encrypted_df_pandas.copy(), "pin", batch_size=2
    )
    print("AFTER decryption:")
    print(decrypted_df_pandas)
    print()

    print("=" * 80)
    print("TESTING POLARS DATAFRAME ENCRYPTION")
    print("=" * 80)
    df_polars = pl.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "pin": ["19920622-2359", "987654321", None, "19920682-2356", "!@#$%^&*()"],
            "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        }
    )
    print("BEFORE encryption:")
    print(df_polars)
    print()

    encrypted_df_polars = client.encrypt_polars_dataframe(
        df_polars.clone(), "pin", batch_size=2
    )
    print("AFTER encryption:")
    print(encrypted_df_polars)
    print()

    print("=" * 80)
    print("TESTING POLARS DATAFRAME DECRYPTION")
    print("=" * 80)
    print("BEFORE decryption:")
    print(encrypted_df_polars)
    print()

    decrypted_df_polars = client.decrypt_polars_dataframe(
        encrypted_df_polars.clone(), "pin", batch_size=2
    )
    print("AFTER decryption:")
    print(decrypted_df_polars)
