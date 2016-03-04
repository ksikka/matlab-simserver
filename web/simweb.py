# Web app: Handle end-user requests and fwd them to the right service
# karanssikka@gmail.com


from flask import Flask, render_template, redirect, request, g

MOCK = False
BACKEND_PORT = 17766

TIMEOUT_LIST = 15
TIMEOUT_CREATE = 45
TIMEOUT_SYNC = 600
CT_JSON = {'Content-type': 'application/json'}


import os
join = os.path.join
import json
from util import MatlabEncoder, safeint, unicode_to_ascii
from util import now


def validate_username(username):
    return username.isalnum() and len(username) <= 10
def validate_sim_name(sim_name):
    if '..' in sim_name:
        return False
    toks = sim_name.split('/')
    if len(toks) != 2:
        return False
    sim_proj_dir, sim_file = toks
    if not sim_file.endswith('.m'):
        return False

    # TODO validate this with the backend.
    return True
    """
    return os.path.isdir(join(config['STORAGE_DIR'], 'users', g.username, sim_proj_dir)) and \
            os.path.isfile(join(config['STORAGE_DIR'], 'users', g.username, sim_proj_dir, sim_file))
    """


class SimClient(object):
    def __init__(self):
        pass
    def performAction(self, action, args):
        pass

from collections import defaultdict
class SimMgrClient(object):
    def __init__(self):
        self._list_cached = [] # will be a list of simulation dicts
        self._list_cached_time = now()

        self.user_to_sim_id = defaultdict(list)

    def _setTimeout(self, *args, **kwargs):
        return g.mgr_proxy._setTimeout(*args, **kwargs)

    def create(self, username, sim_name, params, handle_name='sim',
            make_snapshot=True):
        "name snap username-simname-<hash timestamp and params>"
        assert validate_username(username)
        assert validate_sim_name(sim_name), sim_name

        sim_proj_dir, sim_file = sim_name.split('/')

        g.mgr_proxy._setTimeout(TIMEOUT_CREATE)
        print params
        sim_dict = g.mgr_proxy.create(str(username), str(sim_proj_dir), str(sim_file),
            handle_name=handle_name, params=params, make_snapshot=make_snapshot)

        self.user_to_sim_id[username].append(sim_dict['id'])

        return sim_dict['id']

    def delete(self, guid):
        return g.mgr_proxy.delete(guid)

    def list(self, username=None):
        """
        Return a tuple of stale time, list of sim dicts
        if stale time is 0, this is fresh data.
        """
        g.mgr_proxy._setTimeout(TIMEOUT_LIST)
        try:
            sims = g.mgr_proxy.list()
            t_elapsed_since_last_call = 0

            self._list_cached = sims
            self._list_cached_time = now()

        except ProtocolError:
            traceback.print_exc(3)
            sims = self._list_cached
            t_elapsed_since_last_call = now() - self._list_cached_time

        if username is not None:
            filtered_sims = []
            for s in sims:
                if username == s['username']:
                    filtered_sims.append(s)
            sims = filtered_sims

        return sims, t_elapsed_since_last_call


def init_mgr_proxy():

    import Pyro.core

    Pyro.core.initClient()
    mgr_proxy = Pyro.core.getProxyForURI("PYROLOC://localhost:"+str(BACKEND_PORT)+"/mgr")

    return mgr_proxy

mgr_proxy = SimMgrClient()


def init_sim_proxy(guid):
  if MOCK:
    obj = mgr_proxy.simulations.get(guid)
    if obj is not None:
      return obj.delegate
    else:
      return None
  else:
      import Pyro.core
      obj = Pyro.core.getProxyForURI("PYROLOC://localhost:"+str(BACKEND_PORT)+"/s:"+guid)
      return obj


app = Flask(__name__)
app.debug = True

@app.before_request
def get_user():
    g.username = 'dduke'

"""Can't share proxies accross threads..."""
from threading import local
thread_local = local()

@app.before_request
def get_mgr_proxy():
    if not hasattr(thread_local, 'mgr_proxy'):
        thread_local.mgr_proxy = init_mgr_proxy()

    g.mgr_proxy = thread_local.mgr_proxy

