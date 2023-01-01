from typing import List
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from fastapi.encoders import jsonable_encoder

from app.db import db
from app.models.packets import *
from app.models.jwt import *
from app.auth import get_current_user, get_current_user_data
from app.models.users import UserRead

import httpx
from opentelemetry.propagate import inject

from app.auth import credentials_exception
from app.models.examples import DistanceList

from app.config import Settings, get_settings
from app.routers.stores import table as stores_table

import itertools

TABLE = 'packets'
table = db[TABLE]


router = APIRouter(
    prefix='/packets',
    tags=['packets'],
)


async def get_packet(id: str | UUID, token: JWTokenData = Depends(get_current_user), user_data: UserRead = Depends(get_current_user_data)) -> Packet:
    if user_data.is_delivery_person:
        packet = await table.find_one({'_id': str(id)})

    else:
        packet = await table.find_one({'_id': str(id), 'user_id': str(token.user_id)})

    if not packet: raise HTTPException(status_code=404, detail=f'Packet not found')

    return Packet(**packet)


@router.post('/', response_model=Packet)
async def create_packet(*, packet: Packet, token: JWTokenData = Depends(get_current_user), user_data: UserRead = Depends(get_current_user_data)):
    if not user_data.is_customer:
        raise Exception("Not Authorised to create packets")
    # create
    packet_db = jsonable_encoder(Packet(**packet.dict(), user_id=token.user_id))
    new_packet = await table.insert_one(packet_db)
    created_packet = await get_packet(new_packet.inserted_id, token)
    
    return created_packet


@router.get("/request_route", response_model=UserRead)
async def request_route(store_id: UUID,
                        time_in_minutes: float,
                        mode: Literal[
                                'driving',
                                'walking',
                                'bicycling',
                                'transit'
                            ] = Query(default='driving'),
                        user_data: UserRead = Depends(get_current_user_data),
                        token: JWTokenData = Depends(get_current_user),
                        authorization: str | None = Header(default=None, include_in_schema=False),
                        settings: Settings = Depends(get_settings)):
    # make sure only delivery people can get routes
    if not user_data.is_delivery_person:
        raise Exception("Not Authorised to request delivery routes")

    # get all packets from store
    list_of_items = await table.find({"store_id": str(store_id)}).to_list(1000)

    # get all locations of packets
    coordinates_of_items = [item.delivery_destination for item in list_of_items]

    # add initial store location
    store_coordinates = await stores_table.findOne({"_id": str(store_id)}, "location").to_list(1)
    coordinates_of_items_and_store = store_coordinates + coordinates_of_items

    # get distances
    all_distances = await get_distances(
        auth_header=authorization,
        maps_server_url=settings.maps_server,
        mode=mode,
        coords=coordinates_of_items_and_store
    )

    # dictionary of distances
    distances_dict = {}
    for item in all_distances:
        loc1 = item.p1
        loc2 = item.p2
        duration = item.duration
        distances_dict[(loc1, loc2)] = duration

    coodrinates_of_items2 = []

    for coord in coordinates_of_items:
        distance = distances_dict[(store_coordinates, coord)]
        if distance < time_in_minutes:
            coodrinates_of_items2.append(coord)

    options = []

    for L in range(len(coodrinates_of_items2) + 1):
        for subset in itertools.combinations(coodrinates_of_items2, L):
            subset = [store_coordinates] + subset
            length = 0
            for c1, c2 in zip(subset, subset[1:]):
                length += distances_dict[(c1, c2)]

            if distance < time_in_minutes:
                options.append((subset, length))

    selected, _ = max(options, key=lambda x: (len(x[0]), x[1]))

    selected.pop(0)

    result = []
    for coord in selected:
        result.append(await table.find({"delivery_destination": str(coord)}).first())


async def get_distances(auth_header: str, maps_server_url: str, coords: list[str], mode: Literal['driving', 'walking', 'bicycling', 'transit'],):
    # create headers
    headers = {'Authorization': auth_header}

    # inject trace info to header
    inject(headers)

    qparams = {
        'coords': coords,
        'mode': mode,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f'{maps_server_url}/distances/points_list',
            headers=headers,
            params=qparams,
        )

        if response.status_code == 200:
            distances_str = response.read()
            return DistanceList.parse_raw(distances_str)
        if response.status_code == 401:
            raise credentials_exception

    raise Exception('Exception while communicating with maps server')


@router.get('/', response_model=List[PacketRead])
async def list_packets(token: JWTokenData = Depends(get_current_user), user_data: UserRead = Depends(get_current_user_data)):
    # customer can see their packages
    if user_data.is_customer:
        return await table.find({'user_id': str(token.user_id)}).to_list(1000)
    # delivery person can see all packages
    if user_data.is_delivery_person:
        return await table.find().to_list(1000)


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
