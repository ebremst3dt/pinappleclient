from client_v2 import PinappleClient

pins_to_process = ["19920622-2359", "987654321", "19920682-2354", "!@#$%^&*()"]

with PinappleClient(
    user="blorgh123", password="wee123", api_url="http://localhost:8000"
) as client:
    encrypted_result = client.encrypt_pin(pins=pins_to_process)
    print(f"Encrypted: {encrypted_result}")

    encrypted_strings = [r["encrypted_id"] for r in encrypted_result]
    print(f"Encrypted strings: {encrypted_strings}")

    decrypted_result = client.decrypt_pin(encrypted_strings=encrypted_strings)
    print(f"Decrypted: {decrypted_result}")

    validate_result = client.validate_pin(pins=encrypted_strings)
    for result in validate_result:
        print(result)
