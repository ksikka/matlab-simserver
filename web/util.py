import time
def now():
    "Minutes since the epoch"
    return time.time() / 60

import json
from matlab import mlarray

class MatlabEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, mlarray.double):
			return list(obj)
		return json.JSONEncoder.default(self, obj)

def unicode_to_ascii(o):
    t = type(o)
    if t == unicode:
        return str(o)
    if t == dict:
        return {unicode_to_ascii(k): unicode_to_ascii(v) for k,v in o.iteritems()}
    if t == list:
        return [unicode_to_ascii(v) for v in o]
    else:
        return o

def safeint(i):
    "This wont throw an exception. It will return int | none."
    try:
        return int(i)
    except (ValueError, TypeError):
        return None
