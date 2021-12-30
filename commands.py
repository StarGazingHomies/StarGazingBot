"""
Commands interpreter for the Discord bot.
Handles the cooldown of commands.
Also looks for follow-up interactions if necessary.
"""

import logging
import math
import os
import random
import sys

import aiohttp
import asyncio
import discord
import yaml
import time

from membermanager import UserManager
from serversettings import GetSettingsManager as SettingsManager
from event import CLS_EventFileHandler as EventManager
from modules.dnd.roll import calculate as rolldice
from modules.hypixel.player import Player
from modules.hypixel.guild import getguild
import modules.minecraft.mojangapi as mojangapi
from structures import PagedResponse, ExpandableResponse, VerifyResponse
import command

SKYBLOCK_DICT = yaml.load(open("skyblock_constants.yaml", "r"), Loader=yaml.FullLoader)

cmdinfopath = os.path.join(os.getcwd(), "command", "commandinfo")
COMMANDMAP = yaml.safe_load(open(os.path.join(cmdinfopath, "commandmap.yaml"), "r"))
CATEGORYMAP = yaml.safe_load(open(os.path.join(cmdinfopath, "ctgymap.yaml"), "r"))

logger = logging.getLogger('commands')

# Quality of Life Functions


def betternum(i, sep=','):
    stri = str(i)
    i = -3
    while i > -len(stri):
        stri = stri[:i] + sep + stri[i:]
        i -= 3 + len(sep)
    return stri


def timetosec(t):
    if t[-1] == 's':
        return int(t[:-1])
    elif t[-1] == 'm':
        return 60 * int(t[:-1])
    elif t[-1] == 'h':
        return 3600 * int(t[:-1])
    elif t[-1] == 'd':
        return 86400 * int(t[:-1])
    elif t[-1] == 'w':
        return 604200 * int(t[:-1])
    else:
        return -1


def sec_to_time(s, short=True):
    if s < 0:
        return "<0 seconds"
    responses = ("ms", "s", "m", "h", "d", "w")
    if not short:
        responses = (" milliseconds", " seconds", " minutes", " hours", " days", " weeks")
    if s < 0.001:
        return "<1 ms"
    elif s < 1:
        return f"{round(s*1000,2)}{responses[0]}"
    elif s < 60:
        return f"{round(s,2)}{responses[1]}"
    elif s < 3600:
        return f"{int(s//60)}{responses[2]}, {round(s%60,2)}{responses[1]}"
    elif s < 86400:
        return f"{int(s//3600)}{responses[3]}, {s%3600//60}{responses[2]}, {round(s%60,2)}{responses[1]}"
    elif s < 86400*7:
        return f"{round(s/86400,2)}{responses[4]}"
    else:
        return f"{round(s/86400/7,2)}{responses[5]}"

# Handler Object
# Method that listens to Discord messages, and checks for reactions/follow up msgs.


class Listener(object):
    def __init__(self, client):
        self.version = "Version: 1w6a"                                                      # Version
        self.client = client                                                                # The bot client
        self.tracker = None                                                                 # Tracker for points
        self.reqsession = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))    # Client for requests
        self.usermanager = UserManager()                                                    # User manager
        self.settingsmanager = SettingsManager()                                            # Settings manager
        self.eventmanager = EventManager()

        # Listeners
        self.listeners = {}
        for module in command.__all__:
            self.listeners[module] = eval(f"command.{module}.Listener()")
        self.maneinterface = command.manebooru.Listener()                                   # Manebooru interface
#        self.mcinterface = McMessengerInterface()                                          # Minecraft interface
        self.helppath = os.path.join(os.getcwd(), 'commanddoc')                             # Documentation path
        self.scroll = []        # Format: (message, userid, scrollable object, timestamp)
        self.expand = []        # Format: (message, userid, expandable object, timestamp)
        self.verifyreact = []   # Format: (message, userid, verify response obj, timestamp)
        self.cooldown = {}      # Cooldown format: { author.id : {last: timestamp, command:timestamp} }
        self.glbtasks = {}      # Format: { message.guild.id : {status: (int)status, task: (async task) task } }
        self.owner = None
        self.garbo = None
        self.stopcounter = 0
        # Status
        # -1 - shutdown
        # 0  - init not complete
        # 1  - normal
        # 2  - garbage collecting
        # 3  - processing reaction
        # 4  - processing message
        self.status = 0

    def __str__(self):
        return "A Listener class, listening to all messages."

#  Methods

    @staticmethod
    def get_command_from_submap(command, cmdmap):
        if command in cmdmap:
            if 'alias' in cmdmap[command]:
                alias = cmdmap[command]['alias']
                return cmdmap[alias]
            return cmdmap[command]
        return False

    def get_command(self, message):
        if isinstance(message, str):
            command = message
        else:
            pfx = self.settingsmanager.server_get(message.guild.id, 'prefix')
            args = message.content.split(' ')
            command = args[0][len(pfx):]

        # First, check if the command specifies a namespace.
        # If it does, the namespace is determined.
        # This would not happen with the help message, the only time input is a string.
        if command in self.listeners:
            namespace = command
            command = args[1]
            if command in COMMANDMAP[namespace]:
                return {'namespace':namespace, **COMMANDMAP[namespace][command]}
            else:
                return None

        # Then, search the general commands
        generalmap = COMMANDMAP['general']
        ans = self.get_command_from_submap(command, generalmap)
        if ans:
            return {'namespace': None, **ans}

        # Next, search priority server settings
        try:
            settings = self.settingsmanager.server_get(message.guild.id)
            for key in settings['namespaces']:
                subcmdmap = COMMANDMAP[key]
                ans = self.get_command_from_submap(command, subcmdmap)
                if ans:
                    return {'namespace': key, **ans}
        except AttributeError:
            # No associated server
            pass

        # Next, search through all commands
        for key, subcmdmap in COMMANDMAP.items():
            ans = self.get_command_from_submap(command, subcmdmap)
            if ans:
                return {'namespace': key, **ans}

        return None

    def get_perms(self, message):
        """Gets the permissions for the given author of the message."""
        logger.debug(f"Getting permissions for {message.author.id}")
        # Bot owner (me!)
        if message.author.id == 523717630972919809 or message.author.id == 223085013258731521:
            return 5

        # Bot itself (different me!)
        if message.author.id == 797930119476936715:
            return 2

        # DM commands
        if message.guild is None:
            return 1

        # Server owner
        if message.author.id == message.guild.owner.id:
            return 3

        settings = self.settingsmanager.server_get(message.guild.id)
        for role in message.author.roles:
            if settings['staffrole'] == role.id:
                return 2
        return 1

    def check_perms(self, message, command):
        """Check for command availability based on permissions of the author."""
        logger.debug(f"Checking permissions for {message.author.id} for command {command}")
        p = self.get_perms(message)

        if p == 5:
            return 2
        if p >= command['permission']:
            return 1
        return 0

