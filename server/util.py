import time
def now():
    "Minutes since the epoch"
    return time.time() / 60

import os
import errno

def mkdirp(p):
    try:
        os.makedirs(p)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(p):
	    pass
	else:
	    raise

import config
if config.WINDOWS:
    import ntfsutils.hardlink

def makehardlink(source, link_name):
    if config.WINDOWS:
        ntfsutils.hardlink.create(source, link_name)
    else:
        os.link(source, link_name)
