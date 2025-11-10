"""Configuration helpers for managing lcmeval runtime settings."""

import os
import pathlib
import yaml
from typing import TypedDict, Dict, Any
from .helper import timestamp


class Config(TypedDict):
    runs_dir: str     # Directory for storing runs
    timeout: int      # Timeout for LLM API calls
    max_retries: int  # Maximum number of retries for API calls
    max_tokens: int   # Maximum number of completion tokens
    env_file: str     # Path to the .env file


CONFIG: Config = {
    "runs_dir": "runs",
    "timeout": 120,
    "max_retries": 0,
    "max_tokens": 4096,
    "env_file": ".env",
}


def update_config(config: Config, kwargs: Dict[str, Any]):
    for key, value in kwargs.items():
        if key in config and value is not None:
            config[key] = value
    config["runs_dir"] = pathlib.Path(config["runs_dir"]).expanduser().resolve().as_posix()
    config["env_file"] = pathlib.Path(config["env_file"]).expanduser().resolve().as_posix()


def dump_config(config: Config):
    if not os.path.exists(config["runs_dir"]):
        os.makedirs(config["runs_dir"])
    if os.path.exists(f'{config["runs_dir"]}/config.yaml'):
        os.rename(f'{config["runs_dir"]}/config.yaml', f'{config["runs_dir"]}/config.bak.{timestamp()}.yaml')
    with open(f'{config["runs_dir"]}/config.yaml', 'w') as f:
        yaml.dump(config, f, sort_keys=False)
