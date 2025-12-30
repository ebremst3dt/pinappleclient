from client_v2 import PinappleClient

pins_to_process = ["123456789", "987654321", "555555555"]

with PinappleClient(
    user="your_username",
    password="your_password",
    api_url="localhost"
) as client:
    encrypted_result = client.encrypt_pin(pins=pins_to_process)
    print(f"Encrypted: {encrypted_result}")

    decrypted_result = client.decrypt_pin(
        encrypted_data={"encrypted_string": encrypted_result}
    )
    print(f"Decrypted: {decrypted_result}")