"""
This module focuses on the responses that will be triggered when a command is executed.
Includes basic responses for user verification, expanding, and scrolling through pages.
"""

from discord import Embed, Colour
import discord
from abc import ABC, abstractmethod


class Response(ABC):
    @abstractmethod
    def response(self):
        """Gets the updated message arguments for the response."""

    @abstractmethod
    def timeout(self):
        """Method that returns a timeout embed for the response.
This method will be called after 120s of inactivity on the response."""

    @abstractmethod
    async def proc_reaction(self, reaction, user):
        """Method that processes a reaction on the message.
This method will be called when a reaction is added.
A return value of 0 indicate success. Negative values indicate failure.
A return value of 1 will mean to remove the object from list of checked objects."""

    @abstractmethod
    async def proc_response(self, message):
        """Method that processes a message response after the message.
This method will be called when a player sends a message in the same channel as the response."""


class PagedResponse(Response, ABC):
    def __init__(self, message, user, title, pages, cur=0, colour=Colour.blue()):
        self.msg = message
        self.user = user
        self.title = title
        self.pages = pages
        self.cur = cur
        self.length = len(self.pages)
        self.colour = colour

    @property
    def embed(self):
        embed = Embed(title=self.title, description=self.pages[self.cur], colour=self.colour)
        embed.set_footer(text="React with ⏪ ⏩ ◀️ ▶️ to navigate")
        return embed

    def response(self):
        return {'content': None, 'embed': self.embed}

    def timeout(self):
        embed = self.embed
        embed.set_footer(text='Timed Out')
        return {'content': None, 'embed': embed}

    async def proc_reaction(self, reaction, user):
        if self.msg.id != reaction.message.id or self.user.id != user.id:
            return 0
        if reaction.emoji == '⏪':
            self.rewind()
        elif reaction.emoji == '⏩':
            self.fast_forward()
        elif reaction.emoji == '◀':
            self.prev()
        elif reaction.emoji == '▶':
            self.next()

        await reaction.message.edit(**self.response())
        await reaction.remove(user)
        return 0

    async def proc_response(self, message):
        return 0

    def next(self):
        self.cur += 1

    def prev(self):
        self.cur -= 1

    def rewind(self):
        self.cur = 0

    def fast_forward(self):
        self.cur = self.length - 1


class ExpandableResponse(Response, ABC):
    def __init__(self, message, user, short, long, timeout):
        self.msg = message
        self.user = user
        self.short = short
        self.long = long
        self.timeout_embed = timeout

    def response(self):
        return self.short

    def timeout(self):
        return self.timeout_embed

    async def proc_reaction(self, reaction, user):
        if self.msg.id != reaction.message.id or self.user.id != user.id:
            return 0
        if reaction.emoji == '⬇️':
            await reaction.message.edit(embed=self.long)
            await reaction.remove(user)
            await reaction.remove(self.msg.author)
            return 1
        else:
            return 0

    async def proc_response(self, message):
        return 0


class VerifyResponse(Response, ABC):
    def __init__(self, message, user, verified_role):
        self.msg = message
        self.user = user
        self.verified_role = verified_role
        self.wait = Embed(title="User Verification",
                          description="React with <:izzywut:917852579562659841> to verify!",
                          color=Colour.blue(), )
        self.timeout_embed = Embed(title="Timed out!", color=Colour.red(), )
        self.success = Embed(title="User Verification",
                             description=f"<@!{message.author.id}> You have been verified! Access to the rest of the server will be granted shortly.",
                             color=Colour.green(), )
        self.fail = Embed(title="User Verification",
                          description=f"<@!{message.author.id}> Please react with the right emoji.",
                          color=Colour.red(), )

    def timeout(self):
        return {'content': None, 'embed': self.timeout_embed}

    def response(self):
        return {'content': None, 'embed': self.wait}

    async def proc_reaction(self, reaction, user):
        print(self.msg.id, self.msg.content, reaction.message.id, reaction.message.content, self.user.id, user.id)
        if self.msg.id != reaction.message.id or self.user.id != user.id:
            return 0
        print(reaction.emoji.id)
        if reaction.emoji.id == 917852579562659841:
            await reaction.message.edit(embed=self.success)
            await user.add_roles(self.verified_role)
            try:
                await reaction.message.delete()
            except discord.NotFound:
                pass
            return 1
        else:
            return 0

    async def proc_response(self, message):
        return 0


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