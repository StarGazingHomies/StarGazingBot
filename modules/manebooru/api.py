"""
API calls to Manebooru, and structures for responses.
"""

import asyncio
import json
import os
import random

import aiohttp
import yaml

async def aiorequest(session, url, convert=True, *args, **kwargs):
    """Performs an asyncio request and converts the result into a json."""
    async with session.get(url, *args, **kwargs) as resp:
        assert resp.status == 200
        d = await resp.text()
    # Convert to json?
    if convert:
        d = json.loads(d)
    return d

async def API_featured(session, *args, **kwargs):
    """Gets the featured image on Manebooru."""
    url = f'https://manebooru.art/api/v1/json/images/featured/'
    return await aiorequest(session, url, *args, **kwargs)

#Performs an image search
async def API_search(session, q, page=1, per_page=None, sd=None, sf='random', filter_id=1, key=None, *args, **kwargs):
    """Searches the Manebooru API for a specified image.
Arguments correspond to Manebooru's API.
q:         query (list)                               Format: ['safe','cute','hoers', ... ]
filter_id: The ID of the filter. Defaults to 1 (int)
page:      The page number
per_page:  The amount of images per page
sd:        Sort direction
sf:        Sort field
key:       API key (not necessary)"""
    if not 'safe' in q:
        q_str = 'safe, '
    else:
        q_str = ''
    for elem in q:
        if elem != '':
            q_str += elem + ", "
    q_str = q_str[:-2]
    url = f'https://manebooru.art/api/v1/json/search/images?q={q_str}'
    if page:
        url += f"&page={page}"
    if per_page:
        url += f"&per_page={per_page}"
    if sd:
        url += f"&sd={sd}"
    if sf:
        url += f"&sf={sf}"
    if key:
        url += f"&key={key}"
    return await aiorequest(session, url, *args, **kwargs)

#Not sure what this is used for
async def API_oembed(session, url):
    """Gets the embed for manebooru.
Discord automatically does this, which means it may be redundant."""
    url = f'https://manebooru.art/api/v1/json/oembed?url={url}'
    return await aiorequest(session, url)
