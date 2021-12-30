import asyncio, aiohttp
import json
import logging

logger = logging.getLogger('hypixel.hypixelapi')

# All methods are asynchronous since this is a web application... no?... kinda?


async def aiorequest(session, url, convert=True, *args, **kwargs):
    logger.debug(f"Sending a GET request to {url}.")
    for i in range(5):
        resp = await session.get(url, *args, **kwargs)
        d = await resp.text()
        if resp.status == 200:
            break
        logger.warning(f"Error getting response from {url}. Response status {resp.status} (Try #{i+1})")
        await asyncio.sleep(1)
    if resp.status != 200:
        logger.warning(f"Multiple errorneous responses from {url}, will return empty object instead.")
    # Convert to json?
    if convert:
        d = json.loads(d)
    return d


#Player

async def skyblock(session, uuid, key, *args, **kwargs):
    """API call for all skyblock data.
Params:
Uuid       - Player UUID. Usernames don't work here!
Key        - API key. Obtain by using /api new on Hypixel
"""
    url = f'https://api.hypixel.net/skyblock/profiles?key={key}&uuid={uuid}'
    return await aiorequest(session, url,*args, **kwargs)

async def general(session, uuid, key, *args, **kwargs):
    url = f"https://api.hypixel.net/player?key={key}&uuid={uuid}"
    return await aiorequest(session, url, *args, **kwargs)

async def playerguild(session, uuid, key, *args, **kwargs):
    url = f'https://api.hypixel.net/findGuild?key={key}&byUuid={uuid}'
    return await aiorequest(session, url, *args, **kwargs)

#Guild

async def guildmembers(session, name, key, *args, **kwargs):
    url = f'https://api.hypixel.net/guild?key={key}&name={name}'
    return await aiorequest(session, url, *args, **kwargs)


#Testing code
if __name__ == '__main__':
    #Testing. When imported, this doesn't happen.
    async def main():
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as client:
#            r = await skyblock(client, '8895e842446545c58a736be2c61eefe6', 'ca1fbb03-ad6e-4321-880c-217c2cf455b5')
            r = await guildmembers(client, 'Atlantica', 'ca1fbb03-ad6e-4321-880c-217c2cf455b5')
        with open("Guild test.txt","w") as fo:
            fo.write(str(r))
#        with open("Hypixel API test (RainbowRoadtrip).txt","w") as fout:
#            fout.write(str(r))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
