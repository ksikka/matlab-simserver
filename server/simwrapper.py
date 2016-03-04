# Simulation server
# karanssikka@gmail.com

import matlab.engine
import threading
import Queue
from StringIO import StringIO
import time
import traceback as tb

import logging
logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)

THREAD_SLEEP = 0.1
from util import now


class SimThread(threading.Thread):
    """
    Has a matlab engine.
    Consumes a Q of commands.
    Lazily advances the simulation to the time of the next command
    """
    def __init__(self, sim):
        threading.Thread.__init__(self)
        self.daemon = True
        self.sim = sim

        self.done_event = threading.Event()

    def _eval(self):
        """
        To be run in self.mlthread
        Using async eng eval because blocking call can't be cancelled,
            leaving there no way for us to stop infinite loop
        """
        statement = self.statement
        nargout = self.nargout
        out = StringIO()
        err = StringIO()

        logger.debug(statement + ", nargout=%d"%nargout)
        matlab_future_result = self.eng.eval(statement, nargout=nargout,
            out=out, err=err, async=True)

        while True:
            time.sleep(THREAD_SLEEP)

            if matlab_future_result.done():
                try:
                    ml_result = matlab_future_result.result()
                    self.future.result = (ml_result, out.getvalue(), err.getvalue())
                except Exception as e:
                    self.future.result = (tb.format_exc(e), out.getvalue(), err.getvalue(), True)
                    self.done_event.set()
                out.close()
                err.close()
                return

            elif self.done_event.is_set(): # this is our signal to cancel.
                self.future.result = ('Cancelled', out.getvalue(), err.getvalue())
                matlab_future_result.cancel()
                out.close()
                err.close()
                return

    def eval(self, statement, nargout=1):
        self.statement = statement
        self.nargout = nargout
        self.done_event.clear()
        self.mlthread = threading.Thread(target=self._eval)
        self.mlthread.start()
        self.future.thread = self.mlthread
        self.mlthread.join()

    def cancel(self):
        "Returns true if there was something to cancel."
        try:
            self.done_event.set()
            return True
        except AttributeError:
            return False

    def quit(self):
        self.cancel()
        self.eng.quit()

    def feval(self, fn_lhs, args, nargout=1, prefix=''):
        for i, arg in enumerate(args):
            self.eng.workspace["xtmp_arg%d"%(i+1)] = arg
        statement = prefix + "%s(%s);" % (fn_lhs, ','.join(["xtmp_arg%d"%(i+1) for i in range(len(args))]))
        return self.eval(statement, nargout=nargout)

    def run(self):
        logger.info("Starting matlab engine")
        self.eng = matlab.engine.start_matlab()

        self.eng.workspace['xtmp_codepath'] = str(self.sim.cd_path)
        self.future = Future()
        self.eval("cd(xtmp_codepath);", nargout=0)

        self.sim.t_started = now()
        #TODO security
        self.future = Future()
        self.feval(self.sim.entry_point, self.sim.init_params, nargout=0, prefix='%s = ' % str(self.sim.handle_name))

        while True:
            #t, (action, args, future, persist) = self.sim.q.get()
            data, self.future = self.sim.q.get()
            print "Popped "+repr(data)+" from Q"

            if len(data) == 2:
                statement, nargout = data
                self.eval(statement, nargout=nargout)
            elif len(data) == 3:
                fn_lhs, args, nargout = data
                self.feval(fn_lhs, args, nargout=nargout)
            else:
                assert False


            self.sim.q.task_done()

class Future(object):
    def __init__(self):
        self.result = None
        self.thread = None
    def waitTillDone(self):
        # wait till the thread registers itself w the future
        while self.thread is None:
            time.sleep(THREAD_SLEEP)
        self.thread.join()

class Sim(object):
    def __init__(self, id, cd_path, entry_point,
          handle_name='sim', init_params=None, username=None):
        """
        cd_path is the path to the simulation code,
        entry_point is the file, ie "SimWrapper.m"
        Note that in that case there must be a class inside called "SimWrapper"
        """
        self.id = id
        self.handle_name = handle_name
        self.init_params = init_params if init_params is not None else []
        self.q = Queue.Queue()
        self.thread = SimThread(self)
        self.t_started = None

        assert entry_point.endswith('.m')
        entry_point = entry_point[:-2] # take off the trailing .m

        self.cd_path = cd_path
        self.entry_point = entry_point
        self.username = username

    def start_engine(self):
        self.thread.start()
        # wait for matlab to start up
        while self.t_started is None:
            time.sleep(THREAD_SLEEP)

    def to_dict(self):
        return { 'id' : self.id,
                 'cd_path': self.cd_path,
                 'username': self.username,
                 'entry_point': self.entry_point,
                 'init_params': self.init_params,
                 't_started' : self.t_started,
                 't_elapsed' : now() - self.t_started }

    def eval(self, statement, nargout=1, async=False):
        future = Future()
        self.q.put(([statement, nargout], future))
        if async:
            return future
        future.waitTillDone()
        return future.result

    def feval(self, fn_name, args, nargout=1, async=False):
        future = Future()
        self.q.put(([fn_name, args, nargout], future))
        if async:
            return future
        future.waitTillDone()
        return future.result

    def cancel(self):
        return self.thread.cancel()

    def waitTillIdle(self):
        self.q.join()

    def quit(self):
        self.thread.quit()
