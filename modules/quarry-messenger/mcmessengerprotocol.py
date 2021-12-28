import discord, asyncio
from twisted.internet import protocol

class McPtcl(protocol.ProcessProtocol):
    def __init__(self, channel, conns):
        self.verses = 10
        self.data = ""
        self.channel = channel
        self.otherconnections = conns
        self.ended = 0

    #Kill
    async def kill(self):
        killstring = "kill\r\n"
        self.transport.write(killstring.encode('utf-8'))
##        await asyncio.sleep(5)
##        self.transport.loseConnection()
##        self.transport.signalProcess('KILL')
##        while self.ended != 0:
##            asyncio.sleep(1)

    #Following methods are called when something happens
    def connectionMade(self):
        print("Process started.")

    def outReceived(self, data):
        print(f"Minecraft: Output recieved! {data}")
        #self.data = self.data + str(data)
        strdata = data.decode()
        self.data += strdata
        if not "\r\n" in self.data:
            return
        parts = self.data.split('\r\n')
        for part in parts[:-1]:
            discmsg = {}

            #Sample - chat.type.text{StarGazingHomies, ikr}
            if part.startswith("chat.type.text"):
                m = part.split(',')
                user, message = f"{m[0][15:]}", f"{m[1][1:-1]}"
                if user == 'StarGazingHomies':
                    continue
                embed=discord.Embed(title=user, description=message)
                discmsg['embed'] = embed

            #Sample - multiplayer.player.left{RainbowRoadtrip}\r\n
            if part.startswith("multiplayer.player.left"):
                pass

            #Sample - multiplayer.player.joined
            if part.startswith("multiplayer.player.joined"):
                pass

            if part.startswith("multiplayer.disconnect.server_shutdown"):
                pass #What the heck that's not supposed to happen...

            if discmsg != {}:
                asyncio.create_task(self.channel.send(**discmsg))
        self.data = parts[-1]
        

    def errReceived(self, data):
        print(f"Error recieved!\n{data.decode()}")
#        self.transport.signalProcess('KILL')

    def inConnectionLost(self):
        print("stdin is closed!")

    def outConnectionLost(self):
        print("Stdout is closed!")
#        (dummy, lines, words, chars, file) = re.split(r'\s+', self.data)
#        print("I saw %s lines" % lines)
#        self.transport.signalProcess('KILL')

    def errConnectionLost(self):
        print("Stderr is closed!")

    def processExited(self, reason):
        print("Process exited, status %d" % (reason.value.exitCode,))
        self.otherconnections.pop(self.channel.id)

    def processEnded(self, reason):
        print("Process ended, status %d" % (reason.value.exitCode,))
        print("Quitting...")
        self.ended = 1
