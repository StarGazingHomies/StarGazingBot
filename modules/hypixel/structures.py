"""
Structures, such as Skills, to assist the Hypixel API.
"""

from modules.hypixel.calc import Skills, Slayers, Dungeons


class UnweightedSkill(object):
    __slots__ = ('_level', '_exp')

    def __init__(self, value=0, vtype='exp'):
        self._level = 0
        self._exp = 0
        # assert vtype in ('exp','lvl','level')
        if vtype == 'exp':
            self._exp = value
            self._level = Skills.exp_to_level(value)
        elif vtype == 'lvl' or vtype == 'level':
            self._level = value
            self._exp = Skills.level_to_exp(value)

    def __repr__(self):
        return f"Level: {self.level}; Exp: {self.exp}"

    # When changing the exp and level properties, the other one automagically changes.
    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, val):
        self._level = val
        self._exp = Skills.level_to_exp(val)

    @property
    def exp(self):
        return self._exp

    @exp.setter
    def exp(self, val):
        self._exp = val
        self._level = Skills.exp_to_level(val)


# Represents a weighted skill.
# Weight updates whenever data is changed.
class WeightedSkill(UnweightedSkill):
    __slots__ = ('_type', '_totw', '_basew', '_ovfw')

    def __init__(self, stype, value=0, vtype='exp'):
        if not Skills.validate(stype):
            raise ValueError("Please indicate a valid skill name.")
        super().__init__(value, vtype)
        self._type = stype.lower()
        self._basew, self._ovfw = Skills.weight(self.type, self._exp, self._level)
        self._totw = self._basew + self._ovfw
        self.update()

    def __repr__(self):
        return f"Level: {self.level}; Exp: {self.exp}"

    def update(self):
        pass

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, val):
        self._level = val
        self._exp = Skills.level_to_exp(val)
        self.update()

    @property
    def exp(self):
        return self._exp

    @exp.setter
    def exp(self, val):
        self._exp = val
        self._level = Skills.exp_to_level(val, self._type)
        self.update()

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, val):
        if not Skills.validate(val):
            raise ValueError("Please indicate a valid skill name.")
        self._type = val.lower()
        self.update()

    # Weight(s) are READABLE properties
    @property
    def weight(self):
        return self._totw

    @property
    def weights(self):
        return self._basew, self._ovfw


class WeightedSlayer:
    __slots__ = ('_type', '_ovfw', '_basew', '_totw', '_exp')

    def __init__(self, stype, exp=0):
        if not Slayers.validate(stype):
            raise ValueError("Please indicate a valid slayer name.")
        self._type = stype
        self._exp = exp
        self._basew, self._ovfw = Slayers.weight(stype, exp)
        self._totw = self._basew + self._ovfw

    def __repr__(self):
        return f"Exp: {self.exp}"

    def update(self):
        self._basew, self._ovfw = Slayers.weight(self._type, self._exp)
        self._totw = self._basew + self._ovfw

    @property
    def exp(self):
        return self._exp

    @exp.setter
    def exp(self, val):
        self._exp = val
        self.update()

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, val):
        if not Slayers.validate(val):
            raise ValueError("Please indicate a valid slayer name.")
        self._type = val
        self.update()

    @property
    def weight(self):
        return self._totw

    @property
    def weights(self):
        return self._basew, self._ovfw


class UnweightedDungeon(object):
    __slots__ = ('_level', '_exp')

    def __init__(self, value=0, vtype='exp'):
        self._level = 0
        self._exp = 0
        # assert vtype in ('exp','lvl','level')
        if vtype == 'exp':
            self._exp = value
            self._level = Dungeons.exp_to_level(value)
        elif vtype == 'lvl' or vtype == 'level':
            self._level = value
            self._exp = Dungeons.level_to_exp(value)

    def __repr__(self):
        return f"Level: {self.level}; Exp: {self.exp}"

    # When changing the exp and level properties, the other one automagically changes.
    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, val):
        self._level = val
        self._exp = Dungeons.level_to_exp(val)

    @property
    def exp(self):
        return self._exp

    @exp.setter
    def exp(self, val):
        self._exp = val
        self._level = Dungeons.exp_to_level(val)


# Represents a weighted dungeon skill.
# Weight udpates whenever data is changed.
class WeightedDungeon(UnweightedDungeon):
    __slots__ = ('_type', '_totw', '_basew', '_ovfw')

    def __init__(self, stype, *args, **kwargs):
        if not Dungeons.validate(stype):
            raise ValueError("Please indicate a valid skill name.")
        super().__init__(*args, **kwargs)
        self._type = stype.lower()
        self._basew, self._ovfw = Dungeons.weight(self.type, self._exp, self._level)
        self._totw = self._basew + self._ovfw
        self.update()

    def __repr__(self):
        return f"Level: {self.level}; Exp: {self.exp}"

    def update(self):
        pass

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, val):
        self._level = val
        self._exp = Dungeons.level_to_exp(val)
        self.update()

    @property
    def exp(self):
        return self._exp

    @exp.setter
    def exp(self, val):
        self._exp = val
        self._level = Dungeons.exp_to_level(val)
        self.update()

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, val):
        if not Dungeons.validate(val):
            raise ValueError("Please indicate a valid skill name.")
        self._type = val.lower()
        self.update()

    # Weight(s) are READABLE properties
    @property
    def weight(self):
        return self._totw

    @property
    def weights(self):
        return self._basew, self._ovfw
