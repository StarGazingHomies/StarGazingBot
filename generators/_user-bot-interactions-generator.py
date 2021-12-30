import yaml

CONTAIN = [(('oops',), ('`YOU IDIOT`',)),
           (('alot',), ('`a lot*`',)),
           ]

MATCHING = [(('hi', 'hello',), ('Check this out! <https://nohello.net/>',)),
            ]

yaml.dump(CONTAIN, open("../interactions/contain.yaml", "w"))
yaml.dump(MATCHING, open("../interactions/matching.yaml", "w"))
