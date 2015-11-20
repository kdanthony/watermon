#!/usr/bin/python3
import time
import datetime
import http.client
import random
import urllib

from i2clibraries import i2c_hmc5883l

def arduino_map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

hmc5883l = i2c_hmc5883l.i2c_hmc5883l(1)
hmc5883l.setContinuousMode()
hmc5883l.setDeclination(9,54)

grovestreams_apikey = 'XXXXXXXXXXXXXX'

component_id = "Water"
base_url = '/api/feed?'

conn = http.client.HTTPConnection('www.grovestreams.com')

old_val = 0;
new_val = 0;
crossings = 0;
liter_per_count = 0.017

publish_delay = 60

last_publish = time.time()

while 1:
    now = time.time()

    (x, y, z) = hmc5883l.getAxes()
    old_val = new_val
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
