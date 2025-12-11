"""CLI command modules."""

from .api_keys import cmd_api_key_create, cmd_api_key_list, cmd_api_key_revoke
from .benchmark import cmd_benchmark
from .blockchain import (
    cmd_blockchain_checkpoint,
    cmd_blockchain_connect,
    cmd_blockchain_register,
    cmd_blockchain_verify,
)
from .encryption import cmd_decrypt, cmd_encrypt, cmd_init
from .info import cmd_info, cmd_version
from .prediction import cmd_predict
from .training import cmd_train

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
