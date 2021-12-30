"""
Basic functions that use no imports.
Their job is simply to make everything look nicer.
"""


def simplify_username(username):
    """Simplifies a username since some people may mistype."""
    result = ''
    for c in username:
        n = ord(c)
        if n==124:
            result = ''
        if n==95 or 48 <= n <= 57 or 65 <= n <= 90 or 97 <= n <= 122:
            result += c
    return result


# Time conversion
def time_to_sec(t):
    """Converts an intuitive representation of time to seconds."""
    if t[-1] == 's':
        return int(t[:-1])
    if t[-1] == 'm':
        return 60 * int(t[:-1])
    if t[-1] == 'h':
        return 3600 * int(t[:-1])
    if t[-1] == 'd':
        return 86400 * int(t[:-1])
    if t[-1] == 'w':
        return 604200 * int(t[:-1])
    return -1


def sec_to_time(s, short=True):
    """Converts the amount of seconds to a more intuitive unit (days/hours/minutes)."""
    if s < 0:
        return "<0 seconds"
    resps = ("ms","s","m","h","d","w")
    if not short:
        resps = ("milliseconds","seconds","minutes","hours","days","weeks")
    if s < 0.001:
        return "<1 ms"
    if s < 1:
        return f"{round(s*1000,2)} {resps[0]}"
    if s < 60:
        return f"{round(s,2)} {resps[1]}"
    if s < 3600:
        return f"{s//60} {resps[2]}, {round(s%60,2)} {resps[1]}"
    if s < 86400:
        return f"{s//3600} {resps[3]}, {s%3600//60} {resps[2]}, {round(s%60,2)} {resps[1]}"
    if s < 86400*7:
        return f"{round(s/86400,2)} days"
    return f"{round(s/86400/7,2)} weeks"


# More appealing numbers
def pretty_num(i, sep=','):
    """Prettifies a number by inserting a comma every 3 digits."""
    stri = str(i)
    i = -3
    while i > -len(stri):
        stri = stri[:i] + sep + stri[i:]
        i -= 3 + len(sep)
    return stri


def rank_n(i):
    """Adds the "th" at the end of numbers."""
    stri = str(i)
    if len(stri) >= 2 and stri[-2] == '1':
        return stri+"th"
    if stri[-1] == '1':
        return stri+"st"
    if stri[-1] == '2':
        return stri+"nd"
    if stri[-1] == '3':
        return stri+"rd"
    return stri+"th"


# More appealing strings
def normalize_caps(string):
    """Normalize the capital letters in a string"""
    parts = string.split(' ')
    nstr = ''
    for part in parts:
        nstr += part[0].upper() + part[1:].lower() + ' '
    return nstr
