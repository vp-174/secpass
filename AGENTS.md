# SecPass

A password manager built in Python with PySide6.

## Project Structure

- `secpass/crypto/` - AES-CBC, ChaCha20, Argon2id implementation
- `secpass/secure/` - SecureString with mlock, zeroize
- `secpass/vault/` - Vault with entries/groups management
- `secpass/gui/` - PySide6 GUI (MainWindow, dialogs)
- `tests/` - 27+ passing tests

## Python Tech Stack

- **GUI**: PySide6 (Qt binding)
- **Cryptography**: cryptography (AES-CBC, ChaCha20), argon2-cffi (Argon2)
- **Serialization**: JSON (Base64-encoded IV + ciphertext)
- **Secure strings**: Custom SecureString (zeroize on drop)
- **Memory protection**: mlock/VirtualLock for sensitive data

## Key Architecture Notes

### Vault Layout
- Vault is a folder containing: `entries/`, `groups/`, `masterkey`
- Filenames = SHA256(UUID) to prevent content leakage
- Entry split: **Head** (public: name, UUID, URL) + **Body** (secret: password, username)
- Internal vault name stored encrypted in masterkey file

### Cryptography
- **Master key**: 32 bytes random, encrypted with AES-CBC
- **Key derivation**: Argon2id from user password (+ optional key file)
- **Memory protection**: ChaCha20-encrypt master key with 1MB locked memory region
- **Data encryption**: AES-CBC for entries/groups, double-encrypt for body content

### Important Implementation Details
1. **Entry body encrypted twice**: Inner (body fields) + outer (serialized body)
2. **Group-parent relationship**: Children know parent, parent doesn't know children (sync-safe)
3. **File format**: Base64-encoded IV + ciphertext stored as JSON

## Password Strength
5 threshold levels based on entropy:
- <28 bits: Very Weak (red)
- 28-50 bits: Weak (orange)
- 50-80 bits: Fair (yellow)
- 80-128 bits: Strong (light green)
- >128 bits: Very Strong (green)

Minimum 80 bits entropy required for vault/entry creation.

## GUI Features
- Tabs for multiple vaults (+ button to open new)
- Login page with vault path, key file, password fields
- Entry list with search functionality
- Password generator with entropy calculation
- Entry editing: name, url, username, password, email, notes
- Group editing (double-click) and creation
- Menu: File (New Vault, Open Vault, Lock, Exit), Help (About)
- About dialog: Version 1.0.0, Developer: SecPass Team, Contact: support@secpass.app