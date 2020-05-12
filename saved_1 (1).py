import time
import json
import struct
from bluepy import sensortag
import paho.mqtt.publish as mqtt
import math
import collections 
import matplotlib.pyplot as plt
import statistics 
import threading

base_topic_detection = '/pervasive/collision/road_telemetry'
host = "test.mosquitto.org"
mysensors = {'1A':
             {
                 'tag_address':'54:6C:0E:B5:76:04',
                 #'tag_address':'F0:F8:F2:86:39:87',
                 'road':'A',
                 'pos':40,
                 'isAlive':False
              },
             '2A':
             {
                 'tag_address':'F0:F8:F2:86:39:87',
                 #'tag_address':'54:6C:0E:52:F3:CC',
                 'road':'A',
                 'pos':70,
                 'isAlive':False
                 },
             '1B':
             {
                 'tag_address':'54:6C:0E:53:38:58',
                 'road':'A',
                 'pos':40,
                 'isAlive':False
                 
                 },
             '2B':
             {
                 'tag_address':'54:6C:0E:52:F3:CC',
                 'road':'A',
                 'pos':70,
                 'isAlive':False
                 
                 }
             }

def test_queue(d,r):
    d.append(r)
    if len(d) >= 4:
        d.popleft()

def send_info():
    while True:
        mqtt.multiple(msg_info, hostname = host, port=1883) 
        time.sleep(4)






# for live ploting 
plt.rcParams['animation.html'] = 'jshtml'
plt.title("std dev readings")
plt.xlabel("time in ms")
plt.ylabel("std dev")
fig_tags = {} # holds the plots of repective tags
fig = plt.figure()
ax = fig.add_subplot(111)
fig.show()

j = 0
x, y = [], []

tags = {} # tags will have the sensortags objects
queue = {} # queue is a dictionary which holds deque of the tags(will have the same keys)
#for loop to enable the sensor tags and create respective deque and store the addresses in tags and queue dictionary var for future use 
for key in mysensors.keys():
    try:
        tag = sensortag.SensorTag(mysensors[key]['tag_address'])
        print("Connected to sensortag",mysensors[key])
        tag.lightmeter.enable()
        mysensors[key]['isAlive'] = True
        print("hello")
        tags[key] = tag
        # creating queue for the tag
        len_q_test = 4
        d1 = collections.deque([],len_q_test)
        queue[key] =  d1
        
    except:
        print("not connected to ", mysensors[key])
        continue
   
    
   
#publishing initial info to the broker
info = {
       'timestamp': int(time.time()),
       'sensors' : mysensors
    
       }
    
payload_info = json.dumps(info)
print(payload_info)
msg_info = []
msg_info.append((base_topic_detection, payload_info, 0, False))

t = threading.Thread(target = send_info)

t.start()


while True:
    msgs = []
    
    data = {} #data as a variable which has readings that we are recording(light and time)
    for i in tags: # i is an incrementer
        if(mysensors[i]['isAlive'] ==  True):
            ambient_Light = tags[i].lightmeter.read()
            # if condition for known error correction 
            if(ambient_Light == 0.08):
                continue
            # insert readings in their respective deque
            test_queue(queue[i], ambient_Light)
            st_dev = 0
            if (len(queue[i]) >2) :
                st_dev = statistics.stdev(queue[i])
                print("std dev is %s " % (st_dev))
                j = int(time.time())
                x.append(j)
                y.append(st_dev)
                
                ax.plot(x, y, color='b')
        
                fig.canvas.draw()
        
                ax.set_xlim(left=max(0, j-50), right=j+50)
        
            if (st_dev >= 5):
                print("car detected by %s" % (i))
                #create json object and send it over
           # plt.plot(ambient_Light)
           # plt.show()
          
                data = {
                "road_telemetry":
                    {
                    'timestamp': int(time.time()),
                    'car_detected': True,
                    'detected_by': i,
                    'road':mysensors[i]['road'],
                    'pos':mysensors[i]['pos']
                    }         
                        
                
                }
            
                payload = json.dumps(data)
                print (payload)
       
                msgs.append((base_topic_detection, payload, 0, False))
                 
                mqtt.multiple(msgs, hostname= host, port=1883) #publishing to the local host
    time.sleep(0.01)

#tag.disconnect()




















