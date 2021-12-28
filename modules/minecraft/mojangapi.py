"""
Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import asyncio
import aiohttp
import json
import logging

from modules.minecraft.cache import UsernameCache

logger = logging.getLogger('minecraftapi')

#Getting uuids from the Mojang API servers directly

async def apigetuuid(session, username):
    """Returns the uuid of the player with the specified username, using the Mojang API only."""
    url = f'https://api.mojang.com/users/profiles/minecraft/{username}'
    try:
        async with session.get(url) as resp:
            assert resp.status == 200
            d = await resp.text()
        uuid = json.loads(d)["id"]
        return uuid
    except Exception as e:                               #Missing username...?
        raise e
    return

async def apigetusername(session, uuid):
    """Returns the username of the player with the specified uuid, using the Mojang API only."""
    url = 'https://api.mojang.com/user/profiles/'+uuid+'/names'
    try:
        async with session.get(url) as resp:
            assert resp.status == 200
            d = await resp.text()
        usernames = json.loads(d)
        #Getting the latest username. The Mojang API provides username history.
        lastchanged = 0
        lastusername = usernames[0]["name"]
        for username in usernames[1:]:
            if username["changedToAt"] > lastchanged:
                lastchanged = username["changedToAt"]
                lastusername = username["name"]
        return lastusername
    except AssertionError:
        return
    except Exception as e:
        raise e
    return

#Use these. They automatically use cached values if they are within a day.

async def getuuid(session, username, cache=True):
    """Returns the uuid of the player with the specified username."""
    if cache:
        r = UsernameCache.lookup(username)
    if not r:
        r = await apigetuuid(session, username)
        if not r:       #Probably username not existing, or API broken.
            #Insert logging warning
            logger.warning(f"Connection error, or user doesn't exist: {username}")
            return False
        UsernameCache.update(username, r)
    return r

async def getusername(session, uuid):
    """Returns the username of the player with the specified uuid."""
    r = UsernameCache.lookup(uuid)
    if not r:
        r = await apigetusername(session, uuid)
        if not r:       #Probably username not existing, or API broken.
            #Insert logging warning
#            print(f"Connection error, or user doesn't exist: {uuid}")
            return False
        UsernameCache.update(r, uuid)
    return r


if __name__ == '__main__':
    #Testing. When imported, this doesn't happen.
    async def main():
        async with aiohttp.ClientSession() as client:
            r = await apigetuuid(client, "RainbowRoadtrip")
            r2 = await apigetusername(client, r)
            r3 = await getusername(client, "66d2e6f34807461c997585b9627fb510")
            r4 = await getuuid(client, r3)
            print(r, r2, r3, r4, sep='\n')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
