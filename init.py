import os


def make_dir(folders):
    path = os.path.join(os.getcwd(), *folders)
    try:
        os.mkdir(path)
    except OSError:
        pass


if __name__ == '__main__':
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
