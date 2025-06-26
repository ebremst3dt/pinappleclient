# 🍍 PinappleClient

A Python client for interacting with the Pinapple encryption API.

## 🚀 Features

- **Authentication** 🔐 - Token-based API authentication
- **Flexible Encryption** ⚡ - Support for strict and loose encryption modes
- **Fallback Strategy** 🔄 - Automatic fallback from strict to loose encryption

## 📦 Installation

```bash
pip install PinappleClient
```

## 🔧 Quick Start

```python
from pinapple_client import PinappleClient

# Initialize client
client = PinappleClient(
    user="your_username",
    password="your_password",
    api_url="https://api.pinapple.com"
)

# Encrypt a single PIN
encrypted_pin = client.encrypt_pin_strict("123456")
print(f"Encrypted: {encrypted_pin}")

# Decrypt data
decrypted_pin = client.decrypt_pin(encrypted_data)
print(f"Decrypted: {decrypted_pin}")
```

### 📊 DataFrame Operations

#### `encrypt_dataframe(df, column, strict=True, strict_then_loose=False) -> DataFrame`
Encrypts an entire column in a pandas DataFrame.

```python
import pandas as pd

df = pd.DataFrame({
    'id': [1, 2, 3],
    'pin': ['123456', '789012', '345678']
})

# Encrypt the 'pin' column
encrypted_df = client.encrypt_dataframe(df, 'pin', strict=True)

# Use fallback strategy
encrypted_df = client.encrypt_dataframe(df, 'pin', strict_then_loose=True)
```

**Parameters:**
- `df`: Input DataFrame
- `column`: Column name to encrypt
- `strict`: Use strict encryption (default: True)
- `strict_then_loose`: Enable fallback strategy (default: False)

## 🔒 Authentication

The client automatically handles token management:

1. Requests a bearer token on first API call
2. Caches the token for subsequent requests
3. Automatically includes authentication headers


## 📄 License

This project is licensed under the GPL-3.0 License.

## 🔗 Links

- [Homepage](https://github.com/ebremst3dt/pinappleclient)
- [Issues](https://github.com/ebremst3dt/pinappleclient/issues)
- [Pypi](https://pypi.org/project/PinappleClient/)