from Pyro.errors import ProtocolError

import traceback
@app.route('/sync_users/', methods=['POST'])
def sync_users():
    g.mgr_proxy._setTimeout(TIMEOUT_SYNC)
    g.mgr_proxy.sync_storage()
    return 'ok'

@app.route('/')
def home():
    sim_list, t_elapsed_since_last_call = mgr_proxy.list(g.username)
    sim_json_list = [json.dumps(sim) for sim in sim_list]

    return render_template('index.html',
            sim_list_with_json=zip(sim_list, sim_json_list),
            sim_type_list=['DemoSim/SimWrapper.m'],
            t_elapsed_since_last_call=t_elapsed_since_last_call)

@app.route('/sim/create/', methods=['POST'])
def create_sim():
    sim_name = request.form.get('sim_name','')
    params_json = request.form.get('params_json','')
    handle_name = request.form.get('handle_name','sim')
    make_snapshot = request.form.get('make_snapshot', False)
    try:
        params = unicode_to_ascii(json.loads(params_json))
    except ValueError:
        return 'Params not a valid JSON', 400

    try:
        guid = mgr_proxy.create(g.username, sim_name, params, make_snapshot=make_snapshot)
    except ProtocolError:
        traceback.print_exc()
        return 'Backend down', 503

    return json.dumps({'guid':guid}), 200, CT_JSON
	
@app.route('/sim/create/rdr/', methods=['POST'])
def create_sim_rdr():
    returned_tuple = create_sim()
    code = returned_tuple[1]
    if code == 200:
        return redirect('/')
    else:
        return returned_tuple

@app.route('/sim/<guid>/delete/', methods=['POST'])
def sim_delete(guid):
    sim = init_sim_proxy(guid)
    if sim is None:
        return ('No sim found', 404)
    return json.dumps(mgr_proxy.delete(guid)), 200, CT_JSON

"""
All POST requests, urlencoded, except the args_json should be a json string..
(Values not urlencoded below for clarity. After urlencoding they should look more like gibberish.)

To get result of 1+1:

    POST /sim/<guid>/eval/
    ?statement=1 + 1&nargout=1

To get result of sim.getThreeStats('yo',5):

    POST /sim/<guid>/feval/
    ?fn_name=sim.getThreeStats&args_json=['yo',5]&nargout=3

    or equivalently, using eval instead,

    POST /sim/<guid>/eval/
    ?statement=sim.getThreeStats('yo',5)&nargout=3
"""

@app.route('/sim/<guid>/eval/', methods=['POST'])
def sim_eval(guid):
    statement = request.form.get('statement', None)
    if statement is None:
        return 'missing statement', 400
    nargout = safeint(request.form.get('nargout'))
    if nargout is None:
        nargout = 1

    sim = init_sim_proxy(guid)
    result = sim.eval(str(statement), nargout=nargout)
    return json.dumps(result, cls=MatlabEncoder), 200, CT_JSON

@app.route('/sim/<guid>/feval/', methods=['POST'])
def sim_feval(guid):
    fn_name = request.form.get('fn_name', None)
    args_json = request.form.get('args_json', '[]')
    if fn_name is None:
        return 'missing fn_name', 400
    try:
        args = unicode_to_ascii(json.loads(args_json))
    except ValueError:
        return 'Args not a valid JSON', 400

    nargout = safeint(request.form.get('nargout'))
    if nargout is None:
        nargout = 1

    sim = init_sim_proxy(guid)
    if sim is None:
        return ('No sim found', 404)

    result = sim.feval(str(fn_name), args, nargout=nargout)
    return json.dumps(result, cls=MatlabEncoder), 200, CT_JSON

@app.errorhandler(ProtocolError)
def handle_pyro_unreachable(e):
    traceback.print_exc()
    return 'Backend down', 503


import os
from flask import send_from_directory

@app.route('/favicon.ico')
def favicon():
      return send_from_directory(os.path.join(app.root_path, 'static'),
                                         'favicon.ico', mimetype='image/vnd.microsoft.icon')

import sys
try:
    PORT = int(sys.argv[1])
except (ValueError, IndexError):
    PORT = 8000

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, threaded=True)

