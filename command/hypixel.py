import asyncio
import time

import aiohttp
import discord
import yaml

from modules.hypixel.player import Player
from modules.hypixel.guild import getguild
from structures.response import ExpandableResponse
from event import CLS_EventFileHandler as EventManager
from func import pretty_num, time_to_sec

SKYBLOCK_DICT = yaml.load(open("skyblock_constants.yaml", "r"), Loader=yaml.FullLoader)


class Listener:
    """Listener object for Hypixel (Skyblock) commands."""

    def __init__(self, session=None):
        if not session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))
        else:
            self.session = session

        self.glb_tasks = {}
        self.eventmanager = EventManager()

    async def CMD_Skyblock_getstats(self, message):
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

        # Hypixel API request
        player = Player(self.session, identifier)
        result = await player.parse_skyblock(self.session)

        # If no profile
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
        # Generate return message
        return_msg = f"\n**Skill levels:**\n{player.username} has a skill average of **{player.skill_avg:.4}**```elm\n"
        short_return_msg = f"\n**Skill levels:**\n{player.username} has a skill average of **{player.skill_avg:.4}**\n"
        short_return_msg += f"**Slayer xp:** \n{player.username} has **{pretty_num(player.slayer_total)}** total slayer experience\n"
        short_return_msg += f"**Catacombs:**\n{player.username} has a catacombs level of **{round(player.dungeons['catacombs'].level, 2)}**\n"
        # Skills
        for skill in SKYBLOCK_DICT["SKILLNAMES"]:
            lvl = player.skills[skill].level
            return_msg += f"{skill}{' ' * (11 - len(skill))}> {round(lvl, 2)}\n"
        # Slayer
        return_msg += f"```\n**Slayer xp:** \n{player.username} has **{pretty_num(player.slayer_total)}** total slayer experience\n```elm\n"
        for slayer in SKYBLOCK_DICT["SLAYERS"]:
            xp = player.slayers[slayer].exp
            return_msg += f"{slayer}{' ' * (11 - len(slayer))}> {pretty_num(xp)}\n"
        return_msg += "```\n**Dungeon levels:** \n```elm\n"
        # Dungeons
        for dungstat in SKYBLOCK_DICT["DUNGEONS"]:
            lvl = player.dungeons[dungstat].level
            return_msg += f"{dungstat}{' ' * (11 - len(dungstat))}> {round(lvl, 2)}\n"
        # Dungeon Classes
        for dungstat in SKYBLOCK_DICT["CLASSES"]:
            lvl = player.dungeons[dungstat].level
            return_msg += f"{dungstat}{' ' * (11 - len(dungstat))}> {round(lvl, 2)}\n"
        return_msg += "```"
        # Embeds
        short_embed = discord.Embed(title=player.username + "'s Stats", description=short_return_msg, color=color)
        short_embed.set_footer(text="React with ⬇️to show details")
        embed = discord.Embed(title=player.username + "'s Stats", description=return_msg, color=color)
        timeout_embed = discord.Embed(title=player.username + "'s Stats", description=short_return_msg, color=color)
        timeout_embed.set_footer(text="Timed Out")
        new_message = await message.channel.send(embed=short_embed)
        t1 = time.perf_counter()

        # Timing data for bot owner
        if message.author.id == 523717630972919809:
            await message.channel.send(
                f"The request to the Hypixel API took {result['get']} seconds.\nProcessing the data took {result['proc']} seconds.\nThe response message took {round(t1 - t0, 7)} seconds to generate and send.")

        # Reaction processing
        exp_obj = ExpandableResponse(short_embed, embed, timeout_embed)
        return {'status': 1, 'add': 'expand', 'msg': new_message, 'obj': exp_obj}

    async def CMD_Skyblock_getweight(self, message):
        """
Returns the weight of the given user.
message: discord.Message object"""
        # Parse command
        args = message.content.split(' ')
        if len(args) >= 2:
            identifier = args[1]
        else:
            try:
                identifier = message.author.nick.split('|')[-1].replace(' ', '')
            except AttributeError:
                identifier = message.author.name

        return await self.Skyblock_weightdisp(message.author, message.channel, identifier,
                                              timing=(message.author.id == 523717630972919809))

    async def Skyblock_weightdisp(self, author, channel, identifier, expanded=False, timing=False):
        color = discord.Colour.blue()
        # Hypixel API request
        player = Player(self.session, identifier)
        result = await player.parse_all(self.session)

        # If no profile
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
        # Generate long msg
        return_msg = f"[{player.rank}] {player.username} has a weight of {round(player.totalweight, 3)} ({round(player.weight[0], 3)} + {round(player.weight[1], 3)} overflow)\n\n**Skills weight:** \n```elm\n"
        short_return_msg = f"[{player.rank}] {player.username} has a weight of {round(player.totalweight, 3)} ({round(player.weight[0], 3)} + {round(player.weight[1], 3)} overflow)"
        # Skills
        for skill in player.skills.values():
            weight = skill.weights
            lvl = round(skill.level, 2)
            if weight[1] != 0:
                return_msg += f"{skill.type}{' ' * (11 - len(skill.type))}> lvl: {lvl}{' ' * (8 - len(str(lvl)))}> weight: {round(weight[0], 2)} + {round(weight[1], 2)} overflow\n"
            else:
                return_msg += f"{skill.type}{' ' * (11 - len(skill.type))}> lvl: {lvl}{' ' * (8 - len(str(lvl)))}> weight: {round(weight[0], 2)}\n"
        # Slayers
        return_msg += "```\n**Slayer weight:** \n```elm\n"
        for slayer in player.slayers.values():
            weight = slayer.weights
            xp = slayer.exp
            if weight[1] != 0:
                return_msg += f"{slayer.type}{' ' * (11 - len(slayer.type))}> xp: {xp}{' ' * (9 - len(str(xp)))}> weight: {round(weight[0], 2)} + {round(weight[1], 2)} overflow\n"
            else:
                return_msg += f"{slayer.type}{' ' * (11 - len(slayer.type))}> xp: {xp}{' ' * (9 - len(str(xp)))}> weight: {round(weight[0], 2)}\n"
        # Dungeons
        return_msg += "```\n**Dungeon weight:** \n```elm\n"
        for dungstat in player.dungeons.values():
            weight = dungstat.weights
            lvl = round(dungstat.level, 2)
            if weight[1] != 0:
                return_msg += f"{dungstat.type}{' ' * (11 - len(dungstat.type))}> lvl: {lvl}{' ' * (8 - len(str(lvl)))}> weight: {round(weight[0], 2)} + {round(weight[1], 2)} overflow\n"
            else:
                return_msg += f"{dungstat.type}{' ' * (11 - len(dungstat.type))}> lvl: {lvl}{' ' * (8 - len(str(lvl)))}> weight: {round(weight[0], 2)}\n"
        return_msg += "```"

        # discord.Embed objects for reaction
        short_embed = discord.Embed(title=player.username + "'s Weight", description=short_return_msg, color=color)
        short_embed.set_footer(text="React with ⬇️to show details")
        embed = discord.Embed(title=player.username + "'s Weight", description=return_msg, color=color)
        timeout_embed = discord.Embed(title=player.username + "'s Weight", description=short_return_msg, color=color, )
        timeout_embed.set_footer(text="Timed Out")
        t1 = time.perf_counter()

        # Timing data for bot owner
        if timing:
            await channel.send(
                f"The request to the Hypixel API took {result['get']} seconds.\nProcessing the data took {result['proc']} seconds.\nThe response message took {round(t1 - t0, 7)} seconds to generate and send.")

        # Reaction processing
        if expanded:
            await channel.send(embed=embed)
            return {'status': 0}
        else:
            new_message = await channel.send(embed=short_embed)
            await new_message.add_reaction('⬇️')
            exp_obj = ExpandableResponse(new_message, author, short_embed, embed, timeout_embed)
        return {'status': 1, 'add': 'response', 'obj': exp_obj}

    # Skyblock GUILD/EVENT functions

    @staticmethod
    async def Func_glb_return_msg(channel, resp):
        # Skyblock:Guild Leaderboard - Return messages generation
        return_msg = '```yaml\n'
        total_weight = 0
        messages = []
        for i, memb in enumerate(resp):
            if memb[0] == 'DaddyCVFhyum':
                return_msg += f"{i + 1}: DaddyCVFhyum lol what a loser\n"
            elif len(memb) == 3:
                return_msg += f"{i + 1}: {memb[0]} - {memb[1]} ({memb[2]})\n"
                total_weight += memb[1]
            else:
                return_msg += f"{i + 1}: {memb[0]} - {memb[1]}\n"
                total_weight += memb[1]

            if i % 15 == 14:
                return_msg += '```'
                embed = discord.Embed(description=return_msg)
                messages.append(await channel.send(embed=embed))
                await asyncio.sleep(0.3)
                return_msg = '```yaml\n'
        if return_msg != "```yaml\n":
            return_msg += '```'
            embed = discord.Embed(description=return_msg)
            messages.append(await channel.send(embed=embed))
        average_embed_description = f"```fix\nThe average guild weight is {total_weight / len(resp):.6}.\n```"
        average_embed = discord.Embed(title="Average guild weight", description=average_embed_description)
        messages.append(await channel.send(embed=average_embed))
        return messages

    async def CMD_guildleaderboard(self, message):
        args = message.content.split(' ')
        if len(args) < 2:
            await message.channel.send("Please specify a guild.")
            return

        # API call
        guild_name = args[1]
        guild = getguild(guild_name)
        resp = await guild.getweights(self.session)
        await self.Func_glb_return_msg(message.channel, resp)
        return

    async def CMD_Skyblock_glb_loop_command(self, message):
        """
        Message format: at!loopglb [start] <guild_name> <interval = 1h>
        """
        args = message.content.split(' ')
        subcommand = args[1]

        # Stop subcommand
        if subcommand == 'stop':
            self.glb_tasks[message.guild.id]['status'] = -1
            await message.channel.send("The task should be stopping soon.")
            return

        # Handling arguments
        if len(args) < 3:
            await message.channel.send("Not enough arguments. at!loopglb start <guild name> [interval]")
            return
        guild_name = args[2]
        try:
            time_str = time_to_sec(args[3])
        except IndexError:
            time_str = 3600
        if time_str < 1200:
            await message.channel.send("The interval is too short.")
            return

        # Check if there is another running task
        if message.guild.id in self.glb_tasks.keys():
            await message.channel.send(
                "Another task in progress in this server.\
                 Please stop the previous task with `at!stop` before starting this one.")
            return

        task = asyncio.create_task(self.Func_Skyblock_glb_loop_task(message.channel, guild_name, time_str))
        self.glb_tasks[message.guild.id] = {"status": 0, "task": task}
        await message.channel.send("Task created.")

    async def Func_Skyblock_glb_loop_task(self, channel, guildname, interval):

        # Init
        msg_to_delete = []
        guild = getguild(guildname)

        # Loop
        while self.glb_tasks[channel.guild.id]['status'] == 0:
            resp = await guild.getweights(self.session)
            for msg in msg_to_delete:
                try:
                    await msg.delete()
                except:
                    pass
            msg_to_delete = await self.Func_glb_return_msg(channel, resp)
            last_update = time.time()

            while self.glb_tasks[channel.guild.id]['status'] == 0 and time.time() - last_update < interval:
                await asyncio.sleep(1)

        self.glb_tasks.pop(channel.guild.id)
        await channel.send("Task exited")

    async def CMD_Skyblock_event(self, message):
        # subcommands: list, start, end, restart
        # defaults to list if not specified
        args = message.content.split(' ')
        if len(args) == 1 or args[1] in ('list', 'l'):
            eventlist = self.eventmanager.list()
            message.channel.send(eventlist)
