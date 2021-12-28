import discord, os, sys, time, yaml, asyncio
from mcmessengerprotocol import McPtcl
from twisted.internet.asyncioreactor import AsyncioSelectorReactor
from serversettings import GetSettingsManager as SettingsManager

cmdinfopath = os.path.join(os.getcwd(),"commandinfo")
MINECRAFTSUBCOMMANDS = yaml.safe_load(open(os.path.join(cmdinfopath,"mcsubcmds.yaml"),"r"))

class McMessengerInterface(object):
    def __init__(self):
        #Minecraft related stuff (as in, a fake mc client)
        self.asr = AsyncioSelectorReactor()
        self.connections = {}
        self.connectedservers = {}
        self.settingsmanager = SettingsManager()

        #Do this to spawn a process for Minecraft!
        #processProtocol = McPtcl()
        #asr.spawnProcess(processProtocol, "mcmessengerstart.bat")
        #Then add the processProtocol to this list

    async def proccommand(self, message, subcommand, trailingargs):
        try:
            result = await eval(f"{MINECRAFTSUBCOMMANDS[subcommand]}(message)")
        except KeyError as e:
            #For testing
            raise e
        return result

    async def procmsg(self, message):
        #Bot's own messages
        if message.author.id == 797930119476936715:
            return
        #Another bot
        if message.author.bot:
            return
        pfx = self.settingsmanager.server_get(message.guild.id, 'prefix')
        if message.content.startswith(pfx):
            return
        for channelid, protocol in self.connections.items():
            if message.channel.id != channelid:
                continue
            content = message.content.replace('\n',' ')
            content = f"{message.author} - {content}\r\n"
            protocol.transport.write(content.encode('utf-8'))

    #Closes all subprocesses
    async def quit(self):
        for channelid, protocol in self.connections.items():
            await protocol.kill()

    async def CMD_start(self, message):
        #Initializes a Minecraft instance to connect to the server.
        args = message.content.split(' ')

        if len(args) >= 3:
            server_ip = args[2]
            if ' ' in server_ip:
                await message.channel.send("Server IPs are not supposed to have spaces!")
                return
            if not (1<=server_ip.count('.')<=3):
                await message.channel.send("Is there something wrong with the formatting of your IP?")
                return
        else:
            await message.channel.send("Please specify a server to connect to!")
            return

        channel = message.channel
        channelid = channel.id
        newprotocol = McPtcl(channel, self.connections)
        self.connections[channelid] = newprotocol

        #Generate executable
        with open("starttemp.bat","w") as fout:
            fout.write(f'python mcmessengercore.py --auth "jwang2147483648@gmail.com:JW4ng@!$&$*#^$*" {server_ip}')

        await message.channel.send("The connection to your server should be made soon!")
        self.asr.spawnProcess(newprotocol, "starttemp.bat")

        #Delete the file?
        #os.remove("starttemp.bat")

    async def CMD_stop(self, message):
        #Sends the kill signal to the process, and (waits for it to complete - I don't know much about twisted :/)
        for i, wrappedobj in enumerate(self.connections.items()):
            channelid, protocol = wrappedobj
            if message.channel.id != channelid:
                continue
            await protocol.kill()
            await message.channel.send("The process has ended.")
            return
        await message.channel.send("There are no active processes.")
