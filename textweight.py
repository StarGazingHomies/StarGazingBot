#This file, along with dictionaries that come with it, is a heavy WIP that
#tries to map a user's message into a weight based on contents

#Do not expect this to be fully functional until 2022.

#Maybe someday I will add AI to this xD

import json
import math

with open("words_dictionary.json") as f:
    words = json.load(f)

common_symbols = ('.',',',';',':','-','!','?','(',')','\"','\'','*','>','<','[',']')

def dictlookup(word):
    #Probably a replaced newline
    if word == '':
        return 0
    word = word.lower()
    try:
        #Remove the last punctuation, if there is any
        if word[-1] in common_symbols:
            word = word[:-1]
        if word[0] in common_symbols:
            word = word[1:]
        #Base weight is 1 if the word is an English word. May change sometime in the future.
        w = words[word]
        #If the user avoids using 'e', they get a cookie!
        if word.count('e') == 0:
            w += 1
        #If the word is long, reward more points. Users should spice up their language.
        w += (len(word)-5)//3
        return w
    #If the word is not an English word
    except KeyError:
        return -2

def analyzeword(word):
    #Someone typed a space at the end of a sentence.
    if word == '':
        return ('regular',0)
    #The return values indicate type.
    if word[-1] in common_symbols:
        word = word[:-1]
    #Emoji
    if word.startswith(":"):
        return ('emoji',0)
    #Link
    elif word.count('.') >= 1 and word[-1] != '.':
        return ('link',0)
    #Ping
    elif word.startswith("<@"):
        return ('ping',0)
    #Other discord internals
    elif word.startswith('<'):
        return ('discinternal',0)
    #12 letters or higher -->
    #bansheeificationizing should be a word
    changecnt = 0
    flag = 0
    caps = 0
    for char in word:
        n = ord(char)
        if ord('a') <= n <= ord('z') or ord('A') <= n <= ord('Z'):
            if ord('A') <= n <= ord('Z'):
                caps += 1
            if flag == 2:
                changecnt += 1
            flag = 1
        elif ord('0') <= n <= ord('9'):
            if flag == 1:
                changecnt += 1
            flag = 2
        elif char in common_symbols:
            pass
        else:
            #Probably a common emoji made from characters.
            return ('symbol',0)
    #Many changes between letters and numbers. Perhaps this person's cat walked over the keyboard?
    if changecnt >= 3:
        return ('gibberish',0)
    result = dictlookup(word)
    
    #Long word that isn't in the dictionary
    if len(word) > 12 and result == -2:
        return ('gibberish',0)
    
    #Excessive caps
    if caps > 4:
        return ('caps',result)

    #Normal word, or shorthand for something! Yay!
    return ('regular',result)

def wordalone(word):
    result, pts = analyzeword(word)
    if result == 'emoji':
        return 2
    elif result == 'link':
        return 1
    elif result == 'ping':
        return 0
    elif result == 'symbol':
        return 1
    elif result == 'gibberish':
        return -1
    elif result == 'caps':
        return pts-1 if pts>=1 else 0
    elif result == 'regular':
        return pts+2 if pts>=-2 else 0
    else:
        return 0

def wordinsentence(word):
    """Converts a word into points.
Return values:
Tuple (<int>, <string>)
<int> - the points awarded
<string>
'norm'  - normal
'clear' - no points for this message, as it does not make sense.
'div'   - Add to divider, as certain elements may be offensive."""
    result, pts = analyzeword(word)
    if result == 'emoji':
        return (1, 'norm')
    elif result == 'link':
        return (0, 'norm')
    elif result == 'ping':
        return (0, 'norm')
    elif result == 'discinternal':
        return (2, 'norm')
    elif result == 'symbol':
        return (2, 'norm')
    elif result == 'gibberish':
        return (-15,"div")
    elif result == 'caps':
        return (pts-1 if pts >=  1 else 0, 'div' )
    else:
        return (pts+1 if pts >= -1 else 0, 'norm')

def weigh(text):
    #First, I will have to analyze each message for its contents.
    #The amount of links, emojis, and other stuff.

    #Maybe something went wrong!
    if text == '':
        return 0

    #Probably a command
    if text[:3] in ('at!','at/') or text[0] in ('!','$','?','&',';',',','.','/'):
        return 0

    spaces = text.count(' ')

    #Single word messages, emojis, or links
##    if spaces <= 3:
##        r = 0
##        for word in text.split(' '):
##            r += wordalone(word)
##        return r

    paragraphcount = text.count('\n')
    text = text.replace('\n',' ')
    weight = 0
    wordcnt = spaces + 1
    div = 0

    #Weight of every word
    lastword = None
    for word in text.split(' '):
        r, mod = wordinsentence(word)
        if mod == 'clear':
            return -1
        if mod == 'div':
            div += 1
        weight += r
        if lastword == word:
            #Repeating words! LESS POINTS!
            div += 2
        lastword = word
#        print(f"The word '{word}' gained {r} xp!")

    #Word count bonus weight
    #\frac{97x}{\left(\frac{x}{8}\right)^{2}+15}            (desmos)
    weight += (wordcnt * 97) / ((wordcnt/8)**2 + 15)
    weight *= math.log(wordcnt + 10, 10) * 2.6 - 2.6
    if paragraphcount != 0 and wordcnt // paragraphcount <= 15:
        #Paragraph vs word ratio not ideal (too many newlines)
        div += 15 - (wordcnt // paragraphcount)

#    print(f"Due to the length of the sentence, the user gained {(wordcnt * 97) / ((wordcnt/8)**2 + 15)} more xp!")

    #80% gain rate after 100
    #50% gain rate after 300
    #Hard cap at 1000           - the final weight will not go crazy high if you write paragraphs!
    if weight > 300:
        weight = 0.5*weight+125 #Simplified
        print(f"Loss of {round(0.5*weight -70,2)} weight due to soft cap at 150.")
    elif weight > 100:
        weight = 0.8*weight+20
        print(f"Loss of {round(0.2*weight -20,2)} weight due to soft cap at 100.")
    if weight > 1000:
        weight = 1000
        print("Hard cap of weight at 1000.")

    #Tolerance of 1 word with caps, which is why div is 0
    if div == 0:
        div = 1

    return weight // div

    
