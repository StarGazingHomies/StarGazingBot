#Manages users - their settings, etc.
#Settings will persist across servers

import os, yaml

DEFAULT = {"test":True}

class UserManager(object):
    def __init__(self):
        self.dir = os.path.join(os.getcwd(), "userdata", "member")
        self.loaded = {}

    def member_open(self, userid, mode='a+'):
        return open(os.path.join(self.dir, f'{userid}.txt'), mode)

    def member_init(self, userid):
        yaml.dump( DEFAULT, self.member_open(userid) )

    def member_save(self, userid, settings):
        yaml.dump( settings, self.member_open(userid) )

    def member_load(self, userid):
        d = yaml.safe_load( self.member_open(userid, 'r') )
        return d
