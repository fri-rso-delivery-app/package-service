from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder

from app.db import db
from app.models.packets import *
from app.models.jwt import *
from app.auth import get_current_user, get_current_user_data
from app.models.users import UserRead

TABLE = 'packets'
table = db[TABLE]


router = APIRouter(
    prefix='/packets',
    tags=['packets'],
)


async def get_packet(
    id: str | UUID,
    # enforce ownership + auth
    token: JWTokenData = Depends(get_current_user),
) -> Packet:
    packet = await table.find_one({'_id': str(id), 'user_id': str(token.user_id)})
    if not packet: raise HTTPException(status_code=404, detail=f'Packet not found')

    return Packet(**packet)


@router.post('/', response_model=Packet)
async def create_packet(*, packet: Packet, token: JWTokenData = Depends(get_current_user), user_data: UserRead = Depends(get_current_user_data)):
    if user_data.is_delivery_person:
        raise Exception("Not Authorised to create packets")
    # create
    packet_db = jsonable_encoder(Packet(**packet.dict(), user_id=token.user_id))
    new_packet = await table.insert_one(packet_db)
    created_packet = await get_packet(new_packet.inserted_id, token)
    
    return created_packet


@router.get("/request_route")
async def request_route(store: str, time_in_hours: float, user_data: UserRead = Depends(get_current_user_data)):
    if user_data.is_customer:
        raise Exception("Not Authorised to request delivery routes")
    # create route


@router.get('/', response_model=List[PacketRead])
async def list_packets(token: JWTokenData = Depends(get_current_user), user_data: UserRead = Depends(get_current_user_data)):
    # customer can see their packages
    if user_data.is_customer:
        return await table.find({'user_id': str(token.user_id)}).to_list(1000)
    # delivery person can see all packages
    if user_data.is_delivery_person:
        return await table.find().pretty().to_list(1000)


@router.get('/{id}', response_model=PacketRead)
async def read_packet(packet: Packet = Depends(get_packet)):
    return packet


@router.patch('/{id}', response_model=PacketRead)
async def update_packet(*,
    token: JWTokenData = Depends(get_current_user),
    packet: Packet = Depends(get_packet),
    packet_update: PacketUpdate
):
    # update packet
    packet_update = packet_update.dict(exclude_unset=True)
    await table.update_one({'_id': str(packet.id)}, {'$set': packet_update})
    
    return await get_packet(packet.id, token)


@router.delete('/{id}')
async def delete_packet(packet: Packet = Depends(get_packet),):
    await table.delete_one({'_id': str(packet.id)})

    return {'ok': True}
