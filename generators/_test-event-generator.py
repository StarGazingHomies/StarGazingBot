import yaml

"""
This python file generates a fake event to test the bot's functions.
"""

#Test Event

event = {"enabled":1,\
         "end_time":1,\
         "event_type":'weight',\
         "discord_guild":698420870670188614,\
         "discord_channel":743821641917661356,\
         

yaml.dump(event, open("1.yaml","w"))