# Background Tasks

    async def garbage_collect(self):
        """A garbage collection loop that times out certain elements."""
        self.status = 1
        logger.info(f"Garbage collection loop initiated")
        while self.status > 0:

            # status=2 - collecting
            self.status = 2
            logger.info(f"Garbage collecting...")

            # Scrollables collection
            for i in range(len(self.scroll)-1, -1, -1):
                msg, user, s, timestamp = self.scroll[i]
                if time.time() - timestamp > 120:
                    timeoutmsg = s.timeout()
                    await msg.edit(**timeoutmsg, suppress=True)
                    await msg.clear_reactions()
                    self.scroll.pop(i)

            for i in range(len(self.expand)-1, -1, -1):
                msg, user, s, timestamp = self.expand[i]
                if time.time() - timestamp > 120:
                    self.expand.pop(i)
                    embed = s.timeout
                    await msg.edit(embed=embed, suppress=True)

            for i in range(len(self.verifyreact)-1, -1, -1):
                msg, user, s, timestamp = self.verifyreact[i]
                if time.time() - timestamp > 120:
                    self.verifyreact.pop(i)
                    embed = s.timeout
                    await msg.edit(embed=embed, suppress=True)

            # Wait for next cycle | status=1 - normal
            self.status = 1
            logger.info(f"Garbage collecting finished")
            await asyncio.sleep(10)
            while self.status > 1:
                await asyncio.sleep(1)

        logger.info("Ending tasks for shutdown")
        # Shut down - replace every embed with timed out
        for i, pkg in enumerate(self.scroll):
            msg, user, s, timestamp = pkg
            embed = discord.Embed(title=s.title, description=s.pages[s.cur])
            embed.set_footer(text="Timed out.")
            await msg.edit(embed=embed, suppress=True)
        for i, pkg in enumerate(self.expand):
            msg, user, s, timestamp = pkg
            embed = s.timeout
            await msg.edit(embed=embed, suppress=True)
        for i, pkg in enumerate(self.verifyreact):
            msg, user, s, timestamp = pkg
            embed = s.timeout
            await msg.edit(embed=embed, suppress=True)
        return

# Bot Events Processing

    async def on_ready(self):
        logger.info(f"Bot ready, initiating loops.")
        if self.status == 0:
            self.garbo = asyncio.create_task(self.garbage_collect())
            self.owner = await self.client.fetch_user(523717630972919809)
            await asyncio.sleep(1)
            # Atlantica
#            glb_channel = await self.client.fetch_channel(888044419251589130)
#            await glb_channel.send("at!echo at!loopglb start Atlantica 1h (Weight Leaderboard autostart)")

    async def on_message(self, message):

        logger.debug(f"Received message {message.content} in {message.channel} in {message.guild}.")

        # Pings give prefix
        if message.content.startswith('<@!797930119476936715>'):
            await message.channel.send(f"My prefix is `{'star!' if pfx is None else pfx}`")
            return

        # Commands prefix
        if message.guild is None:
            # DM commands
            pfx = 'star!'

        else:
            # Get the prefix
            pfx = self.settingsmanager.server_get(message.guild.id, 'prefix')
            enabled = self.settingsmanager.server_get(message.guild.id, 'enabled')
            conditionals = self.settingsmanager.server_get(message.guild.id, 'conditional')

            # New server - send setup message
            if pfx is None:
                if message.content == "star!setup":
                    logger.info("Setting up server {message.guild}.")
                    if message.author.guild_permissions.manage_guild:
                        self.settingsmanager.newserver(message.guild.id)
                        await message.channel.send("Bot initialized")
                    else:
                        await message.channel.send("You don't have permissions to do that!")
                elif message.content.startswith("star!"):
                    logger.warning("Server {message.guild} is not set up!")
                    await message.channel.send("This bot is not set up yet!\
                    Ask an admin to run star!setup to initialize the bot.")
                return

            if (not enabled) and message.content.startswith(pfx):
                await message.channel.send("The bot is disabled for this server. Ask a server owner for details.")
                return

            for condition, match, position, result in conditionals:
                # Condition - type of condition such as reaction and message
                # Match - what to match the object to
                # Position - the position of the object
                if condition == 'message':
                    if match == message.content and position == message.channel.id:
                        await result

        # Existing server
        if message.content.startswith(pfx):

            # Get command
            command = self.get_command(message)

            print(command)
            if not command:
                # Command not found
                return

            p = self.check_perms(message, command)
            if p == 0:
                # Not enough permissions
                logger.info("{message.author} does not have enough permission to execute {command}.")
                await message.channel.send(embed=discord.Embed(title="You can't use this command!",
                                                               description="If you think this is an error, please \
                                                                           contact a staff member.",
                                                               colour=discord.Colour.red()))
                return

            # Check cooldown
            if p != 2:
                try:
                    cooldown_type = command['cooldown']
                    logger.debug(f"The cooldown type of command {command} has been identified as {cooldown_type}.")
                    if cooldown_type == 0:
                        time_since_last = time.time() - self.cooldown[message.author.id]['last']
                        if time_since_last < 10 and p <= 1:
                            too_fast = f"""You are sending commands too fast!"
                            Please wait {round(10-time_since_last,2)} seconds before trying again."""
                            logger.info(f"{message.author} is sending commands too fast.")
                            await message.channel.send(embed=discord.Embed(title="Please chill!",
                                                                           description=too_fast,
                                                                           colour=discord.Colour.orange()))
                            # Sending commands too fast removes points
                            self.tracker.remove_points(message.guild.id, message.author.id, 15)
                            return
                        
                        self.cooldown[message.author.id]['last'] = time.time()
                    else:
                        try:
                            time_since_last = time.time() - self.cooldown[message.author.id][command['commonname']]
                            if time_since_last < cooldown_type:
                                logger.info(f"{message.author} is sending the command {command} too fast.")
                                too_fast = f"You are sending commands too fast!\n\
                                Please wait {sec_to_time(cooldown_type - time_since_last, short=False)} before retrying"
                                await message.channel.send(embed=discord.Embed(title="Please chill!",
                                                                               description=too_fast,
                                                                               colour=discord.Colour.orange()))
                                # Sending commands too fast removes points
                                self.tracker.remove_points(message.guild.id, message.author.id, 15)
                                return
                        except KeyError:
                            # Setup cooldown for cmd specific
                            self.cooldown[message.author.id] = {command['commonname']: time.time()}
                except KeyError:
                    # Since bot restart, the author has not sent any commands! So no cooldown, yay!
                    self.cooldown[message.author.id] = {'last': time.time()}
            
            # Find command
            try:
                # Result should return dict containing status
                # 0 = good exec
                # 1 = good exec, do something now
                if command['namespace'] is None:
                    result = await eval(f"self.{command['exec']}(message)")
                else:
                    result = await eval(f"self.listeners['{command['namespace']}'].{command['exec']}(message)")

                if not result:
                    return
                if result['status'] == 1:
                    if 'add' in result:
                        if result['add'] == 'scroll':
                            for r in ('⏪', '◀', '▶', '⏩', chr(128256)):
                                await result['msg'].add_reaction(r)
                            await result['msg'].edit(**result['obj'].msgget())
                            self.scroll.append([result['msg'], message.author.id, result['obj'], time.time()])

            except Exception as e:
                raise e
            return

    async def on_reaction(self, reaction, user):
        # Handling reactions by checking if it is looking for one.
        if user.bot:
            return
        if user == self.client.user:
            return

        # Waiting on another request
        while self.status != 1:
            await asyncio.sleep(0.2)

        self.status = 3
        await self.proc_reaction(reaction, user)
        self.status = 1

    async def proc_reaction(self, reaction, user):
        logger.debug("Recieved reaction {reaction.emoji} to message {reaction.message.id} by user {user}.")
        """Process each reaction to see if they should trigger anything/"""

        # Conditions
        conditionals = self.settingsmanager.server_get(reaction.message.guild.id, 'conditional')
        for condition, match, position, result in conditionals:
            # Condition - type of condition such as reaction and message
            # Match - what to match the object to
            # Position - the position of the object
            if condition == 'message':
                if match == reaction.message.content and position == reaction.message.channel.id:
                    await result

        # Scroll
        for i in range(len(self.scroll)):
            msg, uid, s, timestamp = self.scroll[i]
            if msg.id != reaction.message.id or uid != user.id:
                continue
            if reaction.emoji == '⏪':
                t = await s.rewind()
            elif reaction.emoji == '⏩':
                t = await s.fast_forward()
            elif reaction.emoji == '◀':
                t = await s.prev()
            elif reaction.emoji == '▶':
                t = await s.next()
            elif ord(reaction.emoji) == 128256:  # Shuffle, but the emoji is weirdly utf-32
                try:
                    t = await s.random()
                except AttributeError:
                    continue
            else:
                continue
            self.scroll[i][3] = time.time()
            if t != -1:
                # T returns a dictionary, so hey, why not use **?
                await reaction.message.edit(**t)
            await reaction.remove(user)
            return

        # Expand
        for i in range(len(self.expand)-1, -1, -1):
            msg, uid, s, timestamp = self.expand[i]
            if msg.id != reaction.message.id or uid != user.id:
                continue
            if reaction.emoji == '⬇️':
                t = s.long
            else:
                continue
            await reaction.message.edit(embed=t)
            await reaction.remove(user)
            await reaction.remove(self.client.user)
            self.expand.pop(i)
            return

        # Verify
        for i in range(len(self.verifyreact)-1, -1, -1):
            msg, uid, s, timestamp = self.verifyreact[i]
            if msg.id != reaction.message.id or uid != user.id:
                continue
            if reaction.emoji != '<a:animated_check:717397008922443846>':
                await reaction.message.edit(embed=s.success)
                verifiedrole = self.settingsmanager.server_get(reaction.message.guild.id, 'verifiedrole')
                roleobj = discord.Object(verifiedrole)
                await user.add_roles(roleobj)
                try:
                    await reaction.message.delete()
                except discord.NotFound:
                    pass
                self.verifyreact.pop(i)
            else:
                await reaction.message.edit(embed=s.fail)
                self.verifyreact.pop(i)
            return
        return

