import yaml

CONTAIN = [(('friday',), ('`It\'s friday you duhrling shits!`',)),
           (('hax', 'hacks', ), ('`gaming chair*`', )),
           (('pony',), ('<:cclove:929140947428704266>', )),
           (('silly',), (''))
           ]

MATCHING = [(('lol',), ('<:rdofl:899090292513333259>',)),
            (('hi', 'hello'), ('<a:ponkwave1:929142538076581958>',
                               '<a:ponkwave2:929142538458251304>',
                               '<a:ponkwave3:929142538491801650>',
                               '<a:ponkwave4:929142539498438686>',
                               '<a:derpiwave:929142538928017471>',
                               '<a:flutterwave:929142538814758942>',
                               '<a:sunsetwave:929142799910174802>'))
            ]

yaml.dump(CONTAIN, open("../interactions/contain.yaml", "w"))
yaml.dump(MATCHING, open("../interactions/matching.yaml", "w"))
