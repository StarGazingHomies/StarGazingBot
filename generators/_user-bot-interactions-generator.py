import yaml

CONTAIN = [( ('oops',), ('`YOU IDIOT`',) ),\
           ( ('alot',), ('`a lot*`',) ),\
           ]


MATCHING = [( ('hi', 'hello',), ('Check this out! <https://nohello.net/>',) ),\
            ]

    
yaml.dump(CONTAIN, open("contain.yaml","w"))
yaml.dump(MATCHING, open("matching.yaml","w"))
