#!/usr/bin/python3 -u

# Water Monitor
#
# Reads a HMC5883L sensor to detect a magnet spinning inside a water meter.
# Reverses to field strength on the y axis are counted to detect water is flowing.
# Liters in a period are uploaded to grovestreams for graphing.
#
# Derived from http://seductiveequations.com/2015/11/09/water-meter.html and
# ported to python from wiring.
#
# Requires Think Bowl i2c Libraries from http://think-bowl.com/raspberry-pi/installing-the-think-bowl-i2c-libraries-for-python/
# or https://github.com/quick2wire/quick2wire-python-api.git

import time
import datetime
import http.client
import random
import urllib

from ISStreamer.Streamer import Streamer
from i2clibraries import i2c_hmc5883l

# Change 1 to different i2c if needed
hmc5883l = i2c_hmc5883l.i2c_hmc5883l(1)
hmc5883l.setContinuousMode()
hmc5883l.setDeclination(9,54)

# API Key for Grovestreams (should have write and auto create permissions)
grovestreams_apikey = 'XXXXXXXXXXXXXX'
# Write API Key for Thingspeak
thingspeak_apikey = 'XXXXXXXXXXXXXX'
# Access Key for Initial State
initialstate_apikey = 'XXXXXXXXXXXXXX'

# Name of component at Grovestreams
component_id = "Water"
# Name of bucket at Initial State
initialstate_bucketname = 'Water Usage'
initialstate_bucketkey  = 'waterusage_home'

grovestreambase_url = '/api/feed?'

# How often to publish
publish_delay = 300
# Amount of water per count
liter_per_count = 0.017

old_val = 0
new_val = 0
crossings = 0

last_publish = time.time()

# Start stream to Initial State
streamer = Streamer(bucket_name=initialstate_bucketname, bucket_key=initialstate_bucketkey, access_key=initialstate_apikey)

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

        # Initial State
        try:
            streamer.log("liters", liters)
        except Exception as e:
            print('Failed to write to Initial State: ' + str(e))

        # Grovestream
        try:
            url = grovestreambase_url + urllib.parse.urlencode({'compId' : component_id,
                               'liters' : liters})
            headers = {"Connection" : "close", "Content-type": "application/json",
                   "Cookie" : "api_key="+grovestreams_apikey}

            print('Uploading grovestream feed to: ' + url)
            conn = http.client.HTTPConnection('www.grovestreams.com')
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

        # Thingspeak
        try:
            params = urllib.parse.urlencode({'field1': liters, 'key': thingspeak_apikey})
            headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}

            print('Uploading to thingspeak: ' + params )
            conn = http.client.HTTPConnection('api.thingspeak.com')
            conn.request("POST", '/update', params, headers)
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

