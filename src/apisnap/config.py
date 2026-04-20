"""Configuration management for apisnap."""

import os
import toml
from pathlib import Path
from typing import Optional


CONFIG_DIR = Path.home() / ".apisnap"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def ensure_config_dir() -> None:
    """Ensure config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return _default_config()
    try:
        return toml.load(CONFIG_FILE)
    except Exception:
        return _default_config()


def _default_config() -> dict:
    """Get default configuration."""
    return {
        "cerebras": {
            "api_key": "",
            "model": "qwen-3-235b-a22b-instruct-2507",
        },
        "defaults": {
            "output_dir": "./tests",
            "format": "pytest",
        },
    }


def save_config(config: dict) -> None:
    """Save configuration to file."""
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        toml.dump(config, f)


def get_api_key() -> str:
    """Get Cerebras API key."""
    config = load_config()
    return config.get("cerebras", {}).get("api_key", "")


def set_api_key(key: str) -> None:
    """Set Cerebras API key."""
    config = load_config()
    if "cerebras" not in config:
        config["cerebras"] = {}
    config["cerebras"]["api_key"] = key
    save_config(config)


def get_model() -> str:
    """Get Cerebras model name."""
    config = load_config()
    return config.get("cerebras", {}).get("model", "qwen-3-235b-a22b-instruct-2507")


def set_model(model: str) -> None:
    """Set Cerebras model name."""
    config = load_config()
    if "cerebras" not in config:
        config["cerebras"] = {}
    config["cerebras"]["model"] = model
    save_config(config)


def get_default_format() -> str:
    """Get default test format."""
    config = load_config()
    return config.get("defaults", {}).get("format", "pytest")


def set_default_format(format: str) -> None:
    """Set default test format."""
    config = load_config()
    if "defaults" not in config:
        config["defaults"] = {}
    config["defaults"]["format"] = format
    save_config(config)


def get_default_output_dir() -> str:
    """Get default output directory."""
    config = load_config()
    return config.get("defaults", {}).get("output_dir", "./tests")


def set_default_output_dir(output_dir: str) -> None:
    """Set default output directory."""
    config = load_config()
    if "defaults" not in config:
        config["defaults"] = {}
    config["defaults"]["output_dir"] = output_dir
    save_config(config)


def show_config() -> str:
    """Get configuration as string with masked API key."""
    config = load_config()
    api_key = config.get("cerebras", {}).get("api_key", "")
    masked_key = _mask_api_key(api_key)

    lines = [
        "[cerebras]",
        f'api_key = "{masked_key}"',
        f'model = "{config.get("cerebras", {}).get("model", "qwen-3-235b-a22b-instruct-2507")}"',
        "",
        "[defaults]",
        f'output_dir = "{config.get("defaults", {}).get("output_dir", "./tests")}"',
        f'format = "{config.get("defaults", {}).get("format", "pytest")}"',
    ]
    return "\n".join(lines)


def _mask_api_key(key: str) -> str:
    """Mask API key for display."""
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


def config_exists() -> bool:
    """Check if config file exists."""
    return CONFIG_FILE.exists()
