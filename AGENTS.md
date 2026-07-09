# SecPass

A password manager

## Project Structure

- `secpass/crypto/` - AES-CBC, ChaCha20, Argon2id implementation (`cipher.py`)
- `secpass/secure/` - SecureString with mlock, zeroize (`secure_string.py`)
- `secpass/vault/` - Vault with entries/groups management (`vault.py`)
- `secpass/gui/` - PySide6 GUI (`main_window.py`)
- `secpass/debug.py` - Logging setup
- `tests/` - 94 passing tests

Package `__init__.py` files re-export public API (e.g. `from secpass.crypto import CipherSuite`).

## Python Tech Stack

- **GUI**: PySide6 (Qt binding)
- **Cryptography**: cryptography (AES-CBC, ChaCha20), argon2-cffi (Argon2)
- **Serialization**: JSON (Base64-encoded IV + ciphertext)
- **Secure strings**: Custom SecureString (zeroize on drop)
- **Memory protection**: mlock/VirtualLock for Windows/Linux/macOS

## Key Architecture Notes

### Vault Layout
- Vault is a folder containing: `entries/`, `groups/`, `masterkey`
- Filenames = SHA256(UUID) to prevent content leakage
- Entry split: **Head** (public: name, UUID, URL) + **Body** (secret: password, username)
- Internal vault name stored encrypted in masterkey file

### Important Implementation Details
1. **Entry body encrypted twice**: Inner (body fields) + outer (serialized body)
2. **Group-parent relationship**: Children know parent, parent doesn't know children (sync-safe)
3. **File format**: Base64-encoded IV + ciphertext stored as JSON
4. **Cross-platform**: SecureString supports Windows, Linux, macOS

## Cryptography

### Key Hierarchy

```
                    User Password (+ optional Key File)
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              Argon2id(id) ──> derived_key (32 bytes)
              (65MB, 3 iter, 4 lanes)    │
                                         │
              ┌──────────────────────────┤
              ▼                          ▼
        master_key (32b random)    entry/group data
              │                    (JSON encoded)
              │                          │
              └────── AES-256-CBC ───────┘
                    (with PKCS#7 padding)
```

### Vault Creation Flow

```
  Password + KeyFile                    os.urandom(16)
       │                                      │
       ▼                                      ▼
   Argon2id ──> derived_key               salt
       │
       ▼
  ┌──────────────────────────────────────────────┐
  │  AES-256-CBC encrypt                         │
  │  plaintext = json({"name":...}) | master_key │
  │  format    = Base64( IV(16) + ciphertext )   │
  └──────────────────────────────────────────────┘
       │
       ▼
  masterkey file:  salt(16) :: enc_data
```

### Vault Unlock Flow

```
  masterkey file
       │
       ├── salt ────┐
       │            │
       │  Password (+ KeyFile)
       │       │
       │       ▼
       │   Argon2id ──> derived_key
       │                   │
       ├── enc_data ───────┤
       │                   ▼
       │         AES-256-CBC decrypt
       │                   │
       │         ┌─────────┴─────────┐
       │         ▼                   ▼
       │   vault_data (JSON)    master_key (32b)
       │         │                   │
       │         ▼                   ▼
       │   vault._name       SecureString(bytearray)
       │                     (mlock → no swap)
       │                            │
       │              ┌─────────────┤
       │              ▼             ▼
       │        entry head    entry body
       │        encryption    double encryption
       │              │             │
       │              ▼             ▼
       │        entries/       entries/
       │        {hash}.head    {hash}.body
       │
       ▼
  Wrong password → decrypt garbage → invalid JSON → ValueError
```

### Entry Encryption (Double-Layer)

