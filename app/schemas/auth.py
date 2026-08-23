from __future__ import annotations
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str
    tenant_id: Optional[UUID] = None

class UserOut(BaseModel):
    id: UUID
    email: str
    role: str
    tenant_id: Optional[UUID] = None
    is_active: bool
    model_config = {"from_attributes": True}

class OAuthTokenRequest(BaseModel):
    grant_type: str = "client_credentials"
    client_id: str
    client_secret: str

class OAuthClientCreate(BaseModel):
    tenant_id: UUID
    name: str = Field(max_length=120)

class OAuthClientOut(BaseModel):
    client_id: str
    client_secret: str
    name: str
    tenant_id: UUID
