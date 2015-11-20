#!/usr/bin/python3

# Water Monitor
#
# Reads a HMC5883L sensor to detect a magnet spinning inside a water meter.
# Reverses to field strength on the y axis are counted to detect water is flowing.
# Liters in a period are uploaded to grovestreams for graphing.

import time
import datetime
import http.client
import random
import urllib

#from daemonize import Daemonize
from i2clibraries import i2c_hmc5883l

pid = "/tmp/watermon.pid"

# Change 1 to different i2c if needed
hmc5883l = i2c_hmc5883l.i2c_hmc5883l(1)
hmc5883l.setContinuousMode()
hmc5883l.setDeclination(9,54)

# API Key for Grovestreams (should have write and auto create permissions)
grovestreams_apikey = 'XXXXXXXXXXXXXX'

# Name of component at Grovestreams
component_id = "Water"

base_url = '/api/feed?'
conn = http.client.HTTPConnection('www.grovestreams.com')

# How often to publish
publish_delay = 60
# Amount of water per count
liter_per_count = 0.017

old_val = 0
new_val = 0
crossings = 0

last_publish = time.time()

print('Starting collection..')

while True:
    now = time.time()

    (x, y, z) = hmc5883l.getAxes()
    old_val = new_val
    # Only using the y axis due to orientation on meter
    new_val = y
    changed = (old_val < 0 and new_val > 0) or (old_val > 0 and new_val < 0)
    if(changed):
        crossings += 1

    if((now - last_publish) >= publish_delay):
        liters = crossings * liter_per_count
        print("Count: {} Liters: {}".format(crossings,liters))
        try:
            url = base_url + urllib.parse.urlencode({'compId' : component_id,
                               'liters' : liters})
            headers = {"Connection" : "close", "Content-type": "application/json",
                   "Cookie" : "api_key="+grovestreams_apikey}

            print('Uploading feed to: ' + url)
            conn.request("PUT", url, "", headers)
            response = conn.getresponse()
            status = response.status
            if status != 200 and status != 201:
                try:
                    if (response.reason != None):
                        print('HTTP Failure Reason: ' + response.reason + ' body: ' + response.read())
                    else:
                        print('HTTP Failure Body: ' + response.read())
                except Exception:
                    print('HTTP Failure Status: %d' % (status) )

        except Exception as e:
            print('HTTP Failure: ' + str(e))

        finally:
            if conn != None:
                conn.close()

        crossings = 0
        last_publish = now
