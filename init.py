import os
import yaml


def make_dir(folders):
    path = os.path.join(os.getcwd(), *folders)
    try:
        os.mkdir(path)
    except OSError:
        pass


if __name__ == '__main__':
    # Directory structure
    make_dir(['cache'])
    make_dir(['command'])
    make_dir(['command', 'commanddoc'])
    make_dir(['command', 'commandinfo'])
    make_dir(['events'])
    make_dir(['logs'])
    make_dir(['interactions'])
    make_dir(['settings'])
    make_dir(['settings', 'servers'])
    make_dir(['settings', 'settingsdoc'])
    make_dir(['settings', 'settingsinfo'])
    make_dir(['userdata', 'members'])

    # Inputs
    config = {'token': input("Discord bot token: "),
              'dmprefix': input("Default bot prefix: "),
              'api_key': input("Hypixel API key: ")}
    with open(os.path.join(os.getcwd(), "settings", "config.env"), "w") as cfg_file:
        yaml.dump(config, cfg_file)
