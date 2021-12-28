import os, sys
import yaml

#Changing event format since old bot


class CLS_EventFileHandler(object):
    def __init__(self):
        self.path = os.path.join(os.getcwd(), ".events")
#        print(self.path)

    def list(self, path=None):
        flist = []
        if path==None:
            path = self.path
        else:
            path = os.path.join(os.getcwd(), path)

        with os.scandir(path) as eventdir:
            for entry in eventdir:
                if not entry.name.startswith('.') and entry.is_file():
                    flist.append(entry.name)

        return flist

    def find(self, file):
        with os.scandir(self.path) as eventdir:
            for entry in eventdir:
                if entry.name == file:
                    with open(f"\\event\\{file}.txt", "r") as fin:
                        fl = fin.readlines()
        return fl
    def write(self, name, data):
        with open(os.path.join(self.path, f"{name}.txt"), "a") as fout:
            fout.write(data)
    def enable(self, name):
        with open(os.path.join(self.path, f"{name}.txt"), "a") as fout:
            fout.seek(0)
            fout.write("1")
    def disable(self, name):
        with open(os.path.join(self.path, f"{name}.txt"), "a") as fout:
            fout.seek(0)
            fout.write("1")
    def archive(self, filename, dest=".historical events"):
        ext = filename.split('.')[-1]
        fn = filename[:-len(ext)-1]
        shutil.move(os.path.join(self.path, f"{name}.txt"), os.path.join(os.getcwd(), dest, f"{fn}-{time.asctime().replace(':','-')}.{ext}"))
        return

    def delete(self, pos):
        try:
            if not 'py' in pos:
                os.remove(f"{self.path}\\{pos}")
                return 0
            else:
                return -1
        except FileNotFoundError:
            return -2

    def extend(self, file, length):
        pass

    def modify(self, file, line, newarg):
        with open(f"\\event\\{file}.txt", "r") as fin:
            fl = fin.readlines()
        fl[line] = str(newarg)+'\n'
        with open(f"\\event\\{file}.txt", "w") as fout:
            for l in fl:
                fout.write(fl)