# Commands

    async def stop(self, message):
        """Stops the bot"""
        logger.warning("{message.author} is running the shutdown command.")
        if message.author.id in (523717630972919809, 223085013258731521):
            if self.stopcounter == 0:
                self.stopcounter += 1
                await message.channel.send("Are you sure you want to stop the bot?\n\
- Run the command again to confirm.\n\
- Run `at!nevermind` (change prefix accordingly) to reset the counter.")
                return
            logger.critical("Bot shutdown initiated.")
            self.status = -1
            await message.channel.send("Bot shutting down.")
            await self.garbo
            self.client.loop.stop()
            sys.exit()

    async def nevermind(self, message):
        """Resets the stop counter"""
        if message.author.id in (523717630972919809, 223085013258731521):
            self.stopcounter = 0
            await message.channel.send("Stop counter reset.")

    async def CMD_eval(self, message: discord.Message) -> None:
        logger.warning("{message.author} is trying to evaluate something.")
        if message.author.id != 523717630972919809:
            await message.channel.send("You don't have permission to do this!")
            return
        thingtodo = message.content[len(message.content.split(' ')[0])+1:]
        await message.channel.send(eval(thingtodo))
        return

    async def CMD_exec(self, message: discord.Message) -> None:
        logger.warning("{message.author} is trying to execute something.")
        if message.author.id == 523717630972919809:
            args = message.content.split(' ')
            stmt = message.content[len(args[0])+1:]
            await message.channel.send(f"Executing statement {stmt}")
            try:
                await message.channel.send(exec(stmt))
            except discord.errors.HTTPException:
                await message.channel.send("There is no return value.")

    async def temp(self, message):
        """Temporary testing command"""
        if message.author.id != 523717630972919809:
            await message.channel.send("This temporary is *temporary* for a reason!")
            return
        return
