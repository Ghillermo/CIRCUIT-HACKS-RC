"""Location of the dsptool binary: $DSPTOOL, else <repo>/ext/bin/dsptool[.exe] (tools/setup_local.sh), else the cloud path."""
import os
from pathlib import Path

_bin = Path(__file__).resolve().parents[1] / "ext/bin"
_local = _bin / "dsptool.exe" if (_bin / "dsptool.exe").exists() else _bin / "dsptool"
TOOL = os.environ.get("DSPTOOL") or (str(_local) if _local.exists() else "/home/user/ext/bin/dsptool")
