# Contributing to CrawlKit

Thank you for your interest in contributing to CrawlKit! 🦐

## 🚀 Getting Started

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/crawlkit-oss.git
cd crawlkit-oss
```

### 2. Install Dependencies

```bash
pip install -e ".[dev]"
playwright install chromium
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

## 🧪 Testing

Before submitting a PR, make sure all tests pass:

```bash
pytest
```

Add tests for new features in the `tests/` directory.

## 📝 Code Style

We use:
- **Black** for code formatting
- **Ruff** for linting

Run before committing:

```bash
black crawlkit/
ruff check crawlkit/
```

## 🐛 Reporting Bugs

Found a bug? Please open an issue with:

1. **Description** — What happened?
2. **Expected Behavior** — What should happen?
3. **Steps to Reproduce** — How can we reproduce it?
4. **Environment** — Python version, OS, etc.
5. **Code Sample** — Minimal example to reproduce

## ✨ Feature Requests

Have an idea? Open an issue with:

1. **Use Case** — What problem does it solve?
2. **Proposed Solution** — How should it work?
3. **Alternatives** — What alternatives have you considered?

## 🔧 Adding a New Parser

To add support for a new website:

1. Create a new file in `crawlkit/parsers/` (e.g., `example.py`)
2. Extend `BaseParser` from `crawlkit.parsers.base`
3. Implement `parse()` and optionally `discover()`
4. Register the parser in `crawler.py` → `_load_parsers()`

Example:

```python
from crawlkit.parsers.base import BaseParser

class ExampleParser(BaseParser):
    domain = "example.com"
    
    def parse(self, html: str, url: str, text: str) -> dict:
        # Your parsing logic here
        return {
            "title": "...",
            "content": "...",
            "metadata": {...}
        }
```

## 📦 Pull Request Guidelines

1. **One PR = One Feature** — Keep PRs focused
2. **Write Tests** — Cover new code with tests
3. **Update Docs** — Add usage examples to README if applicable
4. **Commit Messages** — Use clear, descriptive messages
5. **Sign Your Commits** — We require signed commits (GPG)

### Commit Message Format

```
type: short description

Longer explanation if needed.

Closes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## 🔒 Security

Found a security issue? **DO NOT** open a public issue.

Email us privately at: **security@crawlkit.ai**

## 📜 License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.

## 🙏 Thank You!

Every contribution helps make CrawlKit better for everyone. We appreciate your time and effort! ❤️