#        t0 = time.perf_counter()
#        print(message.content[len(message.content.split(' ')[0])+1:])
#        errors = self.your_youre_check.check(message.content[len(message.content.split(' ')[0])+1:])
#        await message.channel.send(errors)
#        t1 = time.perf_counter()
#        await message.channel.send(f'Time taken: {t1-t0}')
        return

        pages = ['1', '2', '3', '4']
        p = PagedResponse("Test", pages)
        msg = await message.channel.send(embed=p.embed)
        for r in ('⏪', '◀', '▶', '⏩'):
            await msg.add_reaction(r)
        self.scroll.append([msg, message.author.id, p, time.time()])
        return

    # Minecraft Server Connection

    async def CMD_minecraft(self, message):
        args = message.content.split(' ')
        if message.author.id != 523717630972919809:
            await message.channel.send("This command is in development, therefore not enabled.")
            return

        if len(args) == 1:
            pfx = self.settingsmanager.server_get(message.guild.id, 'prefix')
            await message.channel.send(f"This module is for interfacing with Minecraft servers.\n\
Please specify a subcommand, or use the `{pfx}help minecraft` command to learn more.")
            return

        await self.mcinterface.proccommand(message, args[1], args[2:])

    # Point commands

    async def CMD_points(self, message):
        perms = self.get_perms(message)
        args = message.content.split(' ')
        userid = message.author.id
        username = str(message.author)
        try:
            serverid = message.guild.id
        except AttributeError:
            await message.channel.send("This command can only be used in servers!")
            return
        # Only bot owner can query other users, add or remove points.
        # The bot owner does not have a cooldown anyway :shrug:
        if len(args) >= 2:
            subcmd = args[1]
            # Leaderboard
            if subcmd in ('top', 'best'):
                leaderboard = self.tracker.getlb(serverid)
                desc = '```yaml\n'
                for i, pkg in enumerate(leaderboard[:min(10, len(leaderboard))]):
                    userid, points = pkg
                    user = self.client.get_user(userid)
                    if not user:
                        user = self.client.fetch_user(userid)
                    desc += f"{i+1}: {user.name}{(32-len(user.name))*' '}- {points}\n"
                desc += '```'
                embed = discord.Embed(title="Points Leaderboard", description=desc)
                await message.channel.send(embed=embed)
                return

            # A help message yay
            if subcmd in ('h', 'help'):
                embed = discord.Embed(title="Points system",
                                      description="""The points system is designed to reward users that are active.
Points are gained passively by talking.
 - Contributing to the conversation awards more points.
Points are removed when
 - Using this command to check the amount of points you have
 - Spamming
 - Cat walking over keyboard
""",
                                      colour=discord.Colour.magenta())
                await message.channel.send(embed=embed)

            # From this point on, these functions are inaccessible by the general user.
            if message.author.id != 523717630972919809:
                await message.channel.send("Hey, you can't do this!")
                return
            if subcmd in ('get', 'query', 'g', 'q'):
                # {prefix}points query <userid/snowflake>
                try:
                    if args[2].startswith('<@!'):
                        userid = int(args[2][3:-1])
                    else:
                        userid = int(args[2])
                except ValueError:
                    await message.channel.send("I can't figure out whose points you are trying to get!")
                    return
                username = message.guild.get_member(userid)
                if username is None:
                    username = message.guild.fetch_member(userid)
            elif subcmd in ('set',):
                # {prefix}points set user pts
                try:
                    userid, pts = args[2:4]
                    logger.info(f"Bot owner modified {userid}'s points to {pts}.")
                    self.tracker.set_points(serverid, int(userid), int(pts))
                    await message.channel.send("Points successfully changed.")
                    return
                except Exception as e:
                    await message.channel.send(f"Something went wrong!\n{e}")
                    return
                

        # Get points and apply penalty of random points between 69 and 100
        # Bot owner, for testing, has no penalty!
        if perms != 5:
            self.tracker.remove_points(serverid, userid, random.randint(69, 150))
        points = self.tracker.get_points(serverid, userid)

        # Send message
        # Experimental cooldown reduction: {round(10*math.log(points,10)-3,1)}%
        # Only after you gain 1,000 points
        if points < 1000:
            embed = discord.Embed(title=f"{username}'s points",
                                  colour=discord.Colour.orange(),
                                  description=f"Current points: {points}")
        else:
            embed = discord.Embed(title=f"{username}'s points",
                                  colour=discord.Colour.green(),
                                  description=f"""Current points: {points}
Cooldown reduction: {round(15*(math.log(points,10)-2.5),2)}%
\\*This is a privilege. It is subject to change, and may be disabled at bot owner's discretion.""")

        if perms != 5:
            embed.set_footer(text="Each time you check your points, you lose some random amount!")
        else:
            embed.set_footer(text="No penalty was applied. Bot owner has no cooldown anyway xD")
        await message.channel.send(embed=embed)

    # General functions

    async def CMD_about(self, message):
        desc = f"""Originally developed for the Atlantica Guild in Hypixel Skyblock.
Active in {len(self.client.guilds)} servers.

Made by StarGazingHomies#0001, hosted by CVFhyum#0001.
"""
        embed = discord.Embed(title=f"Info about StarGazingBot", description=desc, colour=discord.Colour.purple())
        embed.set_footer(text=self.version)
        await message.channel.send(embed=embed)

    async def CMD_status(self, message):
        args = message.content.split(' ')
        if len(args) == 1 or args[1] == 'get':
            with open(os.path.join(os.getcwd(), 'TODO.txt'), 'r') as fin:
                statusmsg = fin.read()
            embed = discord.Embed(title=f"Status", description=statusmsg, colour=discord.Colour.orange())
            version = self.settingsmanager.cfg['version']
            embed.set_footer(text=f"Running version {version}.")
            await message.channel.send(embed=embed)
        elif args[1] == 'set' and message.author.id == 523717630972919809:
            restofmsg = message.content[len(args[0])+5:]
            with open(os.path.join(os.getcwd(), 'TODO.txt'), 'w') as fout:
                fout.write(restofmsg)
            await message.channel.send(f"Status changed to:\n```{restofmsg}\n```")
        else:
            await message.channel.send("What do you want to do with the status? Catch it in 4k?")

    async def CMD_invite(self, message):
        await message.channel.send("Contact StarGazingHomies#0001 if you want to invite this bot to your server!")

    async def CMD_latency(self, message):
        latency = self.client.latency
        await message.channel.send(f"Discord WebSocket protocol latency: {round(latency*1000,2)}ms")

    async def CMD_help(self, message):
        footer = self.version
        args = message.content.split(' ')
        if len(args) >= 2:

            if message.guild is None:
                prefix = 'star!'
            else:
                prefix = self.settingsmanager.server_get(message.guild.id, 'prefix')
        
            try:
                # Get the command
                command = self.get_command(args[1])
                # Special help message for asking for help using help xD
                if command['commonname'] == "help":
                    await message.channel.send("I wonder what the help command does... wait a minute")
                    return

                # Read the help file
                if command['namespace'] is None:
                    with open(os.path.join(self.helppath, f'{commonname}.txt'), 'r') as fin:
                        helpmsg = fin.read()
                else:
                    with open(os.path.join(self.helppath, command['namespace'], f'{commonname}.txt'), 'r') as fin:
                        helpmsg = fin.read()

                # Construct and send message
                embed = discord.Embed(title=f"Info about {commonname}",
                                      description=helpmsg.format(prefix=prefix),
                                      colour=discord.Colour.blue())
                embed.set_footer(text=footer)
                await message.channel.send(embed=embed)
            except KeyError:
                embed = discord.Embed(title="Command not found",
                                      description="Please check your command for spelling mistakes!",
                                      colour=discord.Colour.orange())
                embed.set_footer(text="If the issue persists, please report it.")
                await message.channel.send(embed=embed)

            return  
        else:
            # Sorting based on category, only add if permissions allow
            perms = self.get_perms(message)

            if message.guild is None:
                # DM commands
                prefix = 'star!'
            else:
                prefix = self.settingsmanager.server_get(message.guild.id, 'prefix')

            categories = {}
            for command, ctgy in CATEGORYMAP.items():
                cmdinfo = self.get_command(command)
                if cmdinfo is None:
                    continue
                perm = cmdinfo['permission']
                if perms < perm:
                    continue
                if ctgy == 'WIP' and perms < 5:
                    continue
                try:
                    categories[ctgy].append(command)
                except KeyError:
                    categories[ctgy] = [command]
            # Embed construction
            title = "Commands List "
            desc = f"For more information about a command, use ``{prefix}help <command>``\nFor example: ``{prefix}help apply``"
            embed = discord.Embed(title=title, description=desc, colour=discord.Colour.blue())
            for ctgy, cmdlist in categories.items():
                fielddesc = ''
                for cmd in cmdlist:
                    fielddesc += f'``{cmd}``, '
                fielddesc = fielddesc[:-2]
                embed.add_field(name=ctgy, value=fielddesc, inline=False)
            await message.channel.send(embed=embed)
            mentalhealth = """If you need help, please seek out the help of a professional in your area.
[International List of Crisis Hotlines](https://www.reddit.com/r/SuicideWatch/wiki/hotlines)"""
            embed2 = discord.Embed(title="This is not a mental health bot!", colour=discord.Colour.red(),
                                   description=mentalhealth)
            await message.channel.send(embed=embed2)
    # Fun

    async def CMD_roll(self, message):
        try:
            result, rolls = rolldice(message.content[len(message.content.split(' ')[0])+1:])
            messagecontent = f"Result: {result}\n"
            for dice, allr, total in rolls:
                formattedrolllist = ''
                for individualr in allr:
                    formattedrolllist += f'{individualr}+'
                messagecontent += f"{dice}{(10-len(str(dice)))*' '}- {total} = {formattedrolllist[:-1]}\n"
            await message.channel.send(messagecontent)
        except Exception as e:
            await message.channel.send(f"An exception occured: {type(e).__name__}.\nCheck if you entered everything correctly!")

    # Settings

    async def CMD_user_settings(self, message):
        # User Settings
        args = message.content.split(' ')
        if len(args) >= 3:
            # Specific setting
            pass
        if len(args) == 2:
            # Query specific setting
            pass
        if len(args) == 1:
            # Generate pages
            pass

    async def CMD_server_settings(self, message):
        #Server Settings (config)

        args = message.content.split(' ')
        if len(args) >= 3:
            #Specific setting
            setting = args[1].lower()
            value = args[2]
            prefix = self.settingsmanager.server_get(message.guild.id, 'prefix')

            #Try to convert to None
            if value.lower() == 'none':
                value = None
            #Try to convert to bool
            elif value.lower() in ('n','no','false'):
                value = False
            elif value.lower() in ('y','yes','true'):
                value = True
            #Handles people that use mentions instead of IDs >:(((
            elif value.startswith('<'):
                nv = 0
                for char in value:
                    if 48 <= ord(char) <= 57:
                        nv *= 10
                        nv += ord(char) - 48
                value = nv
            #Try to convert value to int
            else:
                try:
                    value = int(value)
                except ValueError:
                    pass

            result = await self.settingsmanager.server_edit(message.guild, setting, value)

            #Result handling
            if result == -1:
                await message.channel.send("No matching setting was found.")
            elif result == -2:
                await message.channel.send("Editing your server's ID is not allowed!")
            elif result == -3:
                await message.channel.send("The provided value is not the right type!")
            elif result == -4:
                await message.channel.send(f"To edit conditionals, please use the `{prefix}conditional` command!")
            elif result == -5:
                await message.channel.send(f"To disable commands, please use the `{prefix}enable` and `{prefix}disable` commands!")
            else:
                await message.channel.send(f"The setting {setting} is changed to {value}.")

        elif len(args) == 2:
            #Get help message
            setting = args[1]
            try:
                helpmsg = self.settingsmanager.help_get(setting)
            except FileNotFoundError:
                await message.channel.send("Such a setting does not exist!")
                return

            #Generate embed and send
            prefix = self.settingsmanager.server_get(message.guild.id, 'prefix')
            embed = discord.Embed(title=setting, description=helpmsg.format(prefix=prefix))
            await message.channel.send(embed=embed)
            return

        elif len(args) == 1:
            #Generate pages when there are more settings. Right now, it isn't necessary.
            settings = self.settingsmanager.server_get(message.guild.id)
            embed = discord.Embed(title="Server settings",colour=discord.Colour.purple())
            for setting, val in settings.items():
                if setting in ('id'):
                    continue
