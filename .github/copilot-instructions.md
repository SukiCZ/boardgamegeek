# BGG-API Repository Instructions

BGG-API is a Python library that provides an interface to the BoardGameGeek.com API. It supports Python 3.8+ and includes both a programmatic API and a command-line interface.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Environment Setup
- Install development dependencies:
  ```bash
  pip install -r requirements/develop.txt
  ```
  **NOTE**: Installation may timeout in restricted network environments. If pip install fails due to network timeouts, use the existing installed dependencies and work with `PYTHONPATH=.` approach.

- Set up pre-commit hooks (optional but recommended):
  ```bash
  pre-commit install
  ```

### Building and Testing
- Run unit tests (excludes integration tests that require network access):
  ```bash
  PYTHONPATH=. pytest -m "not integration"
  ```
  **TIMING**: Takes approximately 1 second. NEVER CANCEL - set timeout to 2+ minutes to be safe.

- Run all tests including integration tests (requires network access):
  ```bash
  PYTHONPATH=. pytest
  ```
  **TIMING**: Integration tests take 6-7 seconds but will fail in network-restricted environments. NEVER CANCEL - set timeout to 5+ minutes.

- Run tests with coverage:
  ```bash
  PYTHONPATH=. pytest --cov=boardgamegeek --cov-report=xml
  ```

- Run multi-version testing with tox:
  ```bash
  tox
  ```
  **TIMING**: Takes 15+ minutes when dependencies can be installed. NEVER CANCEL - set timeout to 30+ minutes. May fail in network-restricted environments due to dependency installation timeouts.

### Documentation
- Build documentation:
  ```bash
  make html
  ```
  **TIMING**: Takes approximately 3 seconds. NEVER CANCEL - set timeout to 5+ minutes.

- View documentation:
  The built docs are in `build/html/index.html`

### Linting and Code Quality
- Run pre-commit hooks manually:
  ```bash
  pre-commit run --all-files
  ```
  **TIMING**: Takes 1-2 minutes. NEVER CANCEL - set timeout to 5+ minutes.

- Check individual tools (if installed):
  ```bash
  python -m flake8 boardgamegeek tests --count --statistics
  python -m black boardgamegeek tests --check
  ```

### Package Installation
**NOTE**: Standard `pip install -e .` may fail due to permission restrictions. Use the PYTHONPATH approach instead:
```bash
export PYTHONPATH=.
# Then run your commands with PYTHONPATH set
```

## Validation

### Manual Testing Scenarios
Always validate your changes with these scenarios:

1. **Basic API functionality test**:
   ```bash
   PYTHONPATH=. python -c "from boardgamegeek import BGGClient; print('Import successful')"
   ```
   Should print "Import successful" without errors.

2. **Core API classes test**:
   ```bash
   PYTHONPATH=. python -c "
   from boardgamegeek import BGGClient, BGGClientLegacy
   from boardgamegeek.cache import CacheBackendNone
   bgg = BGGClient(cache=CacheBackendNone())
   print('BGGClient created successfully')
   "
   ```
   Should create client without errors.

3. **CLI functionality test**:
   ```bash
   PYTHONPATH=. python -m boardgamegeek.main --help
   ```
   Should display help text without errors.

4. **Unit test validation**:
   ```bash
   PYTHONPATH=. pytest tests/test_utils.py::test_get_xml_subelement_attr -v
   ```
   Should pass quickly (< 1 second).

5. **Documentation build validation**:
   ```bash
   make html
   ```
   Should complete with only warnings (not errors) and produce `build/html/index.html`.

### Key Test Commands
- **Quick validation**: `PYTHONPATH=. pytest tests/test_utils.py -v` (takes ~0.1s)
- **Core functionality**: `PYTHONPATH=. pytest tests/test_game.py -v` (takes ~0.2s)
- **Full unit test suite**: `PYTHONPATH=. pytest -m "not integration"` (takes ~0.75s, 45 tests)

