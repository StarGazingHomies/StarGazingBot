import yaml, os, logging

"""
This file loads setting files for each server. This allows for server-to-server configuration.
"""

#List of all settings

settingsinfopath = os.path.join(os.getcwd(),"settings","settingsinfo")
SETTING_TYPES = yaml.load(open(os.path.join(settingsinfopath,"settingtypes.yaml"),"r"), yaml.FullLoader)
DEFAULT_SETTINGS = yaml.safe_load(open(os.path.join(settingsinfopath,"default.yaml"),"r"))

logger = logging.getLogger("main.settings")

def GetSettingsManager():
    if SettingsManager.created_instance:
        return SettingsManager.created_instance
    obj = SettingsManager()
    SettingsManager.created_instance = obj
    return obj

async def SettingTypeCheck(guild, setting, value):
    #The guild is here for guild.fetch_channel and fetch_role calls.
    try:
        stype = SETTING_TYPES[setting]
    except KeyError:
        #Not valid setting
        return -1

    if setting == 'conditional':
        return -2

    if ':' in stype:
        # Not going to check here!
        return -3

    if isinstance(stype, tuple):
        stypes = stype
    else:
        stypes = (stype,)

    for stype in stypes:
        if stype == 'int':
            if isinstance(value, int):
                return True
        elif stype == 'bool':
            if isinstance(value, bool):
                return True
        elif stype == 'str':
            if isinstance(value, str):
                return True
        elif stype == 'none':
            if value==None:
                return True
        elif stype == 'channel':
            if not isinstance(value, int):
                continue
            if guild.get_channel(value):
                return True
            await guild.fetch_channels()
            if guild.get_channel(value):
                return True
        elif stype == 'role':
            if not isinstance(value, int):
                continue
            if guild.get_role(value):
                return True
            await guild.fetch_roles()
            if guild.get_role(value):
                return True
    return False


class SettingsManager():
    created_instance = None
    """This class manages the settings files for StarGazingBot."""
    def __init__(self, *args, **kwargs):
        try:
            self.path = os.path.join(os.getcwd(), "settings")
            self.serverpath = os.path.join(self.path, "servers")
            self.helppath = os.path.join(self.path, "settingsdoc")
            # Overall settings - this is important for the bot to start running.
            self.cfg = yaml.safe_load(open(os.path.join(os.getcwd(), "settings", "config.env"), 'r'))
            logger.info("Overall config acquired.")
        except:
            raise FileNotFoundError("Overall settings, such as the BOT TOKEN and API KEY, did not properly load. Please check if all files are present, then try again.")
        self.server_specific = {}
        self.load_servers()
        self.types = SETTING_TYPES
        
    def load_servers(self, *args, **kwargs):
        """This function loads the setting files present in the \\settings directory.
It is called automatically upon object init."""
        self.server_specific = {}
        with os.scandir(self.serverpath) as settingsdir:
            for file in settingsdir:
                if file.name == '.DS_Store':
                    continue
                try:
                    server = yaml.safe_load(open(file.path, 'r'))
                    self.server_specific[server['id']] = server
                    self.server_check(server['id'])
                except Exception as e:
                    logger.error()
                    return -1       # Operation not completed
        return

    # Checks validity of server settings upon startup
    def server_check(self, server_id, autosave=True):
        settingsdata = self.server_specific[server_id]
        newsettingsdata = {}
        for setting in SETTING_TYPES.keys():
            try:
                # Norminal
                newsettingsdata[setting] = settingsdata[setting]
                settingsdata.pop(setting)
            except KeyError:
                # No setting!
                newsettingsdata[setting] = DEFAULT_SETTINGS[setting]
                logger.warning(f"Missing setting {setting} in server {server_id}. Replaced with default {DEFAULT_SETTINGS[setting]}.")
        for setting, val in settingsdata.items():
            logger.warning(f"Unknown setting {setting} set as {val} in server {server_id}. Setting dropped.")
        self.server_specific[server_id] = newsettingsdata
        if autosave:
            yaml.dump(newsettingsdata, self.server_open(server_id))
        return

    # Gets the help message
    def help_get(self, setting):
        print(os.path.join(self.helppath, f'{setting}.txt'))
        with open(os.path.join(self.helppath, f'{setting}.txt')) as fin:
            result = fin.read()
        return result

    # Fake function!
    def global_edit(self, setting, value):
        """I simply will NOT let you edit these settings! They can easily break the bot!"""
        return

    # Server settings
    def server_open(self, server_id, mode='w'):
        """Opens a server's config file from the default directory. Returns a file object."""
        return open(os.path.join(self.serverpath,f'{server_id}.yaml'), mode)

    def server_get(self, server_id, setting=None):
        try:
            if setting:
                return self.server_specific[server_id][setting]
            else:
                return self.server_specific[server_id]
        except KeyError:
            return None

    async def server_edit(self, server, setting, value, autosave = True):
        if not ( setting.lower() in SETTING_TYPES.keys() ):
            return -1 # Valid setting not found
        if setting.lower() == 'id':
            return -2 # Can't edit the id - it is your guild's id! It's in the settings for convenience
        checkresult = await SettingTypeCheck(server, setting, value)
#        print(checkresult)
        if checkresult == -2:
            return -4 # Conditional
        if checkresult == -3:
            return -5 # Disable/enable commands
        if not checkresult:
            return -3 # Not the right type
        self.server_specific[server.id][setting] = value
        if autosave:
            yaml.dump(self.server_specific[server.id], self.server_open(server.id))
        return 0

    def server_save(self, server_id):
        """Saves the specified server settings."""
        yaml.dump(self.server_specific[server_id], self.server_open(server_id))
        return
    
    def newserver(self, server_id):
        settings = DEFAULT_SETTINGS
        settings['id'] = server_id
        yaml.dump(settings, self.server_open(server_id))
        self.server_specific[server_id] = settings
        return
