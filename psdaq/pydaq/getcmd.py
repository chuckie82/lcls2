#!/usr/bin/env python
"""
CM get command
"""
#import random
import time
import zmq
import pickle
import pprint
from CMMsg import CMMsg

def main():

    # Prepare our context and DEALER socket
    ctx = zmq.Context()
    cmd = ctx.socket(zmq.DEALER)
    cmd.linger = 0
    cmd.RCVTIMEO = 5000 # in milliseconds
    cmd.connect("tcp://localhost:5556")

    cmd.send(CMMsg.GETSTATE)
    while True:
        try:
            msg = cmd.recv_multipart()
        except Exception as ex:
            print(ex)
            return

        request = msg[0]
        if request == CMMsg.STATE:
            print ("I: Received STATE")
            if len(msg) == 4:
                props = pickle.loads(msg[3])

                # platform
                platform = 0
                try:
                    platform = props['platform']
                except:
                    print('E: platform key not found')
                print ('Platform:', platform)

                # partition name
                partName = '(None)'
                try:
                    partName = props['partName']
                except KeyError:
                    print('E: partName key not found')
                print ('Partition name:', partName)

                # nodes
                nodes = []
                try:
                    nodes = pickle.loads(props['nodes'])
                except Exception:
                    print('E: nodes key not found')
                print ('Nodes:')
                pprint.pprint (nodes)
            else:
                print ("E: STATE message len %d, expected 4" % len(msg))
            break          # Done
        else:
            print ("W: Received key \"%s\"" % request)
            continue

    print ("Done")

if __name__ == '__main__':
    main()
