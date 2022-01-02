"""
Generates necessary configuration files for commands.
Includes permissions, cooldown, etc.
Format: (commandinfo/commands.yaml)

(category):
 - commandname: {exec, commonname, permission, cooldown}
 - commandname2: {exec, commonname, permission, cooldown}

"""

# TODO: change this system into decorators (avoids files)

import yaml

mane_subcommands = {'featured':
                        {'exec': 'CMD_featured',
                         'commonname': 'featured',
                         'permission': 1,
                         'cooldown': 0},

                    'f':
                        {'alias': 'featured'},

                    'pick':
                        {'exec': 'CMD_random',
                         'commonname': 'pick',
                         'permission': 1,
                         'cooldown': 0},

                    'search':
                        {'exec': 'CMD_search',
                         'commonname': 'search',
                         'permission': 1,
                         'cooldown': 30}
                    }

minecraft_subcommands = {'start':
                             {'exec': 'CMD_start',
                              'commonname': 'start',
                              'permission': 5,
                              'cooldown': 0},

                         'stop':
                             {'exec': 'CMD_stop',
                              'commonname': 'stop',
                              'permission': 5,
                              'cooldown': 0}
                         }
# yaml.dump(MINECRAFTSUBCOMMANDS, open("mcsubcmds.yaml","w"))

mojang_subcommands = {'getuuid':
                          {'exec': 'CMD_uuid',
                           'commonname': 'getuuid',
                           'permission': 1,
                           'cooldown': 0},

                      'getusername':
                          {'exec': 'CMD_username',
                           'commonname': 'getusername',
                           'permission': 1,
                           'cooldown': 0}
                      }

hypxiel_subcommands = {'stats':
                           {'exec': 'CMD_Skyblock_getstats',
                            'commonname': 'stats',
                            'permission': 1,
                            'cooldown': 0},

                       'getstats':
                           {'alias': 'stats'},

                       'skill':
                           {'exec': 'CMD_Skyblock_skill',
                            'commonname': 'skill',
                            'permission': 1,
                            'cooldown': 0},

                       'skills':
                           {'alias': 'skill'},

                       'gw':
                           {'alias': 'weight'},

                       'we':
                           {'alias': 'weight'},

                       'getweight':
                           {'alias': 'weight'},

                       'weight':
                           {'exec': 'CMD_Skyblock_getweight',
                            'commonname': 'weight',
                            'permission': 1,
                            'cooldown': 0},

                       'w':
                           {'alias': 'weight'},

                       'r':
                           {'alias': 'reqs'},

                       'req':
                           {'alias': 'reqs'},

                       'reqs':
                           {'exec': 'CMD_Skyblock_Reqs',
                            'commonname': 'reqs',
                            'permission': 1,
                            'cooldown': 0},

                       'requirements':
                           {'alias': 'reqs'},

                       'glb':
                           {'exec': 'CMD_guildleaderboard',
                            'commonname': 'glb',
                            'permission': 2,
                            'cooldown': 1200},

                       'guildleaderboard':
                           {'alias': 'glb'},

                       'loopglb':
                           {'exec': 'CMD_Skyblock_glb_loop_command',
                            'commonname': 'loopglb',
                            'permission': 2,
                            'cooldown': 0},

                       'event':
                           {'exec': 'CMD_Skyblock_event',
                            'commonname': 'event',
                            'permission': 2,
                            'cooldown': 0}
                       }

