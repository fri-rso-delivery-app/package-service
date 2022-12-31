from uuid import UUID
from pydantic import BaseModel


class JWToken(BaseModel):
    access_token: str
    token_type: str


class JWTokenData(BaseModel):
    username: str | None = None
    user_id: UUID
