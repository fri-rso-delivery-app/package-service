from uuid import UUID
from pydantic import BaseModel


from ._common import CommonBase, CommonBaseRead


# common (base, read, write)
class PacketBase(BaseModel):
    delivery_destination: str
    store_id: UUID
    description: str | None = None


# db-only overrides
class Packet(CommonBase, PacketBase):
    user_id: UUID


# create-only overrides
class PacketCreate(PacketBase):
    pass


# updatable fields
class PacketUpdate(BaseModel):
    description: str | None


# read-only overrides
class PacketRead(CommonBaseRead, PacketBase):
    pass