# This includes categories: general, staff, fun
# These commands are not in a particular namespace.
general_commands = {'eval':
                        {'exec': 'CMD_eval',
                         'commonname': 'eval',
                         'permission': 5,
                         'cooldown': 0},

                    'exec':
                        {'exec': 'CMD_exec',
                         'commonname': 'exec',
                         'permission': 5,
                         'cooldown': 0},

                    'settings':
                        {'exec': 'CMD_user_settings',
                         'commonname': 'settings',
                         'permission': 1,
                         'cooldown': 0},

                    'config':
                        {'exec': 'CMD_server_settings',
                         'commonname': 'config',
                         'permission': 3,
                         'cooldown': 0},

                    'prefix':
                        {'exec': 'CMD_prefix',
                         'commonname': 'prefix',
                         'permission': 3,
                         'cooldown': 0},

                    'about':
                        {'exec': 'CMD_about',
                         'commonname': 'about',
                         'permission': 1,
                         'cooldown': 0},

                    'status':
                        {'exec': 'CMD_status',
                         'commonname': 'status',
                         'permission': 1,
                         'cooldown': 0},

                    'help':
                        {'exec': 'CMD_help',
                         'commonname': 'help',
                         'permission': 1,
                         'cooldown': 0},

                    'h':
                        {'alias': 'help'},

                    'ping':
                        {'exec': 'CMD_latency',
                         'commonname': 'latency',
                         'permission': 1,
                         'cooldown': 0},

                    'latency':
                        {'alias': 'ping'},

                    'say':
                        {'exec': 'CMD_say',
                         'commonname': 'say',
                         'permission': 2,
                         'cooldown': 0},

                    'echo':
                        {'exec': 'CMD_echo',
                         'commonname': 'echo',
                         'permission': 3,
                         'cooldown': 0},

                    'apply':
                        {'exec': 'CMD_apply',
                         'commonname': 'apply',
                         'permission': 1,
                         'cooldown': 7200},

                    'verify':
                        {'exec': 'CMD_verify',
                         'commonname': 'verify',
                         'permission': 1,
                         'cooldown': 0},

                    'report':
                        {'exec': 'CMD_report',
                         'commonname': 'report',
                         'permission': 1,
                         'cooldown': 0},

                    'pingowner':
                        {'exec': 'CMD_pingowner',
                         'commonname': 'pingowner',
                         'permission': 1,
                         'cooldown': 1200},

                    'perms':
                        {'exec': 'CMD_perms',
                         'commonname': 'perms',
                         'permission': 1,
                         'cooldown': 1200},

                    'addrole':
                        {'exec': 'CMD_addrole',
                         'commonname': 'addrole',
                         'permission': 3,
                         'cooldown': 0},

                    'nick':
                        {'exec': 'CMD_nick',
                         'commonname': 'nick',
                         'permission': 2,
                         'cooldown': 0},

                    'stop':
                        {'exec': 'stop',
                         'commonname': 'stop',
                         'permission': 5,
                         'cooldown': 0},

                    'nevermind':
                        {'exec': 'nevermind',
                         'commonname': 'nevermind',
                         'permission': 5,
                         'cooldown': 0},

                    'temp':
                        {'exec': 'temp',
                         'commonname': 'temp',
                         'permission': 5,
                         'cooldown': 0},

                    'clean':
                        {'exec': 'CMD_clean',
                         'commonname': 'clean',
                         'permission': 2,
                         'cooldown': 0},

                    'move':
                        {'exec': 'CMD_move',
                         'commonname': 'move',
                         'permission': 2,
                         'cooldown': 0},

                    'roll':
                        {'exec': 'CMD_roll',
                         'commonname': 'roll',
                         'permission': 1,
                         'cooldown': 0},

                    'points':
                        {'exec': 'CMD_points',
                         'commonname': 'points',
                         'permission': 1,
                         'cooldown': 7200},

                    'invite':
                        {'exec': 'CMD_invite',
                         'commonname': 'invite',
                         'permission': 1,
                         'cooldown': 0},

                    }
commandmap = {
    'general': general_commands,
    'hypixel': hypxiel_subcommands,
    'minecraft': minecraft_subcommands,
    'mojang': mojang_subcommands,
    'manebooru': mane_subcommands
}

yaml.dump(commandmap, open("../command/commandinfo/commandmap.yaml", "w"))

namespace_alias = {
    'mane': 'manebooru'
}

yaml.dump(namespace_alias, open("../command/commandinfo/namespacealias.yaml", "w"))

# No aliases will be here for no repeats!
CMCATEGORYMAP = {'eval': 'Bot Owner',
                 'exec': 'Bot Owner',
                 'settings': 'WIP',
                 'config': 'WIP',
                 'prefix': 'WIP',
                 'about': 'General',
                 'status': 'General',
                 'help': 'General',
                 'ping': 'General',
                 'say': 'General',
                 'echo': 'General',
                 'apply': 'General',
                 'report': 'General',
                 'pingowner': 'Fun',
                 'perms': 'General',
                 'getuuid': 'Minecraft',
                 'getusername': 'Minecraft',
                 'stats': 'Skyblock',
                 'skills': 'WIP',
                 'addrole': 'WIP',
                 'weight': 'Skyblock',
                 'reqs': 'WIP',
                 'pets': 'WIP',
                 'guildleaderboard': 'Skyblock',
                 'loopglb': 'Skyblock',
                 'event': 'WIP',
                 'nick': 'Staff',
                 'stop': 'Bot Owner',
                 'nevermind': 'Bot Owner',
                 'temp': 'WIP',
                 'clean': 'Staff',
                 'move': 'Staff',
                 'verify': 'General',
                 'featured': 'Manebooru',
                 'pick': 'Manebooru',
                 'search': 'Manebooru',
                 'points': 'General',
                 'roll': 'Fun',
                 'invite': 'General'}
yaml.dump(CMCATEGORYMAP, open("../command/commandinfo/ctgymap.yaml", "w"))
