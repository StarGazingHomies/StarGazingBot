#D&D Rolling
import random

#Replace a region of a string
def regionreplace(originalstr, newstring, startindex, endindex):
    #Include neither side
    before, after = originalstr[:startindex], originalstr[endindex+1:]
    return before+newstring+after

#Get number (int or float) from string
def getnum(string):
    after_dot = False
    cur = 0
    scale = 1
    for char in string:
        if char == '.':
            after_dot = True
            continue
        if after_dot:
            scale /= 10
            cur += (ord(char)-48) * scale
        else:
            cur *= 10
            cur += ord(char)-48
    return cur

def splitbrackets(string):
    level = 0
    levelbegin = []
    levels = []
    for index, char in enumerate(string):
#        print(index, char, level, levelbegin)
        if char == ('('):
            level += 1
            levelbegin.append(index)
        if char == (')'):
            level -= 1
            if level < 0:
                #Open your brackets!
                raise SyntaxError('unexpected EOF while parsing')
            levels.append((level+1, levelbegin[-1], index))
            levelbegin.pop(-1)
    if level != 0:
        #Close your brackets!
        raise SyntaxError('unexpected EOF while parsing')

    #Sort by the level - higher levels first
    levels.sort(key=lambda x:-x[0])

    # Example: 1+(2*(4+5) + 3 * (3-2)) / (5-2)              (answer = 8)
    # Levels : [(2, 5, 9), (2, 17, 21), (1, 2, 22), (1, 26, 30)]
    # Now, within each level, there are no more brackets!
    # That is, if you evaluate the higher leveled stuff first
    return levels

#Another alternative... find the first bracket to calc
def firstbracket(string):
    begin = 0
    for index, char in enumerate(string):
        if char == ('('):
            begin = index
        if char == (')'):
            return (begin,index)
    return None

#No brackets calculation
def nbcalculate(string):
#    print(string)
    allrolls = []
    operators = ['+','-','*','/','d']
    if string[0] in operators:
        raise SyntaxError('invalid syntax')
    valid = [str(i) for i in range(10)] + operators
    parsed = []
    last = 0
    for i, char in enumerate(string):
        if char in operators:
            if last == i:
                raise SyntaxError('invalid syntax')
            parsed.append( getnum(string[last:i]) )
            parsed.append( char )
            last = i+1
        if not char in valid:
            raise SyntaxError('invalid syntax')
    parsed.append( getnum(string[last:]) )

    # Rolls precede all operations
    i = 0
    while i < len(parsed):
        char = parsed[i]
        while char == 'd':
            rolls = roll(parsed[i-1], parsed[i+1])
            allrolls.append([f"{parsed[i-1]}d{parsed[i+1]}", rolls, sum(rolls)])
            parsed[i-1] = allrolls[-1][2]
            parsed.pop(i)
            parsed.pop(i)
            if i >= len(parsed):
                break
            char = parsed[i]
        i += 1

    # Multiplication and division
    i = 0
    while i < len(parsed):
        char = parsed[i]
        while char in ('*','/'):
            if char == '*':
                parsed[i-1] = parsed[i-1] * parsed[i+1]
                parsed.pop(i)
                parsed.pop(i)
                if i >= len(parsed):
                    break
                char = parsed[i]
            elif char == '/':
                parsed[i-1] = parsed[i-1] / parsed[i+1]
                parsed.pop(i)
                parsed.pop(i)
                if i >= len(parsed):
                    break
                char = parsed[i]
        i += 1

    # Addition and subtraction
    i = 0
    while i < len(parsed):
        char = parsed[i]
        while char in ('+','-'):
            if char == '+':
                parsed[i-1] = parsed[i-1] + parsed[i+1]
                parsed.pop(i)
                parsed.pop(i)
                if i >= len(parsed):
                    break
                char = parsed[i]
            elif char == '-':
                parsed[i-1] = parsed[i-1] - parsed[i+1]
                parsed.pop(i)
                parsed.pop(i)
                if i >= len(parsed):
                    break
                char = parsed[i]
        i += 1
    return parsed[0], allrolls

def roll(cnt, maxroll):
    return [random.randint(1,int(maxroll)) for i in range(int(cnt))]

def rollstr(string):
    if string.count('d') != 1:
        return -1               #Not a supported input
    cnt, maxroll = string.split('d')
    return roll(cnt, maxroll)

def calculate(string):
    string = string.replace(' ','')
    splitbrackets(string)
    allrolls = []
    while True:
        bracket = firstbracket(string)
        if not bracket:
            break
        start, end = bracket
        result, rolls = nbcalculate(string[start+1:end])
        allrolls += rolls
        string = regionreplace(string, str(result), start, end)
    finalresult, rolls = nbcalculate(string)
    return finalresult, allrolls+rolls
