# Run from psana machine, source setup_env.sh
import numpy as np
import dgramCreate as dc
import base64
import zmq

from psana.dgrammanager import DgramManager
from psana import DataSource

import sys, os

outdir = sys.argv[1]
fname  = sys.argv[2]

if len(sys.argv) < 3: 
    print("Usage: python trans.py paths filename")
    print("Example: python trans.py /reg/common/package/temp crystal_xray")

context = zmq.Context()
# receive work
consumer_receiver = context.socket(zmq.PULL)
consumer_receiver.connect("tcp://127.0.0.1:5557")

def munge_json(event):
    if 'done' in event:
        return None, None
    else:
        for key,val in event['data'].items():
            try:
                event['data'][key]= np.frombuffer(base64.b64decode(val[0]), dtype = np.dtype(val[2])).reshape(val[1])
            except TypeError:
                pass
            event_dict = event['data']
            timestamp = event['timestamp']
        return event_dict, timestamp

def translate_xtc_demo(job_type):
    event_file = '%s_evts.xtc' % job_type

    ninfo = dc.nameinfo('DsdCsPad', 'cspad', 'detnum1234', 0)
    alg = dc.alg('raw', [1, 2, 3])

    cydgram = dc.CyDgram()

    with open(event_file, 'wb') as f:
        while True:
            work = consumer_receiver.recv_json()
            event_dict, timestamp = munge_json(work)
            if event_dict is None: break
            cydgram.addDet(ninfo, alg, event_dict)
            df = cydgram.get(timestamp,0,0)
            f.write(df)

    print("Output: ", event_file)

# Examples
# The LCLS1 dgrams are organized differently than the LCLS2 version
# In LCLS2, the configure contains all the names in the subsequent event dgrams
# This isn't the case for LCLS1, so I define the first event as a pseudo-configure
# and the second event as a configure for the rest of the events
# There is an edge case for the crystal data, as the second event is blank
# This causes a segfault when loading the LCLS2 xtc file with DgramManager
# My workaround is to define the second event as the configure for the events
# with the optional offset argument to translate_xtc_demo


#translate_xtc_demo(os.path.join(outdir,'jungfrau'))
#translate_xtc_demo(os.path.join(outdir,'epix'))
#translate_xtc_demo(os.path.join(outdir,'crystal_dark'), 2)
translate_xtc_demo(os.path.join(outdir, fname))