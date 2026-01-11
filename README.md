# TerryAnn CLI

Command line interface for the TerryAnn Medicare Journey Intelligence Platform.

## Installation

```bash
pip install -e .
```

## Configuration

Set the gateway URL via environment variable:

```bash
export TERRYANN_GATEWAY_URL=https://terryann-core-production.up.railway.app
```

Or create a config file at `~/.terryann/config.toml`:

```toml
[gateway]
url = "https://terryann-core-production.up.railway.app"
```

## Usage

### Check gateway status

```bash
terryann status
```

### Start interactive chat

```bash
terryann chat
```

## Development

```bash
pip install -e ".[dev]"
pytest
```
