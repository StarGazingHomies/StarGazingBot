"""
Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""


import yaml

"""
This python file generates some necessary files for the bot, which makes
modifying constants easier.
These files will be read when needed, and have constants for everything
skyblock-related and discord-related such as xp required per level,
and certain figures or settings for the bot. Changing this is going to
be easier than finding/updating the file which contains these, or updating
the beginning of every file related.
"""


#SKYBLOCK
"""
All skyblock constants, obtained JULY 2020 (OUTDATED)
"""

skyblock_dict = {}

skyblock_dict["SKILLWEIGHTS"] = {"mining":[1.18207448, 259634, 60], "foraging":[1.232826, 259634, 50], "enchanting":[0.96976583, 882758, 60], \
                                 "farming":[1.217848139, 220689, 60], "combat":[1.15797687265, 275862, 60], "fishing":[1.406418, 88274, 50], \
                                 "alchemy":[1.0, 1103448, 50], "taming":[1.14744, 441379, 50]}
skyblock_dict["SLAYERWEIGHTS"] = {"zombie":(2208,0.15), "spider":(2118,0.08), "wolf":(1962,0.015), "enderman":(1430, 0.017)}
skyblock_dict["CATAWEIGHTS"] = {"catacombs":0.0002149604615, "healer":0.0000045254834, "mage":0.0000045254834, "berserk":0.0000045254834, "archer":0.0000045254834, "tank":0.0000045254834}
skyblock_dict["SLAYERS"] = ["zombie", "spider", "wolf", "enderman"]
skyblock_dict["CLASSES"] = ["healer", "mage", "berserk", "archer", "tank"]
skyblock_dict["DUNGEONS"] = ["catacombs"]
skyblock_dict["SKILLS"] = {"combat":"skyblock_combat", "mining":"skyblock_excavator", "alchemy":"skyblock_concoctor", "farming":"skyblock_harvester",\
                           "taming":"skyblock_domesticator", "fishing":"skyblock_angler", "enchanting":"skyblock_augmentation", "foraging":"skyblock_gatherer"}
skyblock_dict["SKILLAPINAMES"] = ["experience_skill_combat","experience_skill_mining","experience_skill_alchemy","experience_skill_farming",\
                 "experience_skill_taming","experience_skill_fishing","experience_skill_enchanting","experience_skill_foraging"]
skyblock_dict["SKILLNAMES_FIFTY"] = ["alchemy","taming","fishing","foraging"]
skyblock_dict["SKILLNAMES_SIXTY"] = ["combat","mining","farming","enchanting"]
skyblock_dict["SKILLNAMES"] = skyblock_dict["SKILLNAMES_FIFTY"] + skyblock_dict["SKILLNAMES_SIXTY"]
skyblock_dict["USELESSSKILLNAMES"] = ["experience_skill_runecrafting","experience_skill_carpentry"]
skyblock_dict["SLAYEREXP"] = {'zombie':[0,5,15,200,1000,5000,20000,1e5,4e5,1e6],\
             'spider':[0,5,15,200,1000,5000,20000,1e5,4e5,1e6],\
             'wolf':[0,10,25,250,1500,5000,20000,1e5,4e5,1e6],\
             'enderman':[0,10,25,250,1500,5000,20000,1e5,4e5,1e6]}
skyblock_dict["SKILLEXP"] = (0,50,175,375,675,1175,1925,2925,4425,6425,9925,14925,22425,32425,47425,67425,97425,147425,222425,322425,522425,822425,1222425,\
            1722425,2322425,3022425,3822425,4722425,5722425,6822425,8022425,9322425,10722425,12222425,13822425,15522425,17322425,\
            19222425,21222425,23322425,25522425,27822425,30222425,32722425,35322425,38072425,40972425,44072425,47472425,51172425,55172425,\
            59472425, 64072425, 68972425, 74172425, 79672425, 85472425, 91572425, 97972425, 104672425, 111672425)
skyblock_dict["LEVELEXP"] = (0,50,125,200,300,500,750,1000,1500,2000,3500,5e3,7500,1e4,15e3,2e4,3e4,5e4,75e3,1e5,2e5,3e5,4e5,5e5,6e5,7e5,8e5,9e5,1e6,11e5,\
            12e5,13e5,14e5,15e5,16e5,17e5,18e5,19e5,2e6,21e5,22e5,23e5,24e5,25e5,26e5,275e4,29e5,31e5,34e5,37e5,4e6,43e5,46e5,49e5,52e5,55e5,58e5,61e5,64e5,67e5,7e6)
skyblock_dict["CATAEXP"] = (0,50,125,235,395,625,955,1425,2095,3045,4385,6275,8940,12700,17960,25340,35640,50040,70040,97640,135640,188140,259640,356640,488640,668640,911640,1239640, \
           1684640,2284640,3084640,4149640,5559640,7459640,9959640,13259640,17559640,23159640,30359640,39559640,51559640,66559640,85559640,109559640,139559640,177559640, \
           225559640,285559640,360559640,453559640,569809640)
skyblock_dict["CATALVLEXP"] = (0,50,75,110,160,230,330,470,670,950,1340,1890,2665,3760,5260,7380,10300,14400,20000,27600,38000,52500,71500,97000,132000,180000,\
              243e3,328e3,445e3,6e5,8e5,1065e3,141e4,19e5,25e5,33e5,43e5,56e5,72e5,92e5,12e6,15e6,19e6,24e6,30e6,38e6,48e6,6e7,75e6,93e6,116250000)
skyblock_dict["DATALOCATION"] = {"farming":'k["members"][self.id]["experience_skill_farming"]', "fishing":'k["members"][self.id]["experience_skill_fishing"]', \
                "mining":'k["members"][self.id]["experience_skill_mining"]', "combat":'k["members"][self.id]["experience_skill_combat"]', \
                "taming":'k["members"][self.id]["experience_skill_taming"]', "foraging":'k["members"][self.id]["experience_skill_foraging"]', \
                "enchanting":'k["members"][self.id]["experience_skill_enchanting"]', "alchemy":'k["members"][self.id]["experience_skill_alchemy"]', \
                "catacombs":'k["members"][self.id]["dungeons"]["dungeon_types"]["catacombs"]["experience"]', "zombie":"k['members'][self.id]['slayer_bosses']['zombie']['xp']", \
                "spider":"k['members'][self.id]['slayer_bosses']['spider']['xp']", "wolf":"k['members'][self.id]['slayer_bosses']['wolf']['xp']", \
                "healer":'k["members"][self.id]["dungeons"]["player_classes"]["healer"]["experience"]', "mage":'k["members"][self.id]["dungeons"]["player_classes"]["mage"]["experience"]', \
                "berserk":'k["members"][self.id]["dungeons"]["player_classes"]["berserk"]["experience"]', "archer":'k["members"][self.id]["dungeons"]["player_classes"]["archer"]["experience"]', \
                "tank":'k["members"][self.id]["dungeons"]["player_classes"]["tank"]["experience"]'}

yaml.dump(skyblock_dict, open("skyblock_constants.yaml","w"))
