# 🍍 PinappleClient 🍍

A Python client for interacting with the Pinapple encryption API.

## 🚀 Features

- **Authentication** 🔐 - Token-based API authentication with automatic refresh
- **Flexible Encryption** ⚡ - Support for strict and loose encryption modes
- **Fallback Strategy** 🔄 - Automatic fallback from strict to loose encryption
- **Smart Token Management** ⏰ - Configurable token refresh with expiration handling

## 📦 Installation

```bash
pip install PinappleClient
```

## 🔧 Quick Start

```python
from pinapple_client import PinappleClient

# Initialize client with automatic token refresh
client = PinappleClient(
    user="your_username",
    password="your_password",
    api_url="https://api.pinapple.com",
    refresh_buffer_minutes=5  # Refresh token 5 minutes before expiration
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

## 🔒 Authentication & Token Management

The client automatically handles token management with intelligent refresh:

### Automatic Token Refresh
- Requests a bearer token on first API call
- Caches the token for subsequent requests
- **Automatically refreshes tokens before expiration** based on configurable buffer time
- Handles long-running operations without token expiry issues

### Token Configuration
```python
# Refresh token 10 minutes before it expires
client = PinappleClient(..., refresh_buffer_minutes=10)

# Check token status
expiration = client.get_token_expiration()
should_refresh = client.should_refresh_token()
```

### Token Utilities
- `get_token_expiration()` - Returns token expiration as datetime
- `should_refresh_token()` - Checks if token needs refresh based on buffer
- Automatic refresh during long DataFrame operations

**Perfect for long-running encryption jobs** - no manual token management required!

## 📄 License

This project is licensed under the GPL-3.0 License.

## 🔗 Links

- [Homepage](https://github.com/ebremst3dt/pinappleclient)
- [Issues](https://github.com/ebremst3dt/pinappleclient/issues)
- [Pypi](https://pypi.org/project/PinappleClient/)