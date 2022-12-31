from typing import Optional
from pydantic import BaseModel, Field

from uuid import UUID, uuid4
from datetime import datetime


class CommonBase(BaseModel):
    id: UUID = Field(default_factory=uuid4, alias='_id')
    created: datetime = Field(default_factory=datetime.utcnow)


class CommonBaseRead(BaseModel):
    id: UUID = Field(alias='_id')
    created: datetime