```
  HEAD (public)                    BODY (secret)
  ─────────────                    ─────────────

  { uuid, name, url, group }      { username, password, email, notes }
              │                              │
              ▼                              ▼
         JSON encode                    JSON encode
              │                              │
              ▼                              ▼
    ┌─────────────────┐           ┌─────────────────┐
    │  AES-256-CBC    │           │  AES-256-CBC    │
    │  with derived_key│           │  with derived_key│  ← inner layer
    └─────────────────┘           └─────────────────┘
              │                              │
              ▼                              ▼
    entries/{hash}.head           ┌─────────────────┐
                                  │  AES-256-CBC    │
                                  │  with derived_key│  ← outer layer
                                  └─────────────────┘
                                            │
                                            ▼
                                  entries/{hash}.body

  hash = SHA256(uuid)
```

### Group Encryption

```
  { uuid, name, parent }
           │
           ▼
      JSON encode
           │
           ▼
  ┌─────────────────┐
  │  AES-256-CBC    │
  │  with derived_key│
  └─────────────────┘
           │
           ▼
  groups/{hash}.group
```

### Memory Protection (SecureString)

```
  SecureString(data: bytes)
       │
       ├── _lock_memory():
       │     Windows: msvcrt.mlock → VirtualLock
       │     Linux/macOS: libc.mlock → mlock(2)
       │     (prevents pages being swapped to disk)
       │     Failure is silent — operation continues
       │
       └── zeroize():
             for each byte: data[i] = 0x00
             _unlock_memory() → munlock
             (called on Vault.lock(), __del__, context manager exit)
```

### On-Disk Format Summary

| File | Content |
|------|---------|
| `masterkey` | `salt(16) :: Base64(IV(16) + AES_CBC(name\|master_key))` |
| `entries/{sha256(uuid)}.head` | `Base64(IV(16) + AES_CBC(json_head))` |
| `entries/{sha256(uuid)}.body` | `Base64(IV(16) + AES_CBC( Base64(IV(16) + AES_CBC(json_body)) ))` |
| `groups/{sha256(uuid)}.group` | `Base64(IV(16) + AES_CBC(json_group))` |

### Cipher Suite (CipherSuite)

| Method | Algorithm | Key | IV/Nonce | Padding |
|--------|-----------|-----|----------|---------|
| `derive_key` | Argon2id | 32B | salt 16B | — |
| `encrypt_aes_cbc` | AES-256-CBC | 32B | 16B random | PKCS#7 |
| `decrypt_aes_cbc` | AES-256-CBC | 32B | from data | PKCS#7 |
| `encrypt_chacha20` | ChaCha20 | 32B | 16B random | — (stream) |
| `decrypt_chacha20` | ChaCha20 | 32B | from data | — (stream) |
| `generate_master_key` | os.urandom | — | — | — |
| `generate_salt` | os.urandom | — | — | — |

## Password Strength

5 threshold levels based on entropy:
- <28 bits: Very Weak (red)
- 28-50 bits: Weak (orange)
- 50-80 bits: Fair (yellow)
- 80-128 bits: Strong (light green)
- >128 bits: Very Strong (green)

Minimum 80 bits entropy required for vault/entry creation.

## Input Validation

Entry dialog validates:
- **Password**: Minimum 80 bits entropy
- **URL**: Must start with http://, https://, ftp://, or file://
- **Email**: Must match pattern user@example.com

## GUI Features
- Tabs for multiple vaults (+ button to open new)
- Login page with vault path, key file, password fields
- Entry list with search functionality
- Password generator with entropy calculation
- Entry editing: name, url, username, password, email, notes
- Group editing (double-click) and creation
- Menu: File (New Vault, Exit), Help (About)
- About dialog: Version 1.0.0, Developer: Vladislav Panov, Contact: support@secpass.app https://fr-space.ru
- Window title updates in real-time: `SecPass :: VaultName | groups: N | entries: M`

## Running Tests

```bash
.venv\scripts\activate
python -m pytest tests/ -v
```

## Dependencies

```
PySide6>=6.5.0
cryptography>=41.0.0
argon2-cffi>=23.1.0
pytest>=7.0.0
```
