import logging
import time
import asyncio
import aiohttp
import yaml

import modules.minecraft.mojangapi as mojangapi
import modules.hypixel.hypixelapi as hypixelapi

from modules.hypixel.structures import WeightedSkill as Skill
from modules.hypixel.structures import WeightedSlayer as Slayer
from modules.hypixel.structures import WeightedDungeon as Dungeon

API_KEY = 'ca1fbb03-ad6e-4321-880c-217c2cf455b5'

SKYBLOCK_DICT = yaml.load(open("skyblock_constants.yaml", "r"), Loader=yaml.FullLoader)

logger = logging.getLogger('hypixel.player')


class Player(object):
    """This object represents a skyblock player."""

    # Variables. To save memory ;)
    __slots__ = ('uuid', 'username',
                 # Basic Identifiers
                 'skills', 'slayers', 'dungeons', 'weight', 'totalweight',
                 # Skyblock info
                 'discord', 'guild', 'rank',
                 # Hypixel/Discord info
                 '__dict__')
    # Will remove __dict__ once the class is done and all attrs are finalized

    def __init__(self, session, identifier, *args, **kwargs):
        """
Params:
Session    - The session which api requests will use.
Identifier - Either the username or the uuid"""
        # Discerning uuid and username
        self.identifier = identifier
        self.username = None
        self.uuid = None
        self.partialAPIoff = False
        self.recentprofileindex = -1
        self.skills = {}  # Using each skill object to store the type, weight, lvl, xp, etc of every skill
        self.dungeons = {}
        self.slayers = {}
        self.weight = [0, 0]
        self.totalweight = 0
        self.discord = None
        self.guild = None
        self.recentprofile = None
        self.memberdata = None
        self.profilesdata = None
        self.maindata = None
        self.err = False
        self.recentprofileindex = -1
        self.rank = "Unknown"
        self.acquired = 0
        self.data = [None, None, None]

    @property
    def skill_avg(self):
        total = 0
        for skill in self.skills.values():
            total += skill.level
        try:
            total /= len(self.skills)
            return total
        except ZeroDivisionError:
            return float(0)
        # return sum(map(self.skills, lambda x:x.level)) / len(self.skills)
        # Nah, seems too fancy

    @property
    def slayer_total(self):
        total = 0
        for slayer in self.slayers.values():
            total += slayer.exp
        return total

    def skyblock(self, session):
        if self.data[1] is None:
            self.get(session)
        self.parse_skyblock(self, self.data[1])

    async def parse_all(self, session):
        t1 = await self.parse_skyblock(session)
        t2 = await self.parse_general(session)

        # This is more important
        return t1

    async def parse_skyblock(self, session):
        gettime = None
        if self.data[0] is None:
            r = await self.get(session)
            if r['status'] < 0:
                self.partialAPIoff = True
                return {'status': r['status']}
            gettime = r['get']
        data = self.data[0]
        t = time.perf_counter()

        # Go through each profile for the highest weighted one
        highestweight = 0
        if self.data[0]["profiles"] == None:
            logger.warning(f"The user {self.username} does not have any skyblock profiles!")
            return {'status': -1}
        for profileid, profile in enumerate(self.data[0]["profiles"]):
            weight = self.parse_skyblock_singleprofile(profile['members'][self.uuid])
            if (weight >= highestweight):
                bestprofile = profileid
                highestweight = weight

        self.parse_skyblock_singleprofile(self.data[0]["profiles"][bestprofile]['members'][self.uuid])

        # The fruit name of the profile, because why not. May use sometime later?
        cute_name = self.data[0]["profiles"][profileid]["cute_name"]
        t = round(time.perf_counter() - t, 7)

        # Return a norminal status and the processing time
        return {'status': 0, 'proc': t, 'get': gettime}

    def parse_skyblock_singleprofile(self, data):
        """
        Updates the profile's attributes based on the data given.
        Params:
        Data       - The data obtained via a Skyblock API call.
        """
        self.skills, self.slayers, self.dungeons = {}, {}, {}
        self.err = False
        self.partialAPIoff = False
        self.weight = [0, 0]
        for slayer_type in SKYBLOCK_DICT["SLAYERS"]:
            try:
                slayerxp = data['slayer_bosses'][slayer_type.lower()]['xp']
                self.slayers[slayer_type] = Slayer(slayer_type, slayerxp)
            except KeyError:
                logger.debug(f"The user {self.username} has not unlocked the slayer {slayer_type}!")
                self.slayers[slayer_type] = Slayer(slayer_type)

        for skill_type in SKYBLOCK_DICT["SKILLNAMES"]:
            try:
                exp = round(data['experience_skill_' + skill_type], 2)
                self.skills[skill_type] = Skill(skill_type, value=exp, vtype='exp')
            except KeyError:
                logger.debug(
                    f"The user {self.username} has not unlocked the skill {skill_type}, or their API isn't on.")
                self.partialAPIoff = True
                break

        # DUNGEONS
        for dung_type in SKYBLOCK_DICT["DUNGEONS"]:
            try:
                exp = round(data["dungeons"]["dungeon_types"][dung_type]["experience"], 2)
                self.dungeons[dung_type] = Dungeon(dung_type, value=exp, vtype='exp')
            except KeyError:
                logger.debug(f"The user {self.username} has not unlocked the dungeon {dung_type}!")
                self.dungeons[dung_type] = Dungeon(dung_type)

        for dung_type in SKYBLOCK_DICT["CLASSES"]:
            try:
                exp = round(data["dungeons"]["player_classes"][dung_type]["experience"], 2)
                self.dungeons[dung_type] = Dungeon(dung_type, value=exp, vtype='exp')
            except KeyError:
                logger.debug(f"The user {self.username} has not unlocked the dungeon {dung_type}!")
                self.dungeons[dung_type] = Dungeon(dung_type)

        if self.partialAPIoff:
            logger.debug(
                f"Since some data from user {self.username} are missing, getting data from achievements instead.")
            self.parse_skyblock_achievement(self.data[1])

        # WEIGHT
        for contrb in list(self.skills.values()) + list(self.slayers.values()) + list(self.dungeons.values()):
            self.weight[0] += contrb.weights[0]
            self.weight[1] += contrb.weights[1]

        self.totalweight = round(sum(self.weight), 3)
        return self.totalweight

    def parse_skyblock_achievement(self, data):
        self.skills = {}
        try:
            achievements = data["player"]["achievements"]
            for skill in SKYBLOCK_DICT["SKILLNAMES"]:
                try:
                    lvl = round(achievements[SKYBLOCK_DICT["SKILLS"][skill]])
                    self.skills[skill] = Skill(skill, value=lvl, vtype='lvl')
                except:
                    logger.debug(f"The user {self.username} has not unlocked the skill {skill}!")
                    self.skills[skill] = Skill(skill)
        except Exception as e:
            logger.exception()

    async def parse_general(self, session):
        gettime = None
        if self.data[1] is None:
            r = await self.get(session)
            if r['status'] < 0:
                self.partialAPIoff = True
                return {'status': r['status']}
            gettime = r['get']
        data = self.data[1]
        if not data['success']:
            return {'status': -2}
        t = time.perf_counter()
        try:
            if (data['player']['rank'] == 'YOUTUBER'):
                self.rank = 'YOUTUBER'
        except KeyError:
            pass
        except TypeError:
            return {'status': -2}
        try:
            if (data['player']["mostRecentMonthlyPackageRank"] == 'SUPERSTAR'):
                self.rank = "MVP++"
        except KeyError:
            pass
        except TypeError:
            return {'status': -2}
        try:
            self.rank = data['player']['newPackageRank'].replace("_PLUS", "+")
        except KeyError:
            self.rank = ""
        except TypeError:
            return {'status': -2}
        try:
            self.discord = data["player"]["socialMedia"]["links"]["DISCORD"]
        except KeyError:
            self.discord = None
        except TypeError:
            return {'status': -2}

        # Timing
        t = round(time.perf_counter() - t, 7)
        return {'status': 0, 'proc': t, 'get': gettime}

    # All-in-one function to get player-based data from API
    async def get(self, session, apitype=3):
        """
Gets relevant data from the Hypixel API.
Session: A aiohttp session.
Apitype: A number where each bit represents whether to get the data.
1 - Skyblock
2 - General (Achievement)
4 - Guild (playerguild)
(7 - all)
If the Mojang API has not been called, it will be.
"""
        t1 = time.perf_counter()

        # Mojang API (username, uuid)
        try:
            if not self.username and not self.uuid:
                if len(self.identifier) == 32:
                    self.uuid = self.identifier
                    self.username = await mojangapi.getusername(session, self.uuid)
                else:
                    self.username = self.identifier
                    self.uuid = await mojangapi.getuuid(session, self.identifier)
        except AssertionError:
            # Username doesn't exist.
            return {'status': -2}
        try:
            if apitype & 1:
                self.acquired = self.acquired | 1
                self.data[0] = await hypixelapi.skyblock(session, self.uuid, API_KEY)
            if apitype & 2:
                self.acquired = self.acquired | 2
                self.data[1] = await hypixelapi.general(session, self.uuid, API_KEY)
            if apitype & 4:
                self.acquired = self.acquired | 4
                self.data[2] = await hypixelapi.playerguild(session, self.uuid, API_KEY)
        except AssertionError:
            # Something went wrong with the request, so response status was not 200
            return {'status': -1}
        t = round(time.perf_counter() - t1, 7)
        return {'status': 0, 'get': t}


if __name__ == '__main__':
    async def main():
        global resp
        # (do something here)
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as client:
            p = Player(session=client, identifier='RainbowRoadtrip')
            #            p = Player(session=client, identifier='59147965782f4da6b3f61dd8dc8b1dfd')
            await p.parse_all(session=client)
        #        p.get(skyblock)
        #        print(d["profiles"][2]['members']['8895e842446545c58a736be2c61eefe6'])
        print(p.username)
        print([(i.type, i.level, i.exp, i.weight) for i in p.skills.values()])
        print([(i.type, i.level, i.exp, i.weight) for i in p.dungeons.values()])
        print([(i.type, i.exp, i.weight) for i in p.slayers.values()])
        print(p.weight, p.totalweight)
        print(p.rank, p.discord)


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
