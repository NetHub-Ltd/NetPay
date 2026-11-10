#!/usr/bin/env python3
"""CLI entry: python -m app.identity.staging_probe or this wrapper from backend/."""
from __future__ import annotations

import sys
from pathlib import Path

# Allow `python scripts/identity_staging_probe.py` from backend/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.identity.staging_probe import main

if __name__ == "__main__":
    raise SystemExit(main())
