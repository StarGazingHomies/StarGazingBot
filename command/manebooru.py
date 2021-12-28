import os
import time

import aiohttp
import discord
import yaml

from modules.manebooru.struct import ManebooruPagesInteractive
from modules.manebooru.api import API_featured, API_search

class ManebooruInterface(object):
    def __init__(self, session=None):
        if not session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))
        else:
            self.session = session

    # Help command
    async def CMD_help(self, message):
        args = message.content[i:].split(' ')
        if len(args) == 2:
            pass

    # API commands
    async def CMD_featured(self, message):
        data = await API_featured(self.session)
        await message.channel.send(f"https://manebooru.art/images/{data['image']['id']}")
        return {"status":0}

    async def CMD_random(self, message):
        cnt = 0
        for i, char in enumerate(message.content):
            if cnt == 2:
                break
            if char == ' ':
                cnt += 1
        queries = message.content[i:]
        querylist = queries.split(', ')
        data = await API_search(self.session, querylist)

        if data['total'] == 0:
            await message.channel.send("No images found!")
            return {"status":0}
        
        img = data['images'][0]
        imgurl = f"https://manebooru.art/images/{img['id']}"
        msg = await message.channel.send(f"[{data['total']} results] [ID #{img['id']}] {imgurl}")
        return {"status":0}

    async def CMD_search(self, message):
        cnt = 0
        for i, char in enumerate(message.content):
            if cnt == 2:
                break
            if char==' ':
                cnt+=1
        args = message.content[i:].split(',')
        keys = {}
        querylist = []

        for arg in args:
            if '=' in arg:
                m = arg.split('=')
                keys[m[0]] = m[1]
            else:
                querylist.append(arg)

        data = await API_search(self.session, querylist)

        if data['total'] == 0:
            await message.channel.send("No images found!")
            return {"status":0}

        msg = await message.channel.send("Please wait a bit...")
        respobj = ManebooruPagesInteractive(session=self.session, querylist=querylist, **keys)
        await respobj.apiget()
        
        #Add object to list
        return {"status":1, 'msg':msg, 'obj':respobj}
