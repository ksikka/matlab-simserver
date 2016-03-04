import json
import os.path

import platform
WINDOWS = platform.system() == 'Windows'

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
if WINDOWS:
    DEFAULTS = os.path.join(BASE_PATH, "defaults_windows.json")
else:
    DEFAULTS = os.path.join(BASE_PATH, "defaults_linux.json")
CURRENT = os.path.join(BASE_PATH, "settings.json")


from threading import Lock


save_lock = Lock()


def save():
    save_lock.acquire()
    with open(CURRENT, "w") as f:
        json.dump(config, f)
    save_lock.release()

config = None

def load():
    global config
    with open(CURRENT) as f:
        config = json.load(f)

import logging

if not os.path.exists(CURRENT):
    logging.warn("Config file not found, copying from "+DEFAULTS)
    with open(DEFAULTS) as f:
        data = json.load(f)
    with open(CURRENT, "w") as f:
        json.dump(data, f)

load()
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)
