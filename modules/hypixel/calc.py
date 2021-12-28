"""
Classes and functions that assist in calculating Skyblock data.
"""


import yaml

#Load skyblock data
with open("skyblock_constants.yaml","r",encoding='utf-8') as fin:
    SKYBLOCK_DICT = yaml.load(fin, Loader=yaml.FullLoader)

class Skills():
    """Class with staticmethods for common skill operations."""

    #Validate skill name
    @staticmethod
    def validate(name):
        """Validates a skill name."""
        return name.lower() in SKYBLOCK_DICT["SKILLNAMES"]

    #Skills calculator (especially changing between level and exp)
    @staticmethod
    def level_to_exp(level):
        """Converts a Hypixel Skyblock skill's level into total exp."""
        if int(level)+1>len(SKYBLOCK_DICT["SKILLEXP"]):
            raise ValueError(f"Invalid skill level: {level}")
        if int(level)+1==len(SKYBLOCK_DICT["SKILLEXP"]):
            return SKYBLOCK_DICT["SKILLEXP"][int(level)]
        return SKYBLOCK_DICT["SKILLEXP"][int(level)] + \
               SKYBLOCK_DICT["LEVELEXP"][int(level)+1] * (level - int(level))

    @staticmethod
    def exp_to_level(exp, max_lvl=60):
        """Converts a Hypixel Skyblock skill's total exp into level."""
        if isinstance(max_lvl,str):
            if max_lvl in SKYBLOCK_DICT["SKILLNAMES_FIFTY"]:
                max_lvl = 50
            else:
                max_lvl = 60
        startpt = 0
        endpt = max_lvl+1
        mpt = None
        while startpt != endpt - 1:
            mpt = (startpt + endpt)//2
            if SKYBLOCK_DICT["SKILLEXP"][mpt] >= exp:
                endpt = mpt
            else:
                startpt = mpt
        rem_exp = exp - SKYBLOCK_DICT["SKILLEXP"][startpt]
        if startpt == max_lvl:
            return max_lvl
        return startpt + rem_exp / SKYBLOCK_DICT["LEVELEXP"][startpt+1]

    @staticmethod
    def raw_weight(expo, mod, maxlvl, level, exp):
        """The most primitive weight calculator, taking in all necessary arguments.
Expo, Mod   - Arguments from Senither's Weight Formula
Maxlvl      - Maximum level of the respective skill
Level, Exp  - Skill progress indicator
"""
        maxskillxp = SKYBLOCK_DICT["SKILLEXP"][maxlvl]
        level = min(level, maxlvl)
        base = (level * 10) ** (0.5 + expo + (level / 100)) / 1250
        if exp >= maxskillxp:
            base = round(base)
        else:
            return (base, 0)
        return (base, ((exp - maxskillxp) / mod) ** 0.968)

    @staticmethod
    def weight(skill, exp, level=None):
        """Calculates weight by skill and exp."""
        skill_weight = SKYBLOCK_DICT["SKILLWEIGHTS"][skill]
        if not level:
            level = Skills.exp_to_level(exp)
        return Skills.raw_weight(skill_weight[0], skill_weight[1], skill_weight[2], level, exp)




class Slayers():
    """Class with staticmethods for common slayer operations."""

    @staticmethod
    def validate(name):
        """Validates a slayer name."""
        return name.lower() in SKYBLOCK_DICT["SLAYERS"]

    @staticmethod
    def raw_weight(div, mod, exp):
        """The most primitive weight calculator, taking in all necessary arguments."""
        if exp < 1000000:
            return (0,0) if exp==0 else (exp/div,0)
        base = 1000000 / div
        rem = exp - 1000000
        cmod = mod
        ovf = 0
        while rem > 0:
            left = min(rem, 1000000)
            ovf += (left / (div * (1.5 + cmod))) ** 0.942
            cmod += mod
            rem -= left
        #Since overflow is internal for slayers, it will be combined when returned.
        return (base+ovf, 0)

    @staticmethod
    def weight(slayer, exp):
        """Calculates weight by skill and exp."""
        slayer_weight = SKYBLOCK_DICT["SLAYERWEIGHTS"][slayer]
        return Slayers.raw_weight(slayer_weight[0], slayer_weight[1], exp)

class Dungeons():
    """Class with staticmethods for common dungeon/class operations."""

    @staticmethod
    def validate(name):
        """Validates a dungeon/class name."""
        return name.lower() in SKYBLOCK_DICT["CLASSES"] + SKYBLOCK_DICT["DUNGEONS"]

    @staticmethod
    def level_to_exp(level):
        """Converts a Hypixel Skyblock dungeon's level into total exp."""
        if int(level)+1>len(SKYBLOCK_DICT["CATALVLEXP"]):
            raise ValueError(f"Invalid dungeon level: {level}")
        if int(level)+1==len(SKYBLOCK_DICT["CATALVLEXP"]):
            return SKYBLOCK_DICT["CATAEXP"][int(level)]
        return SKYBLOCK_DICT["CATAEXP"][int(level)] + \
               SKYBLOCK_DICT["CATALVLEXP"][int(level)+1] * (level - int(level))

    @staticmethod
    def exp_to_level(exp, max_lvl=50):
        """Converts a Hypixel Skyblock dungeon's total exp into level."""
        startpt = 0
        endpt = max_lvl+1
        mpt = None
        while startpt != endpt - 1:
            mpt = (startpt + endpt)//2
            if SKYBLOCK_DICT["CATAEXP"][mpt] >= exp:
                endpt = mpt
            else:
                startpt = mpt
        rem_exp = exp - SKYBLOCK_DICT["CATAEXP"][startpt]
        if startpt == max_lvl:
            return max_lvl
        return startpt + rem_exp / SKYBLOCK_DICT["CATALVLEXP"][startpt+1]

    @staticmethod
    def raw_weight(mod, level, exp):
        """The most primitive weight calculator, taking in all necessary arguments."""
        base = (level**4.5) * mod
        if exp < SKYBLOCK_DICT["CATAEXP"][-1]:
            return (base, 0)
        rem = exp - SKYBLOCK_DICT["CATAEXP"][-1]
        splitter = 4 * SKYBLOCK_DICT["CATAEXP"][-1] / base
        return (round(base), (rem / splitter) ** 0.968)

    @staticmethod
    def weight(dung, exp, level=None):
        """Calculates weight by skill and exp."""
        dungeon_weight = SKYBLOCK_DICT['CATAWEIGHTS'][dung]
        if not level:
            level = Dungeons.exp_to_level(exp)
        return Dungeons.raw_weight(dungeon_weight, level, exp)
