import yaml

VALID_SETTINGS = ('enabled','verifiedrole','staffrole','apply','verify','skyblock_guild','prefix','applycategory','namespaces')

SETTING_TYPES = {'enabled':'bool',\
                 'verifiedrole':'role',\
                 'staffrole':('role','none'),\
                 'apply':'bool',\
                 'verify':'bool',\
                 'skyblock_guild':('str','none'),\
                 'prefix':'str',\
                 'applycategory':('channel','none'),\
                 'id':'int',\
                 'logchannel':('channel','none'),\
                 'namespaces':('list-namespaces'),\
                 'conditional':('conditional'),\
                 'disabled':('channel:list-command')}
    
yaml.dump(SETTING_TYPES, open("../settings/settingsinfo/settingtypes.yaml", "w"))

DEFAULT_SETTINGS = {'enabled':True,\
                    'id':None,\
                    'verifiedrole':None,\
                    'staffrole':None,\
                    'apply':False,\
                    'verify':False,\
                    'skyblock_guild':None,\
                    'prefix':'star!',\
                    'applycategory':None,\
                    'logchannel':None,\
                    'namespaces':[],\
                    'conditional':[],\
                    'disabled':{}}

yaml.dump(DEFAULT_SETTINGS, open("../settings/settingsinfo/default.yaml", "w"))
