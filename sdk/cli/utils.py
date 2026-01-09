"""Utility functions for CLI commands."""

import sys


def get_version() -> str:
    """Get SDK version."""
    try:
        from .. import __version__
        return __version__
    except ImportError:
        return "0.1.0"


def print_error(message: str) -> None:
    """Print error message to stderr."""
    print(f"Error: {message}", file=sys.stderr)


def print_success(message: str) -> None:
    """Print success message."""
    print(f"  {message}")


def print_warning(message: str) -> None:
    """Print warning message."""
    print(f"Warning: {message}")


__all__ = ["get_version", "print_error", "print_success", "print_warning"]