### CI Validation
Always run these commands before submitting changes:
```bash
# 1. Run unit tests (NEVER CANCEL - timeout: 5 minutes)
PYTHONPATH=. pytest -m "not integration"

# 2. Build documentation (NEVER CANCEL - timeout: 5 minutes) 
make html

# 3. Check core imports work
PYTHONPATH=. python -c "from boardgamegeek import BGGClient; from boardgamegeek.cache import CacheBackendNone; bgg = BGGClient(cache=CacheBackendNone()); print('Validation complete')"
```

## Common Tasks and File Locations

### Repository Structure
```
.
├── README.md                  # Project overview and basic usage
├── boardgamegeek/            # Main package source code
│   ├── __init__.py           # Package initialization and exports
│   ├── api.py               # Main BGGClient implementation
│   ├── legacy_api.py        # Legacy BGGClientLegacy
│   ├── main.py              # CLI entry point
│   ├── utils.py             # Utilities and rate limiting
│   ├── exceptions.py        # Custom exceptions
│   ├── cache.py             # Caching backends
│   └── objects/             # Data model objects
├── tests/                    # Test suite
│   ├── conftest.py          # Pytest configuration and fixtures
│   └── test_*.py            # Individual test modules
├── docs/                     # Sphinx documentation
├── requirements/             # Dependencies
│   ├── base.txt             # Runtime dependencies
│   └── develop.txt          # Development dependencies
├── setup.py                  # Package setup (legacy)
├── pyproject.toml           # Modern package configuration
├── tox.ini                  # Multi-version testing config
├── .pre-commit-config.yaml  # Pre-commit hooks config
└── Makefile                 # Documentation build commands
```

### Key Configuration Files
- **setup.py**: Legacy package setup with version 1.1.12
- **pyproject.toml**: Modern package configuration with build system
- **pytest.ini**: Test configuration, excludes integration tests by default
- **setup.cfg**: flake8 configuration (max-line-length=120)
- **tox.ini**: Multi-version testing for Python 3.8-3.13
- **.pre-commit-config.yaml**: Code quality tools (black, flake8, pyupgrade)

### Important Code Areas
- **API Client**: `boardgamegeek/api.py` - Main BGGClient class
- **CLI**: `boardgamegeek/main.py` - Command-line interface implementation
- **Rate Limiting**: `boardgamegeek/utils.py` - RateLimitingAdapter for API throttling
- **Data Models**: `boardgamegeek/objects/` - Game, User, Collection objects
- **Test Fixtures**: `tests/conftest.py` - BGGClient fixtures and XML test data

### Development Notes
- **Network Dependencies**: Integration tests require access to boardgamegeek.com API
- **API Rate Limiting**: Built-in rate limiting (20 requests/minute default)
- **Caching**: Supports multiple backends (memory, SQLite, none)
- **Python Versions**: Supports 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- **Dependencies**: Minimal runtime deps (requests, requests-cache)

### Troubleshooting
- **Import Errors**: Use `PYTHONPATH=.` if package installation fails
- **Network Timeouts**: Skip integration tests with `-m "not integration"`
- **Permission Issues**: Use `--user` flag for pip installs if needed
- **Dependency Issues**: Focus on unit tests if dev dependencies can't be installed

### Example Usage
```python
from boardgamegeek import BGGClient
from boardgamegeek.cache import CacheBackendNone

# Create client (with rate limiting, without cache for testing)
bgg = BGGClient(cache=CacheBackendNone(), timeout=10, retries=3)

# In real usage (with network access):
# game = bgg.game("Monopoly")
# print(f"{game.name} ({game.year}) - Rating: {game.rating_average}")

# CLI usage examples:
# PYTHONPATH=. python -m boardgamegeek.main --help
# PYTHONPATH=. python -m boardgamegeek.main --game "Catan"
# PYTHONPATH=. python -m boardgamegeek.main --user "someuser"
```

## Critical Reminders
- **NEVER CANCEL** long-running builds or tests - they may take several minutes
- Use `PYTHONPATH=.` approach if package installation fails
- Integration tests will fail without network access (this is expected)
- Set generous timeouts: 5+ minutes for tests, 5+ minutes for docs, 30+ minutes for tox
- Always validate changes with the core scenarios listed above
