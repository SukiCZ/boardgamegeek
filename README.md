# BGG-API

### A Python API for [boardgamegeek.com](https://boardgamegeek.com/)


[![docs status](https://readthedocs.org/projects/bgg-api/badge/?version=latest)](https://bgg-api.readthedocs.io/en/latest/)
[![ci workflow status](https://github.com/SukiCZ/boardgamegeek/actions/workflows/ci.yml/badge.svg)](https://github.com/SukiCZ/boardgamegeek/actions)
[![codecov](https://codecov.io/gh/SukiCZ/boardgamegeek/graph/badge.svg?token=LMOWZ62OIS)](https://codecov.io/gh/SukiCZ/boardgamegeek)
[![Black code style](https://img.shields.io/badge/code_style-black-000000.svg)](https://github.com/ambv/black)
![Contributions welcome](https://img.shields.io/badge/contributions-welcome-green.svg)

## Installation

```bash
pip install bgg-api
```

## Usage

### Basic Usage

```python
from boardgamegeek import BGGClient

bgg = BGGClient()

game = bgg.game("Monopoly")

print(game.year)  # 1935
print(game.rating_average)  # 4.36166
```

### BGG Access Token Authentication

BoardGameGeek now requires users to register and obtain access tokens for API usage. You can provide your BGG access token when creating the client:

```python
from boardgamegeek import BGGClient

# With access token for authentication
bgg = BGGClient(access_token='your_bgg_access_token')

game = bgg.game("Monopoly")
```

The access token is passed as an `Authorization: Bearer <token>` header with all API requests.

### Legacy API with Access Token

The legacy API client also supports access tokens:

```python
from boardgamegeek import BGGClientLegacy

bgg = BGGClientLegacy(access_token='your_bgg_access_token')
```

### Backward Compatibility

The library maintains full backward compatibility. Existing code will continue to work without access tokens, though BGG may require tokens for API access in the future.

## Development

```bash
# Install dependencies
pip install -r requirements/develop.txt
# Install pre-commit hooks
pre-commit install

# Run tests
pytest .
# Run tests with tox
tox
```

## Publishing

```bash
# Bump version (patch, minor, major)
bump2version patch
# Push to github
git push --tags origin master
```
