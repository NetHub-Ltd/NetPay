#!/usr/bin/env python3
"""CLI entry for the independent frontend/BFF staging probe."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.identity.staging_probe import main

if __name__ == "__main__":
    raise SystemExit(main())
