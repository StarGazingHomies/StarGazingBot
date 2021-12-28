import logging, os

def SetupLoggers():
    logfilepath = os.path.join(os.getcwd(), "logs")
    #Hypixel parent logger
    hypixellogger = logging.getLogger('hypixel')
    hypixellogger.setLevel(logging.DEBUG)
    hypixelhandler = logging.FileHandler(filename=os.path.join(logfilepath, 'hypixel.log'), encoding='utf-8', mode='w')
    hypixelhandler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    hypixellogger.addHandler(hypixelhandler)
    
    #Minecraft API parent logger
    minecraftapilogger = logging.getLogger('minecraftapi')
    minecraftapilogger.setLevel(logging.DEBUG)
    minecraftapihandler = logging.FileHandler(filename=os.path.join(logfilepath, 'minecraftapi.log'), encoding='utf-8', mode='w')
    minecraftapihandler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    minecraftapilogger.addHandler(minecraftapihandler)

    #Commands parent logger
    cmdlogger = logging.getLogger('commands')
    cmdlogger.setLevel(logging.DEBUG)
    cmdhandler = logging.FileHandler(filename=os.path.join(logfilepath, 'commands.log'), encoding='utf-8', mode='w')
    cmdhandler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    cmdlogger.addHandler(cmdhandler)

    #Discord logger setup
    discordlogger = logging.getLogger('discord')
    discordlogger.setLevel(logging.DEBUG)
    discordhandler = logging.FileHandler(filename=os.path.join(logfilepath, 'discord.log'), encoding='utf-8', mode='w')
    discordhandler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    discordlogger.addHandler(discordhandler)

    #Cache logger
    cachelogger = logging.getLogger('cache')
    cachelogger.setLevel(logging.DEBUG)
    cachehandler = logging.FileHandler(filename=os.path.join(logfilepath, 'cache.log'), encoding='utf-8', mode='w')
    cachehandler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    cachelogger.addHandler(cachehandler)


    #Main logger for stuff that isn't hypixel or discord or commands... or whatever is defined above
    mainlogger = logging.getLogger('main')
    mainlogger.setLevel(logging.INFO)
    mainstdouthandler = logging.StreamHandler()
    mainstdouthandler.setFormatter(logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s: %(message)s'))
    mainfilehandler = logging.FileHandler(filename=os.path.join(logfilepath, 'main.log'), encoding='utf-8', mode='w')
    mainfilehandler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    mainlogger.addHandler(mainstdouthandler)
    mainlogger.addHandler(mainfilehandler)