#                capitalizedsetting = setting[0].upper() + setting[1:].lower()
                embed.add_field(name=setting, value=str(val), inline=False)
            await message.channel.send(embed=embed)

    async def CMD_prefix(self, message):
        #Alias to {prefix}settings prefix <prefix>
        pfx = message.content[len(message.content.split(' ')[0])+1:]    #Stuff after first space
        if ' ' in pfx:
            await message.channel.send("Spaces can't be in the prefix!")
            return
        for char in pfx:
            if ord(char) >= 128:
                await message.channel.send("Only characters, numbers, and common punctuation are available as prefixes.")
                return
        rtrn = self.settingsmanager.server_edit(message.guild.id, 'prefix', pfx)
        await message.channel.send("Prefix changed.")

    async def CMD_conditional(self, message):
        #Guided.

        #Current types:
        #reaction {message:msg, reaction:rctn}
        #message {channel:chnl, message:msg}
        pass

    async def CMD_perms(self, message):
        perms = self.get_perms(message)
        if perms == 5:
            await message.channel.send("You are a **Bot Owner** and have access to all commands.")
        elif perms == 4:
            await message.channel.send("You are a **Bot Tester** and have access to normal commands and in-development commands.")
        elif perms == 3:
            await message.channel.send("You are a **Server Owner** and have access to most commands. (`at!settings server` but not `at!stop`)")
        elif perms == 2:
            await message.channel.send("You are a **Server Staff** and have access to most commands. (`at!move` but not `at!settings`)")
        elif perms == 1:
            await message.channel.send("You are a **Member** and have access to non-moderation commands.")
        else:
            msg = await message.channel.send("Something went wrong while getting your permissions. Here, have a cookie! 🍪")
            await msg.add_reaction("🍪")

    async def CMD_say(self, message):
        #Permission - staff
        if len(message.content) - len(message.content.split(' ')[0]) - 1 <= 0:
            await message.channel.send("Please tell me something to say!")
            return
        embed = discord.Embed(description=message.content[len(message.content.split(' ')[0])+1:], colour = discord.Colour.random())
        await message.channel.send(embed=embed)
        try:
            await message.delete()
        except discord.errors.NotFound:
            #Message not found - maybe it was already deleted
            pass

    async def CMD_echo(self, message):
        #Permission - staff

        #Construct fake message
        


        #Old
        #-d anywhere in message --> do not delete original message
        if len(message.content) - len(message.content.split(' ')[0]) - 1 <= 0:
            await message.channel.send("Please tell me something to say!")
            return
        delete = True
        msg = message.content[len(message.content.split(' ')[0])+1:]
        if "-d" in message.content:
            delete = False
            msg = msg.replace('-d','')
        await message.channel.send(msg)

        if delete:
            try:
                await message.delete()
            except discord.errors.NotFound:
                #Message not found - maybe it was already deleted
                pass

    async def CMD_report(self, message):
        #Still not done, but it will do for now
        reportcontent = message.content[len(message.content.split(' ')[0])+1:]+'\n'
        if reportcontent == '\n':
            await message.channel.send("Please specify what to report!")
            return
        embed = discord.Embed(title="Bug Report", colour=discord.Colour.orange(),
                              description=f"""
**[User]**
{message.author.name}#{message.author.discriminator} (ID: {message.author.id})

**[Message]**
[here]({message.jump_url})

**[Content]**
{reportcontent}""")
        await self.owner.send(embed=embed)
        await message.channel.send("Thanks for reporting!\nNote: to help improve the bot, your most recent interactions with the bot are recorded.")
        return

    async def CMD_pingowner(self, message):
        #Mainly a test command for command-specific cooldowns!
        #Owner can request multiple pings
        if message.author.id == 523717630972919809:
            args = message.content.split(' ')
            if len(args) >= 2:
                t = int(args[1])
            else:
                t = 1
        else:
            t = 1
        guild = self.client.get_guild(906231970651070504)
        channel = guild.get_channel(910878442239713280)
        for i in range(t):
            await channel.send("<@!523717630972919809>")
            await asyncio.sleep(1.5)

        await message.channel.send("Done!")

    async def CMD_nick(self, message):
        """
Nicks a certain user with the provided nickname.
"""
        # (prefix)!nick <nickname> [user]
        args = message.content.split(' ')[1:]
        try:
            nick = args[0]
        except IndexError:
            await message.channel.send("Please specify a nickname.")
            return
        if len(nick) > 32:
            await message.channel.send("That's too long for a nickname!")
            return
        try:
            try:
                user = args[1]
                if user.startswith('<@!'):
                    user = int(user[3:-1])
                else:
                    user = int(user)
                member = await message.guild.fetch_member(user)
                if nick=='reset':
                    nick = member.name
                await member.edit(nick=nick)
            except IndexError:
                if nick=='reset':
                    nick = message.author.name
                await message.author.edit(nick=nick)
            await message.channel.send("Nickname changed.")
        except discord.errors.Forbidden:   
            await message.channel.send("Insufficient permissions.")

    async def CMD_move(self, message):
        """
Moves a certain user.
"""
        # (prefix)!nick <nickname> [user]
        args = message.content.split(' ')[1:]
        try:
            user = args[0]
            if user.startswith('<@!'):
                user = int(user[3:-1])
            else:
                user = int(user)
            member = await message.guild.fetch_member(user)
        except IndexError:
            await message.channel.send("Please specify who to move!")
            return
        except discord.errors.NotFound:
            await message.channel.send("Unknown member.")
            return
        
        try:
            channelid = args[1]
            if channelid.startswith('<#'):
                channelid = int(channelid[2:-1])
            else:
                channelid = int(channelid)
            channel = message.guild.get_channel(channelid)
            if channel == None:
                channels = await message.guild.fetch_channels()
                for tc in channels:
                    if tc.id == channelid:
                        channel = tc
        except IndexError:
            # Disconnect
            channel = None

        try:
            await member.move_to(channel, reason="Bot owner command")
        except discord.errors.Forbidden:   
            await message.channel.send("Insufficient permissions.")

    async def CMD_clean(self, message):
        """Cleans up messages in a channel"""
        args = message.content.split(' ')[1:]

        #Amount of messages
        try:
            amount = int(args[0])
        except ValueError:
            await message.channel.send(f"How much message is {args[0]}?")
            return
        except IndexError:
            await message.channel.send("Please specify how many messages to delete.")
            return

        #User specific
        try:
            if args[1].startswith('<@!'):
                userid = int(args[1][3:-1])
            else:
                userid = int(args[1])
        except IndexError:  # There is no 2nd argument. Fine.
            userid = None
        except ValueError:
            await message.channel.send(f"Who is {args[1]}?\nPro tip: Use the user's ID to avoid of mentioning them!")
            return

        if userid == self.client.user.id:
            bulk = False
        else:
            bulk = True

        # Deletion
        try:
            if userid:
                actualamount = await message.channel.purge(limit=amount,
                                                           bulk=bulk,
                                                           check=lambda tmsg: tmsg.author.id == userid)
            else:
                actualamount = await message.channel.purge(limit=amount, bulk=bulk)
        except discord.errors.Forbidden:
            await message.channel.send("I do not have the permissions to do so!")
            return
        except discord.errors.HTTPException:
            await message.channel.send("Purging failed due to a network issue. Perhaps try again later?")
            return

        #Send and delete the confirmation that messages are gone
        msg = await message.channel.send(f"Cleaned up {len(actualamount)} messages.")
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except discord.errors.NotFound:
            pass

    #--------------------------------------------------------------------    User-Staff interactions... i think?    --------------------------------------------------------------------

    async def CMD_verify(self, message):
        try:
            await message.delete()
        except Exception:
            pass
        settings = self.settingsmanager.server_get(message.guild.id)
        if not settings['verify']:
            await message.channel.send("Verification is not enabled on this server. Please check with a server staff on which bot you should use to verify.")
            return

        args = message.content.split(' ')
        if len(args) < 2 or len(args) > 2:
            await message.channel.send("Please indicate a valid username!")
            return

        username = args[1]
        player = Player(self.reqsession, username)
        result = await player.parse_general(self.reqsession)
        if player.discord is None:
            await message.channel.send("Please check the pinned messages on how to link your Discord account!", delete_after=20)
            return
        if player.discord != f'{message.author.name}#{message.author.discriminator}':
            await message.channel.send(f"Your linked discord on Hypixel `{player.discord}` does not match your discord `{message.author.name}#{message.author.discriminator}`.", delete_after=20)
            await message.channel.send("Please check the pinned messages on how to link your Discord account!", delete_after=20)
            return

        verifyobj = VerifyResponse(message)
        rmsg = await message.channel.send(embed=verifyobj.wait)
        await rmsg.add_reaction('<a:animated_check:717397008922443846>')

        #Response proc
        self.verifyreact.append([rmsg, message.author.id, verifyobj, time.time()])
        return

    async def CMD_apply(self, message):

        #Check if apply is enabled
        settings = self.settingsmanager.server_get(message.guild.id)
        if settings['apply'] == False:
            await message.channel.send("Applications aren't enabled in this server! Perhaps you should use another bot?")

        try:
            ctgy = settings['applycategory']
            if isinstance(ctgy, int):
                ctgy = message.guild.get_channel(ctgy)
                if ctgy == None:
                    ctgy = message.guild.fetch_channel(ctgy)
        except KeyError:
            #Settings broken?
            ctgy = None

        #Channel construction
        Overwrites = {
            message.guild.default_role:
            discord.PermissionOverwrite(read_messages=False),
            message.author:
            discord.PermissionOverwrite(
                send_messages=True,
                view_channel=True,
                read_messages=True,
                add_reactions=True),
            message.guild.get_role(settings['staffrole']):
            discord.PermissionOverwrite(
                send_messages=True,
                view_channel=True,
                read_messages=True,
                add_reactions=True)      
        }
        if ctgy:
            channel = await message.guild.create_text_channel(name=f'@{message.author.name} application', overwrites=Overwrites, category=ctgy)
        else:
            channel = await message.guild.create_text_channel(name=f'@{message.author.name} application', overwrites=Overwrites)

        #Return message
        embed = discord.Embed(
            title=f"**Alright {message.author.name}, your application is set up**",
            description=
            f'Your application channel is here: <#{channel.id}>',
            colour=discord.Colour.blue())
        embed2 = discord.Embed(title = f"{message.author.name}'s application",
                               description = """Guild Application
You’re all set! Please wait patiently for a staff member to respond.
If you want to add any extra information, you can provide it here.""",
                               colour = discord.Colour.green())
        message2 = await message.channel.send(embed=embed, delete_after=10)
        message3 = await channel.send(f"<@&{settings['staffrole']}>", delete_after=1)

        #Application set up, in-channel message
        await channel.send(embed=embed2)

        #Displays weight of user
        try:
            identifier = message.author.nick.split('|')[-1].replace(' ','')
        except AttributeError:
            identifier = message.author.name
        await self.Skyblock_weightdisp(message.author, channel, identifier)

    async def CMD_suggest(self, message):
        # Not done!
        if message.author.id != 523717630972919809:
            return
        # Check if it is enabled
        settings = self.settingsmanager.server_get(message.guild.id)
        if not settings['suggest']:
            await message.channel.send("Suggestions aren't enabled in this server! Perhaps you should use another bot?")

        try:
            ctgy = settings['suggestcategory']
            if isinstance(ctgy, int):
                ctgy = message.guild.get_channel(ctgy)
                if ctgy == None:
                    ctgy = message.guild.fetch_channel(ctgy)
        except KeyError:
            # Settings broken?
            ctgy = None

        # Overwrites only work in Atlantica.
        Overwrites = {
            message.guild.default_role:
            discord.PermissionOverwrite(read_messages=False),
            message.author:
            discord.PermissionOverwrite(
                send_messages=True,
                view_channel=True,
                read_messages=True,
                add_reactions=True),
            message.guild.get_role(settings['staffrole']):
            discord.PermissionOverwrite(
                send_messages=True,
                view_channel=True,
                read_messages=True,
                add_reactions=True)      
        }
        if ctgy:
            channel = await message.guild.create_text_channel(name=f'@{message.author.name} application', overwrites=Overwrites, category=ctgy)
        else:
            channel = await message.guild.create_text_channel(name=f'@{message.author.name} application', overwrites=Overwrites)
        # Return message and channel construction
        embed = discord.Embed(
            title=f"**Please elaborate on your suggestion in the newly created channel!**",
            description=
            f'Your suggestion channel is <#{channel.id}>',
            colour=discord.Colour.blue())
        embed2 = discord.Embed(title = f"{message.author.name}'s suggestion",
                               description = """Please elaborate on your suggestion, and staff members will be provide feedback.""",
                               colour = discord.Colour.green())
        message2 = await message.channel.send(embed=embed, delete_after=10)
        message3 = await channel.send(f"<@&{settings['staffrole']}>", delete_after=1)

        # Application set up, in-channel message
        await channel.send(embed=embed2)

    # Skyblock functions

    async def CMD_uuid(self, message, limited=3):
        """Get the uuid of a Minecraft user"""
        args = message.content.split(' ')
        if len(args) >= 2:
            username = args[1]
        else:
            await message.channel.send("Please indicate a username to get the uuid of.")
            return
        kwargs = {}
        if len(args) >= 3 and message.author.id == 523717630972919809:
            for arg in args[2:]:
                try:
                    a, b = arg.split('=')
                    kwargs[a] = b
                except TypeError:
                    await message.channel.send(f"Error in keyword argument {arg}.")
        result = await mojangapi.getuuid(self.reqsession, username, **kwargs)
        if not result:
            await message.channel.send("An error occured. Please try again later.")
        await message.channel.send(f"The uuid of {username} is {result}.")
        return

    async def CMD_username(self, message, limited=3):
        """Get the username of a Minecraft user."""
        args = message.content.split(' ')
        if len(args) >= 2:
            uuid = args[1]
        else:
            await message.channel.send("Please indicate a uuid to get the username of.")
            return
        result = await mojangapi.getusername(self.reqsession, uuid)
        if not result:
            await message.channel.send("An error occured. Please try again later.")
        await message.channel.send(f"The username of {uuid} is {result}.")

    async def CMD_Skyblock_getstats(self, message, limited=3):
        """Returns all basic Skyblock stats, such as skills, slayers, and dungeon levels.
Usage: `at!getstats [username]`
Cooldown: 10s"""
        # Parse command
        args = message.content.split(' ')
        color = discord.Colour.blue()
        if len(args) >= 2:
            identifier = args[1]
        else:
            try:
                identifier = message.author.nick.split('|')[-1]
            except AttributeError:
                identifier = message.author.name

        #Hypixel API request
        player = Player(self.reqsession, identifier)
        result = await player.parse_skyblock(self.reqsession)

        #If no profile
        if result['status'] == -1:
            embed = discord.Embed(title=f"{player.username} has no skyblock profiles!", colour=discord.Colour.red())
            embed.set_footer(text="If you believe this is an error, please report.")
            await message.channel.send(embed=embed)
            return
        if result['status'] == -2:
            embed = discord.Embed(title=f"{identifier} does not exist!", colour=discord.Colour.red())
            embed.set_footer(text="If you believe this is an error, please report.")
            await message.channel.send(embed=embed)
            return

        t0 = time.perf_counter()
        #Generate return message
        return_msg = f"\n**Skill levels:**\n{player.username} has a skill average of **{player.skill_avg:.4}**```elm\n"
        short_return_msg = f"\n**Skill levels:**\n{player.username} has a skill average of **{player.skill_avg:.4}**\n"
        short_return_msg += f"**Slayer xp:** \n{player.username} has **{betternum(player.slayer_total)}** total slayer experience\n"
        short_return_msg += f"**Catacombs:**\n{player.username} has a catacombs level of **{round(player.dungeons['catacombs'].level,2)}**\n"
        #Skills
        for skill in SKYBLOCK_DICT["SKILLNAMES"]:
            lvl = player.skills[skill].level
            return_msg += f"{skill}{' '*(11-len(skill))}> {round(lvl, 2)}\n"
        #Slayer
        return_msg += f"```\n**Slayer xp:** \n{player.username} has **{betternum(player.slayer_total)}** total slayer experience\n```elm\n"
        for slayer in SKYBLOCK_DICT["SLAYERS"]:
            xp = player.slayers[slayer].exp
            return_msg += f"{slayer}{' '*(11-len(slayer))}> {betternum(xp)}\n"
        return_msg += "```\n**Dungeon levels:** \n```elm\n"
        #Dungeons
        for dungstat in SKYBLOCK_DICT["DUNGEONS"]:
            lvl = player.dungeons[dungstat].level
            return_msg += f"{dungstat}{' '*(11-len(dungstat))}> {round(lvl, 2)}\n"
        #Dungeon Classes
        for dungstat in SKYBLOCK_DICT["CLASSES"]:
            lvl = player.dungeons[dungstat].level
            return_msg += f"{dungstat}{' '*(11-len(dungstat))}> {round(lvl, 2)}\n"
        return_msg += "```"
        #Embeds
        shortembed = discord.Embed(title = player.username + "'s Stats", description=short_return_msg, color = color)
        shortembed.set_footer(text="React with ⬇️to show details")
        embed = discord.Embed(title = player.username + "'s Stats", description=return_msg, color = color)
        timeoutembed = discord.Embed(title = player.username + "'s Stats", description=short_return_msg, color = color)
        timeoutembed.set_footer(text="Timed Out")
        newmessage = await message.channel.send(embed=shortembed)
        await newmessage.add_reaction('⬇️')
        t1 = time.perf_counter()

        #Timing data for bot owner
        if message.author.id == 523717630972919809:
            await message.channel.send(f"The request to the Hypixel API took {result['get']} seconds.\nProcessing the data took {result['proc']} seconds.\nThe response message took {round(t1-t0,7)} seconds to generate and send.")

        #Reaction processing
        expobj = ExpandableResponse(shortembed, embed, timeoutembed)
        self.expand.append([newmessage, message.author.id, expobj, time.time()])
        return

    async def CMD_Skyblock_getweight(self, message, limited=3):
        """
Returns the weight of the given user.
message: discord.Message object"""
        #Parse command
        args = message.content.split(' ')
        if len(args) >= 2:
            identifier = args[1]
        else:
            try:
                identifier = message.author.nick.split('|')[-1].replace(' ','')
            except AttributeError:
                identifier = message.author.name

        await self.Skyblock_weightdisp(message.author, message.channel, identifier, timing = (message.author.id == 523717630972919809))

    async def Skyblock_weightdisp(self, author, channel, identifier, expanded=False, timing=False):
        color = discord.Colour.blue()
        #Hypixel API request
        player = Player(self.reqsession, identifier)
        result = await player.parse_all(self.reqsession)

        #If no profile
        if result['status'] == -1:
            embed = discord.Embed(title=f"{player.username} has no skyblock profiles!", colour=discord.Colour.red())
            embed.set_footer(text="If you believe this is an error, please report.")
            await channel.send(embed=embed)
            return
        if result['status'] == -2:
            embed = discord.Embed(title=f"{identifier} does not exist!", colour=discord.Colour.red())
            embed.set_footer(text="If you believe this is an error, please report.")
            await channel.send(embed=embed)
            return

        t0 = time.perf_counter()
        #Generate long msg
        return_msg = f"[{player.rank}] {player.username} has a weight of {round(player.totalweight,3)} ({round(player.weight[0],3)} + {round(player.weight[1],3)} overflow)\n\n**Skills weight:** \n```elm\n"
        short_return_msg = f"[{player.rank}] {player.username} has a weight of {round(player.totalweight,3)} ({round(player.weight[0],3)} + {round(player.weight[1],3)} overflow)"
        #Skills
        for skill in player.skills.values():
            weight = skill.weights
            lvl = round(skill.level,2)
            if weight[1] != 0:
                return_msg += f"{skill.type}{' '*(11-len(skill.type))}> lvl: {lvl}{' '*(8-len(str(lvl)))}> weight: {round(weight[0],2)} + {round(weight[1],2)} overflow\n"
            else:
                return_msg += f"{skill.type}{' '*(11-len(skill.type))}> lvl: {lvl}{' '*(8-len(str(lvl)))}> weight: {round(weight[0],2)}\n"
        #Slayers
        return_msg += "```\n**Slayer weight:** \n```elm\n"
        for slayer in player.slayers.values():
            weight = slayer.weights
            xp = slayer.exp
            if weight[1] != 0:
                return_msg += f"{slayer.type}{' '*(11-len(slayer.type))}> xp: {xp}{' '*(9-len(str(xp)))}> weight: {round(weight[0],2)} + {round(weight[1],2)} overflow\n"
            else:
                return_msg += f"{slayer.type}{' '*(11-len(slayer.type))}> xp: {xp}{' '*(9-len(str(xp)))}> weight: {round(weight[0],2)}\n"
        #Dungeons
        return_msg += "```\n**Dungeon weight:** \n```elm\n"
        for dungstat in player.dungeons.values():
            weight = dungstat.weights
            lvl = round(dungstat.level,2)
            if weight[1] != 0:
                return_msg += f"{dungstat.type}{' '*(11-len(dungstat.type))}> lvl: {lvl}{' '*(8-len(str(lvl)))}> weight: {round(weight[0],2)} + {round(weight[1],2)} overflow\n"
            else:
                return_msg += f"{dungstat.type}{' '*(11-len(dungstat.type))}> lvl: {lvl}{' '*(8-len(str(lvl)))}> weight: {round(weight[0],2)}\n"
        return_msg += "```"

        #discord.Embed objects for reaction
        shortembed = discord.Embed(title = player.username + "'s Weight", description=short_return_msg, color = color)
        shortembed.set_footer(text="React with ⬇️to show details")
        embed = discord.Embed(title = player.username + "'s Weight", description=return_msg, color = color)
        timeoutembed = discord.Embed(title = player.username + "'s Weight", description=short_return_msg, color = color,)
        timeoutembed.set_footer(text="Timed Out")
        t1 = time.perf_counter()

        #Timing data for bot owner
        if timing:
            await channel.send(f"The request to the Hypixel API took {result['get']} seconds.\nProcessing the data took {result['proc']} seconds.\nThe response message took {round(t1-t0,7)} seconds to generate and send.")


        #Reaction processing
        if expanded:
            await channel.send(embed=embed)
        else:
            newmessage = await channel.send(embed=shortembed)
            await newmessage.add_reaction('⬇️')
            expobj = ExpandableResponse(shortembed, embed, timeoutembed)
            self.expand.append([newmessage, author.id, expobj, time.time()])
        return

