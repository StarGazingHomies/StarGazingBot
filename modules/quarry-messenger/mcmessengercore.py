"""
Messenger example client

Bridges minecraft chat (in/out) with stdout and stdin.
"""

import os
import sys

from twisted.internet import defer, reactor, stdio
from twisted.protocols import basic
from quarry.net.auth import ProfileCLI
from quarry.net.client import ClientFactory, SpawningClientProtocol

#twisted.internet.stdio.StandardIO?
class StdioProtocol(basic.LineReceiver):
    delimiter = os.linesep.encode('ascii')
    in_encoding  = getattr(sys.stdin,  "encoding", 'utf8')
    out_encoding = getattr(sys.stdout, "encoding", 'utf32')

    def lineReceived(self, line):
#        print("Line recieved!")
        self.minecraft_protocol.send_chat(line.decode(self.in_encoding))

    def send_line(self, text):
#        m = text.split(',')
#        print(f"{m[0][15:]}: {m[1][1:-1]}")
        self.sendLine(text.encode(self.out_encoding))


class MinecraftProtocol(SpawningClientProtocol):
    spawned = False

    def player_joined(self, *args, **kwargs):
        super(SpawningClientProtocol,self).player_joined(*args, **kwargs)
        self.stdio_protocol.send_line("Joined.")

    def packet_received(self, *args, **kwargs):
        print("Packet received!")
#        self.stdio_protocol.send_line("Packed received!")
        super(SpawningClientProtocol, self).packet_received(*args, **kwargs)

    def packet_chat_message(self, buff):
        p_text = buff.unpack_chat().to_string()

        # 1.7.x
        if self.protocol_version <= 5:
            p_position = 0
        # 1.8.x
        else:
            p_position = buff.unpack('B')

        if p_position in (0, 1) and p_text.strip():
            m = p_text.split(',')
##            try:
##                if m[1][1:-1]=="test":
##                    self.send_chat("test!")
##            except Exception:
##                pass
            self.stdio_protocol.send_line(p_text)

    def send_chat(self, text):
        self.stdio_protocol.send_line(f"Sending {text} to chat!")
        if text == 'kill':
            reactor.stop()
        self.send_packet("chat_message", self.buff_type.pack_string(text))


class MinecraftFactory(ClientFactory):
    protocol = MinecraftProtocol
    log_level = "WARN"

    def buildProtocol(self, addr):
        minecraft_protocol = super(MinecraftFactory, self).buildProtocol(addr)
        stdio_protocol = StdioProtocol()

        minecraft_protocol.stdio_protocol = stdio_protocol
        stdio_protocol.minecraft_protocol = minecraft_protocol

        stdio.StandardIO(stdio_protocol)
        return minecraft_protocol


@defer.inlineCallbacks
def run(args):
    # Log in
    profile = yield ProfileCLI.make_profile(args)
#    print("Mojang profile acquired.")

    # Create factory
    factory = MinecraftFactory(profile)

    # Connect!
    factory.connect(args.host, args.port)


def main(argv):
#    print("THIS IS NOT THE MAIN DISCORD BOT")
#    argv = ['--auth', 'jwang2147483648@gmail.com:JW4ng@!$&$*#^$*', '127.0.0.1']
    parser = ProfileCLI.make_parser()
    parser.add_argument("host")
    parser.add_argument("port", nargs='?', default=25565, type=int)
    args = parser.parse_args(argv)
#    print(args)

    run(args)
    reactor.run()


if __name__ == "__main__":
    main(sys.argv[1:])
