import logging
from typing import Literal
from fastapi import APIRouter, Depends, Header

from app.models.jwt import *
from app.models.users import *
from app.auth import get_current_user, get_current_user_data


router = APIRouter(
    prefix='/examples',
    tags=['examples'],
)


@router.get('/warning')
async def list_tasks():
    logging.warning('This is an example warning log')
    return 'warning logged'


@router.get('/error')
async def list_tasks():
    logging.error('This is an example error log')
    return 'error logged'


@router.get('/exception')
async def list_tasks():
    raise Exception('Intentional exception')

    return 'Exception raised' # unreachable code


@router.get('/user_data', response_model=UserRead)
async def list_tasks(
    token: JWTokenData = Depends(get_current_user),
    user_data: UserRead = Depends(get_current_user_data)
):
    logging.info('Retreiving user data from the auth server.')

    return user_data

#
# Primer klica za 
#

import httpx
from opentelemetry.propagate import inject

from auth import credentials_exception
from app.models.examples import DistanceList

async def get_distances(
    auth_header: str,
    maps_server_url: str,
    coords: list[str],
    mode: Literal[
        'driving',
        'walking',
        'bicycling',
        'transit'
    ],
):
    # create headers
    headers = { 'Authorization': auth_header }

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
            params = qparams,
        )

        if response.status_code == 200:
            distances_str = response.read()
            return DistanceList.parse_raw(distances_str)
        if response.status_code == 401:
            raise credentials_exception

    raise Exception('Exception while communicating with maps server')


from app.config import Settings, get_settings

# primer funkcije
@router.get('/get_path', response_model=UserRead)
async def get_path(
    token: JWTokenData = Depends(get_current_user),
    # to forward token
    authorization: str | None = Header(default=None, include_in_schema=False),
    # site settings
    settings: Settings = Depends(get_settings),
):

    distances = await get_distances(
        auth_header=authorization,
        maps_server_url=settings.maps_server,
        mode='driving',
        coords=[
            #TODO: pridobi seznam tock
        ]
    )

    # sedaj imas seznam v "distances"