#------------------------------------------------------------------------    Skyblock GUILD/EVENT functions    ------------------------------------------------------------------------

    async def CMD_glbreturnmsg(self, channel, resp):
        #Skyblock:Guild Leaderboard - Return messages generation
        return_msg = '```yaml\n'
        totalweight = 0
        messages = []
        for i, memb in enumerate(resp):
            if memb[0] == 'DaddyCVFhyum':
                return_msg += f"{i+1}: DaddyCVFhyum lol what a loser\n"
            elif len(memb) == 3:
                return_msg += f"{i+1}: {memb[0]} - {memb[1]} ({memb[2]})\n"
                totalweight += memb[1]
            else:
                return_msg += f"{i+1}: {memb[0]} - {memb[1]}\n"
                totalweight += memb[1]

            if i%15==14:
                return_msg += '```'
                embed = discord.Embed(description = return_msg)
                messages.append( await channel.send(embed=embed) )
                await asyncio.sleep(0.3)
                return_msg = '```yaml\n'
        if return_msg != "```yaml\n":
            return_msg += '```'
            embed = discord.Embed(description = return_msg)
            messages.append( await channel.send(embed=embed) )
        averageembed = discord.Embed(title = "Average guild weight", description = f"```fix\nThe average guild weight is {totalweight/len(resp):.6}.\n```")
        messages.append( await channel.send(embed=averageembed) )
        return messages

    async def CMD_guildleaderboard(self, message):
        args = message.content.split(' ')
        if len(args) < 2:
            await message.channel.send("Please specify a guild.")
            return

        #API call
        guildname = args[1]
        guild = getguild(guildname)
        resp = await guild.getweights(self.reqsession)
        await self.CMD_glbreturnmsg(message.channel, resp)
        return

    async def CMD_Skyblock_glb_loop_command(self, message):
        """
        Message format: at!loopglb [start] <guild_name> <interval = 1h>
        """
        args = message.content.split(' ')
        subcommand = args[1]

        #Stop subcommand
        if subcommand == 'stop':
            self.glbtasks[message.guild.id]['status'] = -1
            await message.channel.send("The task should be stopping soon.")
            return

        #Handling arugments
        if len(args) < 3:
            await message.channel.send("Not enough arguments. at!loopglb start <guild name> [interval]")
            return
        guildname = args[2]
        try:
            time = timetosec(args[3])
        except IndexError:
            time = 3600
        if time < 1200:
            await message.channel.send("The interval is too short.")
            return

        #Check if there is another running task
        if message.guild.id in self.glbtasks.keys():
            await message.channel.send("Another task in progress in this server. Please stop the previous task with `at!stop` before starting this one.")
            return

        task = asyncio.create_task(self.Func_Skyblock_glb_loop_task(message.channel, guildname, time))
        self.glbtasks[message.guild.id] = {"status":0, "task":task}
        await message.channel.send("Task created.")

    async def Func_Skyblock_glb_loop_task(self, channel, guildname, interval):

        #Init
        lastupdate = time.time()
        msgtodelete = []
        guild = getguild(guildname)

        #Loop
        while self.glbtasks[channel.guild.id]['status'] == 0:
            resp = await guild.getweights(self.reqsession)
            for msg in msgtodelete:
                try:
                    await msg.delete()
                except:
                    pass
            msgtodelete = await self.CMD_glbreturnmsg(channel, resp)
            lastupdate = time.time()

            while self.glbtasks[channel.guild.id]['status'] == 0 and time.time() - lastupdate < interval:
                await asyncio.sleep(1)

        self.glbtasks.pop(channel.guild.id)
        await channel.send("Task exited")

    async def CMD_Skyblock_event(self, message):
        #subcommands: list, start, end, restart
        #defaults to list if not specified
        args = message.content.split(' ')
        if len(args)==1 or args[1] in ('list','l'):
            eventlist = self.eventmanager.list()
            message.channel.send(eventlist)
        
