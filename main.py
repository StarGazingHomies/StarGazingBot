"""
The main module of StarGazingBot. Running this starts the bot.
"""

import logging
import os

import discord
import yaml

from commands import Listener
from track import MemberWeight
from loggersetup import SetupLoggers

if __name__ == '__main__':
    # Voice library
    #    discord.opus.load_opus() #[ this is for linux ]

    # Discord intents
    INTENTS = discord.Intents.all()
    INTENTS.presences = False

    with open(os.path.join(os.getcwd(), "settings", "config.env"), encoding='utf-8') as fin:
        config = yaml.safe_load(fin)
    TOKEN = config.get('token')
    API_KEY = config.get('api_key')

    VERSION = '1w7a'

    # Logging
    SetupLoggers()
    mainlogger = logging.getLogger('main')

    try:
        bot = discord.Client(intents=INTENTS)
        commands = Listener(bot)
        memberweight = MemberWeight()
        commands.tracker = memberweight


        @bot.event
        async def on_ready():
            """Async function that triggers when the bot is ready."""
            activity = discord.Activity(name='Boop!', type=discord.ActivityType.playing)
            await bot.change_presence(activity=activity)
            mainlogger.info("Bot ready.")
            mainlogger.info("Current active guilds:")
            for guild in bot.guilds:
                mainlogger.info("%s (ID: %d)", guild.name, guild.id)
            await commands.on_ready()


        @bot.event
        async def on_message(message):
            """Async function that triggers when the bot receives a message."""
            await memberweight.on_message(message)
            await commands.on_message(message)
            # Commands also checks if this is a response message.


        @bot.event
        async def on_reaction_add(reaction, user):
            """Async function that triggers when the bot sees an reaction being added."""
            if user == bot.user:  # Reactions by the bot itself
                return
            if user.bot:  # If reaction was by another bot, ignore
                return
            mainlogger.info("Reaction %s added by user %s.", str(reaction), str(user))
            await commands.on_reaction(reaction, user)


        bot.run(TOKEN)
    except Exception as e:
        raise e
