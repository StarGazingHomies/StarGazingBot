# This module tracks messages sent by users and reacts accordingly.
# It will be toggleable when settings come online.

import os
import logging
import time
import random
import yaml
# from language_tool_python import LanguageTool
from textweight import weigh

logger = logging.getLogger('main.tracker')

interactionspath = os.path.join(os.getcwd(), 'interactions')
MATCHING = yaml.load(open(os.path.join(interactionspath, "matching.yaml")), yaml.FullLoader)
CONTAIN = yaml.load(open(os.path.join(interactionspath, "contain.yaml")), yaml.FullLoader)

class MemberWeight(object):
    def __init__(self):
        self.path = os.path.join(os.getcwd(),'userdata')
        self.memberpath = os.path.join(self.path, 'members')
        # Just in case I want to implement this. It's too slow for practical use though
#        self.your_youre_check = LanguageTool('en-US')
#        self.your_youre_check.enabled_rules = 'YOUR_YOU_RE'
        # Response cooldown so people can't spam the bot
        # Cooldown: 1200s, but no one should know this.
        self.matchingcd = {}
        self.containcd = {}
        self.usertriggers = {}
        self.lastmessage = {}

        # User points. Simple format - {serverid:userid:points}
        try:
            self.points = yaml.safe_load(open(os.path.join(self.path, 'points.yaml'), 'r'))
        except FileNotFoundError:
            self.points = {}
            yaml.dump(self.points, open(os.path.join(self.path, 'points.yaml'), "w"))
        if self.points is None:
            self.points = {}
            yaml.dump(self.points, open(os.path.join(self.path, 'points.yaml'), "w"))
        print(self.points)
        # Amount of changes in points
        self.ptchanges = 10
        # How many points changes to autosave at
        self.ptautosave = 10
        # Last updated timestamp
        self.ptlbupdate = 0
        self.ptlbupdatetime = 1200
        self.leaderboard = {}

    def __str__(self):
        return "A Listener of everything."
    
    # Points modifications
    def add_points(self, serverid, userid, points):
        try:
            self.points[serverid][userid] += points
        except KeyError:
            try:
                self.points[serverid][userid] = points
            except KeyError:
                self.points[serverid] = {userid:points}
        self.ptchanges += 1
        if self.ptchanges >= self.ptautosave:
            self.ptchanges = 0
            yaml.dump(self.points, open(os.path.join(self.path,'points.yaml'),"w"))

    def remove_points(self, serverid, userid, points):
        try:
            self.points[serverid][userid] -= points
        except KeyError:
            try:
                self.points[serverid][userid] = -points
            except KeyError:
                self.points[serverid] = {userid:-points}
        if self.points[serverid][userid] < 0:
            self.points[serverid][userid] = 0
        self.ptchanges += 1
        if self.ptchanges >= self.ptautosave:
            self.ptchanges = 0
            yaml.dump(self.points, open(os.path.join(self.path,'points.yaml'),"w"))

    def get_points(self, serverid, userid):
        try:
            return self.points[serverid][userid]
        except KeyError:
            return 0

    def set_points(self, serverid, userid, points):
        # Always save if this is called, since only bot owner can do this!
        try:
            self.points[serverid][userid] = points
        except KeyError:
            self.points[serverid] = {userid:points}
        self.ptchanges = 0
        yaml.dump(self.points, open(os.path.join(self.path,'points.yaml'),"w"))

    # Points leaderboards
    def lbupdate(self):
        for serverid, subpts in self.points.items():
            npts = subpts.copy()

            # Bot owner does not count
            try:
                npts.pop(523717630972919809)
            except KeyError:
                # Bot owner has never been on server
                pass

            # Sort
            newl = [(key, val) for key, val in npts.items()]
            newl.sort(key=lambda x: x[1], reverse=True)
            self.leaderboard[serverid] = newl
        return

    def getlb(self, serverid):
        if time.time() - self.ptlbupdate > self.ptlbupdatetime:
            self.lbupdate()
        return self.leaderboard[serverid]
    
    # Discord
    async def on_message(self, message):
        if message.author.bot:
            return

        r = weigh(message.content)
        logger.info("{0.guild} - #{0.channel} - Message from {0.author} [Points: {1}] - {0.content}".format(message, r))

        # If DM message, no points
        try:
            serverid = message.guild.id
        except AttributeError:
            return
        authorid = message.author.id

        
        # In all of a user's messages in a 75 seconds (since their first),
        # the amount of points will be determined by the maximum amount.
        try:
            lastmsgtime, content, lastpoints = self.lastmessage[serverid][authorid]

            # If the last message is more than 75 seconds away, refresh and add points as normal
            if time.time() - lastmsgtime > 75:
                self.add_points(serverid, authorid, r)
                self.lastmessage[serverid][authorid] = (time.time(), message.content, r)

            # If the last message a user sends is the same
            elif message.content == content:
                self.remove_points(serverid, authorid, 150)  # Remove 150 points
                self.lastmessage[serverid][authorid] = (lastmsgtime, content, r)
                await message.delete(delay=0.1)

            # If the new message has more points than the old one
            elif r > lastpoints:
                self.add_points(serverid, authorid, r-lastpoints)
                self.lastmessage[serverid][authorid] = (lastmsgtime, message.content, r)
        except KeyError:
            try:
                self.add_points(serverid, authorid, r)
                self.lastmessage[serverid][authorid] = (time.time(), message.content, r)
            except KeyError:
                self.lastmessage[serverid] = {}
                self.lastmessage[serverid][authorid] = (time.time(), message.content, r)

        
        # User-bot interactions are also included
        for i, matchresp in enumerate(MATCHING):
            vals, resps = matchresp
            try:
                if time.time() - self.matchingcd[i] < 1200:
                    continue
            except KeyError:
                # no prior cooldown.
                pass
            for val in vals:
                if message.content.lower() == val:
                    await message.channel.send(resps[random.randint(0,len(resps)-1)])
                    self.matchingcd[i] = time.time()
                    break

        for i, containresp in enumerate(CONTAIN):
            vals, resps = containresp
            try:
                if time.time() - self.containcd[i] < 1200:
                    continue
            except KeyError:
                # no prior cooldown.
                pass
            for val in vals:
                if message.content.lower().count(val) >= 1:
                    await message.channel.send(resps[random.randint(0, len(resps)-1)])
                    self.containcd[i] = time.time()
                    break
    
