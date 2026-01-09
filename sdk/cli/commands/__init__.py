"""CLI command modules."""

from .encryption import cmd_init, cmd_encrypt, cmd_decrypt
from .training import cmd_train
from .prediction import cmd_predict
from .blockchain import (
    cmd_blockchain_connect,
    cmd_blockchain_register,
    cmd_blockchain_checkpoint,
    cmd_blockchain_verify,
)
from .api_keys import cmd_api_key_create, cmd_api_key_list, cmd_api_key_revoke
from .benchmark import cmd_benchmark
from .info import cmd_version, cmd_info

__all__ = [
    # Encryption
    "cmd_init",
    "cmd_encrypt",
    "cmd_decrypt",
    # Training
    "cmd_train",
    # Prediction
    "cmd_predict",
    # Blockchain
    "cmd_blockchain_connect",
    "cmd_blockchain_register",
    "cmd_blockchain_checkpoint",
    "cmd_blockchain_verify",
    # API Keys
    "cmd_api_key_create",
    "cmd_api_key_list",
    "cmd_api_key_revoke",
    # Benchmark
    "cmd_benchmark",
    # Info
    "cmd_version",
    "cmd_info",
]
