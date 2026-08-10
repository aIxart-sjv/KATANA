from pathlib import Path


PROGRAMS = [
    "exec",
    "connect",
]

ROOT = (
    Path(__file__)
    .parent.parent
)

BUILD_DIR = ROOT / "build"