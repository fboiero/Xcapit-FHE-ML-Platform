"""Info commands: version, info."""

import pickle
import sys
from pathlib import Path

from ..utils import get_version


def cmd_version(args) -> int:
    """Print version information."""
    print(f"Xcapit FHE-ML SDK v{get_version()}")
    print(f"Python: {sys.version.split()[0]}")

    # Check TenSEAL availability
    try:
        import tenseal

        print(f"TenSEAL: {tenseal.__version__}")
    except ImportError:
        print("TenSEAL: Not installed")

    return 0


def cmd_info(args) -> int:
    """Show information about encrypted data or model."""
    path = Path(args.path)

    if not path.exists():
        print(f"Error: File not found: {path}")
        return 1

    with open(path, "rb") as f:
        bundle = pickle.load(f)

    print(f"File: {path}")
    print(f"Size: {path.stat().st_size / 1024:.1f} KB")
    print(f"Version: {bundle.get('version', 'unknown')}")
    print()

    if "model_type" in bundle:
        print("Type: Trained Model")
        print(f"  Model: {bundle['model_type']}")

        config = bundle.get("config", {})
        if config:
            print("  Config:")
            for k, v in config.items():
                if v is not None:
                    print(f"    {k}: {v}")

        params = bundle.get("params", {})
        if params:
            print("  Parameters:")
            if params.get("weights") is not None:
                weights = params["weights"]
                print(f"    Weights: {len(weights)} features")
                if args.verbose:
                    print(
                        f"    Weight values: {weights[:5]}..."
                        if len(weights) > 5
                        else f"    Weight values: {weights}"
                    )
            if params.get("bias") is not None:
                print(f"    Bias: {params['bias']:.6f}")
            if params.get("state"):
                print(f"    State: {params['state']}")

        if bundle.get("feature_names"):
            print(f"  Features: {bundle['feature_names']}")

    elif "serialized_X" in bundle or "encrypted_dataset" in bundle:
        print("Type: Encrypted Dataset")
        print(f"  Samples: {bundle.get('n_samples', 'unknown')}")
        print(f"  Features: {bundle.get('n_features', 'unknown')}")

        if bundle.get("columns"):
            print(f"  Columns: {bundle['columns']}")
        if bundle.get("feature_names"):
            print(f"  Feature names: {bundle['feature_names']}")
        if bundle.get("target"):
            print(f"  Target: {bundle['target']}")
        if bundle.get("normalization_params"):
            print("  Normalized: Yes")
        if bundle.get("keys_path"):
            print(f"  Keys path: {bundle['keys_path']}")

    else:
        print("Type: Unknown")
        print(f"  Keys: {list(bundle.keys())}")

    return 0


__all__ = ["cmd_version", "cmd_info"]
