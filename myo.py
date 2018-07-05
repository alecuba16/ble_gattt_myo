#!/usr/bin/python
from bledevice import *
import time
import sys
import struct

target_mac = 'D3:CF:59:A4:36:BB'
uuid_command = "0401"
uuid_classifier = "0103"
uuid_imu = "0402"
uuid_emg = "0104"

imu_reply_handler = None
emg_reply_handler = None
classifier_reply_handler = None

def toggle_notifications(uuid,status=False,sleep=0.5,verbose=False):
    reply_handler=dev.getvaluehandle(uuid)
    if status==True:
        dev.writereq(reply_handler+1, "0100",verbose=verbose) 
    else:
        dev.writereq(reply_handler+1, "0000",verbose=verbose) 
    time.sleep(sleep)
    return reply_handler

def configure(dev,sleep=0.5,enable_imu=False,enable_emg_raw=False,enable_emg=False,enable_classifier=False,verbose=False):
    global imu_reply_handler,emg_reply_handler,classifier_reply_handler,uuid_command,uuid_classifier,uuid_imu,uuid_emg
    controlServiceHandler=dev.getvaluehandle(uuid_command)
    dev.writecmd(controlServiceHandler, "0101010301") # Enable all
    classifier_reply_handler=toggle_notifications(uuid_classifier,enable_classifier,sleep)
    imu_reply_handler=toggle_notifications(uuid_imu,enable_imu,sleep)
    emg_reply_handler=toggle_notifications(uuid_emg,enable_emg|enable_emg_raw,sleep,verbose=verbose)
    
    
def flatten(l):
    if isinstance(l,list):
        return sum(map(flatten,l))
    else:
        return l

def handle_data(handle, value):
    if handle == imu_reply_handler: #IMU
        value=struct.unpack('<10h',value)
        quat=value[:4]
        accel=value[4:7]
        gyro=value[7:]
        print("got imu notification quat:"+str(quat)+" accel:"+str(accel)+" gyro:"+str(gyro))
    elif handle == emg_reply_handler: #EMG
        #data = struct.unpack('<8HB', value)  # an extra byte for some reason TODO
        print("got emg notification data:"+str(value))
    else:
        print("Received from handler:"+str(handle)+" but not processed")
        

be_connected=True
initialized=False
while be_connected:
    try:
        if not initialized:
            #print("Connecting...")
            dev=BLEDevice(target_mac,printCharacteristics=False)
            #print("Connected")
            print("Configuring...")
            configure(dev=dev,enable_emg=True)
            print("Configured")
            initialized=True
            
        data = dev.notify()
        if data is not None:
            handle_data(data["handle"],data["value"])
        else:
            print("No data")
        time.sleep(1)
    
    except KeyboardInterrupt:
        print("Stopped by keyboard")
        sys.exit()
        
    except pexpect.TIMEOUT:
        time.sleep(0.5)
        print("timeout .")
    except:
        time.sleep(0.5)
        print(".")
