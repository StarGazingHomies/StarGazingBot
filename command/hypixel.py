cmdinfopath = os.path.join(os.getcwd(), 'command', 'commandinfo')
with open(os.path.join(cmdinfopath,"hysubcmds.yaml"),"r") as f:
    HYPIXELSUBCMDS = yaml.safe_load(f)
