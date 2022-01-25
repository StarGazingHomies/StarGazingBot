"""
This module focuses on often-used structures/classes in the discord bot.
Most base/data modules will be defined here.
"""

import discord
from discord import Embed, Colour


class ReactionResponse:
    def __init__(self, message, user):
        """The most basic response object to a reaction.
:param message: the message to react to
:type message: discord.Message
:param user: the user that triggers the reaction
:type user: discord.User

:rtype: ReactionResponse
:return: An object that uses on_reaction to handle reactions.
"""
        self.message = message
        self.user = user

    def is_match(self, reaction, user):
        """Checks whether a reaction should be handled by this object
:param reaction: the reaction object, provided by discord.on_reaction_add
:type reaction: discord.Reaction
:param user: the user provided by discord.on_reaction_add
:type user: discord.User

:rtype: bool
:return: Whether the reaction should be handled
"""
        if self.message.id != reaction.message.id:
            return False
        if self.user.id != user.id:
            return False
        return True

    def on_reaction(self, reaction, user):
        """Handles a reaction by checking if it matches the message and user.
:param reaction: the reaction object, provided by discord.on_reaction_add
:type reaction: discord.Reaction
:param user: the user provided by discord.on_reaction_add
:type user: discord.User

:rtype: dict
:return: A dictionary indicating the status and any additional information.
"""
        if not self.is_match(reaction, user):
            return {'status': -1}
        # Implement anything else here.


class PagedResponse(object):
    def __init__(self, title, pages, cur=0, colour=Colour.blue()):
        self.title = title
        self.pages = pages
        self.cur = cur
        self.length = len(self.pages)
        self.colour = colour

    @property
    def embed(self):
        embed = Embed(title=self.title, description=self.pages[self.cur], colour=self.colour)
        embed.set_footer(text="React with ⏪ ⏩ ◀️ ▶️ to navigate")
        return {'content': None, 'embed': embed}

    def next(self):
        if self.cur == self.length - 1:
            return -1
        self.cur += 1
        return self.embed

    def prev(self):
        if self.cur == 0:
            return -1
        self.cur -= 1
        return self.embed

    def rewind(self):
        self.cur = 0
        return self.embed

    def fast_forward(self):
        self.cur = self.length - 1
        return self.embed


class ExpandableResponse(object):
    def __init__(self, short, long, timeout):
        self.short = short
        self.long = long
        self.timeout = timeout


class VerifyResponse(object):
    def __init__(self, message, nick_change):
        self.wait = Embed(title="User Verification",
                          description="React with <a:check:927622044709969981> to verify!",
                          color=Colour.blue(), )
        self.timeout = Embed(title="Timed out!", color=Colour.red(), )
        self.success = Embed(title="User Verification",
                             description=f"<@!{message.author.id}> You have been verified! Access to the rest of the "
                                         f"server will be granted shortly.",
                             color=Colour.green(), )
        self.fail = Embed(title="User Verification",
                          description=f"<@!{message.author.id}> Please react with the right emoji.",
                          color=Colour.red(), )
        self.nick_change = nick_change


class EchoMessage(object):
    def __init__(self, content, channel, author, perms=1):
        self.content = content
        self.channel = channel
        self.author = author
        self.permission_level = perms
        # Maybe the message is in a DM channel. This shouldn't happen, but it might
        try:
            self.guild = channel.guild
        except AttributeError:
            pass

    # These calls won't do anything because the message is fake.
    async def delete(self, *args, **kwargs):
        pass

    async def edit(self, *args, **kwargs):
        pass

    async def add_reaction(self, *args, **kwargs):
        pass

    async def clear_reaction(self, *args, **kwargs):
        pass

    async def clear_reactions(self, *args, **kwargs):
        pass
