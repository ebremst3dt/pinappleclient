# 🍍 PinappleClient 🍍

Python client for the Pinapple encryption API with automatic token management and robust error handling.

## Installation
```bash
pip install PinappleClient
```

## Quick Start
```python
from pinapple_client import PinappleClient

client = PinappleClient(
    user="username",
    password="password",
    api_url="https://api.pinapple.com"
)

# Encrypt/decrypt individual PINs
encrypted = client.encrypt_pins(["123456", "789012"])
decrypted = client.decrypt_pins(["enc_abc123", "enc_def456"])

# Validate PINs
validation = client.validate_pins(["123456", "789012"])
```

## DataFrame Operations

### Pandas
```python
import pandas as pd

df = pd.DataFrame({
    'id': [1, 2, 3],
    'pin': ['123456', '789012', '345678']
})

# Encrypt
encrypted_df = client.encrypt_pandas_dataframe(df, 'pin', batch_size=100)

# Decrypt
decrypted_df = client.decrypt_pandas_dataframe(encrypted_df, 'pin', batch_size=100)
```

### Polars
```python
import polars as pl

df = pl.DataFrame({
    'id': [1, 2, 3],
    'pin': ['123456', '789012', '345678']
})

# Encrypt
encrypted_df = client.encrypt_polars_dataframe(df, 'pin', batch_size=100)

# Decrypt
decrypted_df = client.decrypt_polars_dataframe(encrypted_df, 'pin', batch_size=100)
```

## Configuration
```python
client = PinappleClient(
    user="username",
    password="password",
    api_url="https://api.pinapple.com",
    refresh_token_after_x_minutes=5,  # Token refresh buffer (default: 5)
    timeout=30,                        # Request timeout (default: 30)
    max_retries=3,                     # Retry attempts (default: 3)
    backoff_base=2.0                   # Exponential backoff (default: 2.0)
)
```

### Token Management

- Automatic token refresh before expiration
- Thread-safe token operations
- JWT payload parsing for expiration tracking

### Network Resilience

- Exponential backoff retry: `backoff_base ^ (attempt + 1)`
- Handles 503 database errors
- Connection/timeout error recovery

## License

GPL-3.0

## Links

- [GitHub](https://github.com/ebremst3dt/pinappleclient)
- [PyPI](https://pypi.org/project/PinappleClient/)