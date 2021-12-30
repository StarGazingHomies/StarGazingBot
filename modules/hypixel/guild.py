import aiohttp
import asyncio
import logging
import requests
import time
import yaml

import modules.hypixel.hypixelapi as hypixelapi
from modules.hypixel.player import Player

API_KEY = 'ca1fbb03-ad6e-4321-880c-217c2cf455b5'

SKYBLOCK_DICT = yaml.load(open("skyblock_constants.yaml","r"), Loader=yaml.FullLoader)

logger = logging.getLogger('hypixel.guild')

def getguild(name):
    if name in Guild.objs.keys():
        return Guild.objs[name]
    obj = Guild(name)
    Guild.objs[name] = obj
    return obj

class Guild(object):
    objs = {}
    def __init__(self, name):
        self.name = name
        self.players = []
        self.usernames = []
        self.uuids = []
        self.data = None
        self.weights = []
        self.skill_averages = []
        self.slayer_totals = []
        self.cata_levels = []
        self.last_update = 0
        self.status = 0
        #0 - normal
        #1 - getting data

    async def getmembers(self, session, key=API_KEY):
        self.data = await hypixelapi.guildmembers(session, self.name, key)
        self.uuids = self.data['guild']['members']
        self.players = [Player(session, i['uuid']) for i in self.uuids]

    async def getweights(self, session, key=API_KEY, bestprofile=True, partialapi = True):

        #Wait for other getweights to complete
        while self.status == 1:
            await asyncio.sleep(1)

        if time.time() - self.last_update < 1200:
            #Less than 20 mins since last update
            return self.weights

        #Block other functions
        self.status = 1

        self.weights = []
        if self.data == None:
            await self.getmembers(session)

        for pi, player in enumerate(self.players):
            logger.debug(f"Getting data for {player.identifier}")
            status = await player.parse_all(session)
            if self.players[pi].partialAPIoff:
                self.weights.append((player.username, player.totalweight, "partial API off"))
            else:
                self.weights.append((player.username, player.totalweight))

            logger.info(f"Skyblock Guild {self.name} getting data: {pi+1} out of {len(self.players)}")
            await asyncio.sleep(1)

        #Sort the weight
        self.weights.sort(key=lambda x:x[1], reverse=True)

        #Update status & last updated time
        self.last_update = time.time()
        self.status = 0
        return self.weights

if __name__ == '__main__':
    
    async def main():
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as client:
            g = Guild('Atlantica')
            r = await g.getweights(client)
        print(r)
#    loop = asyncio.get_event_loop()
#    loop.run_until_complete(main())
