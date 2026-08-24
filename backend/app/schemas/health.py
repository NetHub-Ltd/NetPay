from __future__ import annotations
from pydantic import BaseModel

class HealthOut(BaseModel):
    status: str
    database: bool
    redis: str
    admin_ready: bool
    environment: str
    version: str
