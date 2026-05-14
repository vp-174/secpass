# PWDuck 🦆

A password manager built in Python with PySide6.

## Project Structure



## Python Tech Stack

- **GUI**: PySide6 (Qt binding)
- **Cryptography**: cryptography (AES-CBC, ChaCha20), argon2-cffi (Argon2)
- **Serialization**: RON-like format (use JSON or custom binary)
- **Secure strings**: Use custom secure string implementation (zeroize on drop)
- **Memory protection**: mlock/VirtualLock for sensitive data

## Key Architecture Notes

### Vault Layout (from reference)
- Vault is a folder containing: `entries/`, `groups/`, `masterkey`
- Filenames = SHA256(UUID) to prevent content leakage
- Entry split: **Head** (public: name, UUID, URL) + **Body** (secret: password, username)
- Loading vault loads heads only; body decrypted on demand

### Cryptography (from reference)
- **Master key**: 32 bytes random, encrypted with AES-CBC
- **Key derivation**: Argon2id from user password (+ optional key file)
- **Memory protection**: ChaCha20-encrypt master key with 1MB locked memory region
- **Data encryption**: AES-CBC for entries/groups, double-encrypt for body content

### Important Implementation Details
1. **Entry body encrypted twice**: Inner (body fields) + outer (serialized body)
2. **Group-parent relationship**: Children know parent, parent doesn't know children (sync-safe)
3. **File format**: Base64-encoded IV + ciphertext stored as RON

