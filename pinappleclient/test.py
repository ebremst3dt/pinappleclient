import pandas as pd
from client import PinappleClient
from roskarl import env_var


def test_pinapple_endpoints() -> None:
    # Initialize client
    client = PinappleClient(
        user=env_var("PINAPPLE_USER"),
        password=env_var("PINAPPLE_PASSWORD"),
        api_url=env_var("PINAPPLE_URL"),
    )

    test_pin: str = "20150331-9442"

    print("=== Testing Pinapple API Endpoints ===\n")

    # Test 1: Get token
    try:
        token = client.get_token()
        print(f"✓ Token obtained: {token[:20]}...")
    except Exception as e:
        print(f"✗ Token failed: {e}")
        return

    # Test 2: Strict encryption
    try:
        encrypted_strict = client.encrypt_pin_strict(test_pin)
        print(f"✓ Strict encryption: {encrypted_strict}")
    except Exception as e:
        print(f"✗ Strict encryption failed: {e}")
        encrypted_strict = None

    # Test 3: Loose encryption
    try:
        encrypted_loose = client.encrypt_pin_loose(test_pin)
        print(f"✓ Loose encryption: {encrypted_loose}")
    except Exception as e:
        print(f"✗ Loose encryption failed: {e}")
        encrypted_loose = None

    # Test 4: Strict then loose
    try:
        encrypted_hybrid = client.encrypt_pin_strict_then_loose(test_pin)
        print(f"✓ Strict-then-loose: {encrypted_hybrid}")
    except Exception as e:
        print(f"✗ Strict-then-loose failed: {e}")
        encrypted_hybrid = None

    # Test 5: Decryption (if we have encrypted data)
    if encrypted_strict:
        try:
            # Need to determine the correct format for encrypted_data
            decrypted = client.decrypt_pin({"encrypted_string": encrypted_strict})
            print(f"✓ Decryption result: {decrypted}")
            print(f"✓ Matches original: {decrypted == test_pin}")
        except Exception as e:
            print(f"✗ Decryption failed: {e}")

    # Test 6: DataFrame encryption - strict
    try:
        test_df = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "personnummer": ["20150331-9442", "20150331-9442", "20150331-9442"],
                "name": ["Alice", "Bob", "Charlie"],
            }
        )

        print(f"\n--- DataFrame encryption (strict) ---")
        print("Original DataFrame:")
        print(test_df)

        encrypted_df_strict = client.encrypt_dataframe(
            test_df.copy(), "personnummer", strict=True
        )
        print("\nEncrypted DataFrame (strict):")
        print(encrypted_df_strict)

    except Exception as e:
        print(f"✗ DataFrame strict encryption failed: {e}")


if __name__ == "__main__":
    test_pinapple_endpoints()
