# envault

> CLI tool to encrypt and version-control `.env` files safely alongside your codebase.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/):

```bash
pipx install envault
```

---

## Usage

**Encrypt your `.env` file before committing:**

```bash
envault lock --file .env --output .env.vault
```

**Decrypt on another machine or in CI:**

```bash
envault unlock --file .env.vault --output .env
```

**Rotate your encryption key:**

```bash
envault rotate --file .env.vault --new-key $NEW_SECRET_KEY
```

Add `.env` to your `.gitignore` and commit `.env.vault` safely to your repository. Store your secret key in a password manager or CI secrets — never in the repo.

```gitignore
# .gitignore
.env
```

---

## How It Works

`envault` uses AES-256-GCM encryption to protect your environment variables. Each vault file is self-contained and includes a versioned header, making it easy to track changes over time with standard Git tooling.

---

## Requirements

- Python 3.8+
- `cryptography` >= 41.0

---

## License

MIT © 2024 — see [LICENSE](LICENSE) for details.