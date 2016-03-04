# Simulation server
# Meant to run on one worker process only.
# karanssikka@gmail.com

import Pyro.core
""" TO DEBUG
Pyro.config.PYRO_TRACELEVEL = 3
Pyro.config.PYRO_USER_TRACELEVEL = 3
"""
from simwrapper import Sim
import os
join = os.path.join
from config import config

# FYI this is global
pyro_daemon = None

import json
import hashlib
import time
from snapshot import snapshot, clean_snapshots


def gen_snap_name(username, proj, mainfile, unixtime_sec, params):
    h = hashlib.sha1()
    h.update(str(unixtime_sec))
    h.update(json.dumps(params))
    return "%s-%s-%s-%s" % (username, proj, mainfile, h.hexdigest())

import logging
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

class SimMgr(object):
    """Appears to be not much more than a network-accessible list.
       Actually it's a dictionary so we have handles to the simulation objects so we can delete them and do other things to them in bulk.

        -List simulation guids
        -Create a simulation
        -Delete a simulation (TODO)
    """
    def __init__(self):
        ## Key is GUID, value is Sim Proxy object.
        self.simulations = {}
        # ( each sim can be accessed by sim_proxy.delegate )

        self._sims_in_creation = [] # list of ids, used to prevent race conditions.

    def list(self):
        "Return a list of simulations"
        logger.info("Call to list")
        return [sim.delegate.to_dict() for sim in self.simulations.values()]

    def list_by_id(self):
        logger.info("Call to list by id")
        return { sim_id : sim.delegate.to_dict() for sim_id, sim in self.simulations.iteritems() }

    def create(self, username, sim_proj_dir, sim_file, handle_name='sim', params=None, make_snapshot=True):
        logger.info("Creating Simulation for "+username)
        code_path = join(config['SIM_STORAGE_DIR'], 'users', username, sim_proj_dir)

        obj = Pyro.core.ObjBase()
        self._sims_in_creation.append(obj.GUID())
        try:

            if make_snapshot:
                logger.info("Making snapshot of " + code_path)
                snap_name = gen_snap_name(username, sim_proj_dir, sim_file, int(time.time()), params)
                snapshot(code_path, snap_name)

                old_code_path = code_path
                code_path = join(config['SIM_STORAGE_DIR'], 'sim_snapshots', snap_name)
            else:
                logger.info("Skipping snapshot, using " + code_path + " directly")

            s = Sim(obj.GUID(), code_path, sim_file,
                handle_name=handle_name, init_params=params, username=username)
            s.start_engine()

            obj.delegateTo(s)
            pyro_daemon.connect(obj,'s:'+obj.GUID())

            self.simulations[obj.GUID()] = obj

        finally:

            self._sims_in_creation.remove(obj.GUID())

        return s.to_dict()

    def clean_snapshots(self):
        "Delete unused snapshots"
        try:
            clean_snapshots(self.simulations.keys() + self._sims_in_creation)
        except Exception:
            import traceback; traceback.print_exc()
            pass
        return True

    def delete(self, guid):
        if guid in self.simulations:
            sim_remote = self.simulations[guid]
            sim = sim_remote.delegate
            pyro_daemon.disconnect(sim_remote)
            sim.cancel()
            sim.quit()
            del self.simulations[guid]

        return self.clean_snapshots()


def init():
    global pyro_daemon
    Pyro.core.initServer(banner=1)

    pyro_daemon = Pyro.core.Daemon(host='0.0.0.0', port=config['BACKEND_PORT'])

    mgr = SimMgr()
    mgr_pyro = Pyro.core.ObjBase()
    mgr_pyro.delegateTo(mgr)
    pyro_daemon.connect(mgr_pyro, 'mgr')

if __name__ == "__main__":
    init()
    print "Listening on 0.0.0.0:%d" % pyro_daemon.port
    pyro_daemon.requestLoop()
