import aiohttp

import modules.minecraft.mojangapi as mojangapi


class Listener:
    def __init__(self):
        self.req_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))

    async def CMD_uuid(self, message):
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
        result = await mojangapi.getuuid(self.req_session, username, **kwargs)
        if not result:
            await message.channel.send("An error occurred. Please try again later.")
        await message.channel.send(f"The uuid of {username} is {result}.")
        return

    async def CMD_username(self, message):
        """Get the username of a Minecraft user."""
        args = message.content.split(' ')
        if len(args) >= 2:
            uuid = args[1]
        else:
            await message.channel.send("Please indicate a uuid to get the username of.")
            return
        result = await mojangapi.getusername(self.req_session, uuid)
        if not result:
            await message.channel.send("An error occurred. Please try again later.")
        await message.channel.send(f"The username of {uuid} is {result}.")
