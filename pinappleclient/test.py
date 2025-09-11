import pandas as pd
from client import PinappleClient
from roskarl import env_var


def test_pinapple_endpoints() -> None:
    print("=== Testing Pinapple API Endpoints with Token Management ===\n")

    # Initialize client with retry and backoff settings
    client = PinappleClient(
        user=env_var("PINAPPLE_USER"),
        password=env_var("PINAPPLE_PASSWORD"),
        api_url=env_var("PINAPPLE_URL"),
        refresh_token_after_x_minutes=2,
        timeout=30,
        max_retries=3,
        backoff_base=2,
    )

    test_pin: str = "20150331-9442"

    # Test 1: Token expiration info (with retry logic)
    try:
        print("Testing token retrieval with retry logic...")
        token = client.get_token()
        print(f"✓ Token obtained: {token[:20]}...")

        exp_time = client.get_token_expiration()
        if exp_time:
            print(f"✓ Token expires: {exp_time.isoformat()}Z")

        should_refresh = client.should_refresh_token()
        print(f"✓ Should refresh token: {should_refresh}")

    except Exception as e:
        print(f"✗ Token failed after retries: {e}")
        return

    # Test 2: Encryption methods (with connection retry)
    try:
        print("\nTesting encryption with retry logic...")
        encrypted_strict = client.encrypt_pin_strict(test_pin)
        print(f"✓ Strict encryption: {encrypted_strict}")
    except Exception as e:
        print(f"✗ Strict encryption failed after retries: {e}")
        encrypted_strict = None

    try:
        encrypted_loose = client.encrypt_pin_loose(test_pin)
        print(f"✓ Loose encryption: {encrypted_loose}")
    except Exception as e:
        print(f"✗ Loose encryption failed after retries: {e}")

    try:
        encrypted_hybrid = client.encrypt_pin_strict_then_loose(test_pin)
        print(f"✓ Strict-then-loose: {encrypted_hybrid}")
    except Exception as e:
        print(f"✗ Strict-then-loose failed after retries: {e}")

    # Test 3: Decryption (with retry)
    if encrypted_strict:
        try:
            decrypted = client.decrypt_pin({"encrypted_string": encrypted_strict})
            print(f"✓ Decryption result: {decrypted}")
            print(f"✓ Matches original: {decrypted == test_pin}")
        except Exception as e:
            print(f"✗ Decryption failed after retries: {e}")

    # Test 4: DataFrame encryption with retry capability
    try:
        test_df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "personnummer": ["20150331-9442", "20150331-9442", "20150331-9442",
                           "20150331-9442", "20150331-9442"],
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
        })

        print(f"\n--- DataFrame encryption (with retry logic) ---")
        print("Original DataFrame:")
        print(test_df)

        print(f"\nToken refresh status before encryption:")
        print(f"Should refresh: {client.should_refresh_token()}")

        encrypted_df = client.encrypt_dataframe(test_df.copy(), "personnummer")

        print(f"\nToken refresh status after encryption:")
        print(f"Should refresh: {client.should_refresh_token()}")

        print("\nEncrypted DataFrame:")
        print(encrypted_df)

    except Exception as e:
        print(f"✗ DataFrame encryption failed after retries: {e}")

    # Test 5: Test different retry configurations
    print(f"\n--- Testing different retry configurations ---")

    # Test with aggressive backoff
    aggressive_client = PinappleClient(
        user=env_var("PINAPPLE_USER"),
        password=env_var("PINAPPLE_PASSWORD"),
        api_url=env_var("PINAPPLE_URL"),
        refresh_token_after_x_minutes=2,
        timeout=45,
        max_retries=5,
        backoff_base=3,
    )

    try:
        print("Testing with aggressive retry settings (3s, 9s, 27s backoff)...")
        token = aggressive_client.get_token()
        print(f"✓ Aggressive retry client token: {token[:20]}...")
    except Exception as e:
        print(f"✗ Aggressive retry client failed: {e}")


if __name__ == "__main__":
    test_pinapple_endpoints()