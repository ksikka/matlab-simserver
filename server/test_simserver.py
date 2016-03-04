# Simulation server
# karanssikka@gmail.com

from simwrapper import Sim
from simserver import SimMgr

print "Testing sim mgr"
# Test Creation
mgr = SimMgr()

s1uuid = mgr.create()
assert len(mgr.list()) == 1

mgr.delete(s1uuid)
assert len(mgr.list()) == 0


print "Testing sim init"
# Test Sims themselves.
s = Sim()
s.init()
print "Testing sim getstate"
# tests that getting state at various times
# works as expected
r100 = s.getStateAt(100)
assert s.t == 100

r200 = s.getStateAt(200)
assert s.t == 200
assert r100 != r200

r100_2 = s.getStateAt(100)
assert s.t == 200
assert r100 == r100_2

print "Testing performaction"
# This blocks
s.performAction("eat", [50], 350, async=False)
assert s.t == 350

# This doesn't block
s.performAction("eat", [50], 500)
assert s.t == 350
s.waitTillIdle()
assert s.t == 500

"""
These tests are highly nondeterministic, they work when laptop is in power saving mode and cpu is slow.

"""
# Events happen in a priority Q fashion,
#   so that we don't have to wait for Future events to finish
#   before accessing already computed data.
#   Also this makes it harder to accidentally go back in time.
s.performAction("eat", [50], 10750)
# 1st eat starts executing since Q was empty prior to this.
s.performAction("eat", [50], 20900)
# 2nd eat gets queued up.
s.getStateAt(10700)
# 3. getState gets added to Q, and the above call blocks until it completes
assert s.t == 10750
# 1st eat has occured 1st, then getStateAt, then 2nd eat.
s.waitTillIdle()
assert s.t == 20900
