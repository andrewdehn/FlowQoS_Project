import os
import os.path
#from pox.core import core
from threading import Thread
from threading import Lock
from time import sleep
import json
import re
import findMAC

#log = core.getLogger()

macUpdateFilePath = 'macs_update.json'
macRecordFilePath = 'macs.json'
devicesFilePath = "Webportal/FlowQoS GUI/device.cfg"

defaultServiceType = 'DEFAULT'
videoServiceType = 'VIDEO'
voipServiceType = 'VOIP'
gameServiceType = 'Game'
webServiceType = 'WEB'

macAddressPattern = re.compile("00:00:00:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}")
macDevicePattern = re.compile(" : ")

# videoDeviceTypeIdentifiers = ['tv']
# voipDeviceTypeIdentifiers = ['phone']
# gameDeviceTypeIdentifiers = ['playstation','xbox']
# webDeviceTypeIdentifiers = ['laptop']

deviceTypeIdentifiers = {
                videoServiceType:['tv'],
                voipServiceType:['phone'],
                gameServiceType:['playstation','xbox'],
                webServiceType:['laptop']
                }
                
deviceTypeNumbers = {
                '0':defaultServiceType,
                '1':webServiceType,
                '2':videoServiceType,
                '3':gameServiceType,
                '4':voipServiceType
                }
deviceTypeReverseNumbers = {
                defaultServiceType:'0',
                webServiceType:'1',
                videoServiceType:'2',
                gameServiceType:'3',
                voipServiceType:'4'
                }

class MacClassifier(Thread):

    def _applyMacUpdates(self, mac, type):
        #TODO replace macRecordFilePath contents with contents from macUpdateFilePath
        #TODO reapply macRecordFilePath rules, use some kind of 
        self.flowqos.log.debug("Change for %s to type %s detected" % (mac, type))
        #TODO self.flowqos.service_port_routing(type, self.ports.get(type))
        return
        
    def run(self):
        while True:
            sleep(1)
            deviceList = loadDeviceList(self.flowqos.dir + devicesFilePath)
            if deviceList is not None:
                for device in deviceList:
                    if device.get("user_defined") is True:
                        mac = parseMacAddress(device.get("MAC"))
                        type = device.get("type")
                        self._applyMacUpdates(mac, type)
                        device["user_defined"] = False
                storeDeviceList(self.flowqos.dir + devicesFilePath, deviceList)
                    

    def __init__(self, flowqos):
        super(MacClassifier, self).__init__()
        #TODO Set some other variables to use
        self.flowqos = flowqos
        
    def startMonitorThread(self):
        #Setup and start thread 
        #self.thread = Thread(target = checkForMacUpdates)
        #self.thread.daemon = True
        #self.thread.start()
        self.daemon = True
        self.start()
        
    def _addMac(self, macAddress, deviceList):
        mac = self._findType(macAddress)
        if mac is None:
            return None
        company = mac.get('company')
        type = mac.get('type')
        #type = defaultServiceType
        deviceList.append({"MAC":macAddress + " : " + company, "type":type, "user_defined":False})
        storeDeviceList(self.flowqos.dir + devicesFilePath, deviceList)
        return type
            
    def _findType(self, macAddress):
        # Find details about the device
        macDesc = findMAC.getCompany(macAddress)
        if macDesc is None:
            return None
        company = macDesc['company']
        deviceTypes = macDesc['devices']
        serviceTypes = []
        
        # Find all possible service types for the device
        for serviceType in deviceTypeIdentifiers:
            for dType in deviceTypeIdentifiers[serviceType]:
                if dType in deviceTypes:
                    serviceTypes.append(serviceType)
                    break
                    
        # Determine what service type this is
#        if len(serviceTypes) >= 1:
#            return serviceType[0]
        if videoServiceType in serviceTypes:
            return {'company':company, 'type':videoServiceType}
        elif voipServiceType in serviceTypes:
            return {'company':company, 'type':voipServiceType}
        elif gameServiceType in serviceTypes:
            return {'company':company, 'type':gameServiceType}
        elif webServiceType in serviceTypes:
            return {'company':company, 'type':webServiceType}
        else:
            return None
    
    '''
    Sees if the mac_classifier cares about the event.
    Returns the name of the service type if it cares,
    returns None if it doesn't.
    '''
    def deviceServiceType(self, macAddress):
        #TODO if not already in macs, update macs and macsRecordFile
#        packet = event.parsed
#        macAddress = None
#        if not macAddressPattern.match(str(packet.src)):
#            macAddress = packet.src
#        if not macAddressPattern.match(str(packet.dst)):
#            macAddress = packet.dst
        if macAddress is None:
            return None
        macAddress = str(macAddress)
        
        macDevice = None
        deviceList = loadDeviceList(self.flowqos.dir + devicesFilePath)
        for device in deviceList:
            if (parseMacAddress(device.get("MAC")) == macAddress):
                macDevice = device
        
        if macDevice is None:
            return self._addMac(macAddress, deviceList)
        else:
            return macDevice.get("type")


def parseMacAddress(macDeviceStr):
    return macDevicePattern.split(macDeviceStr)[0]
    
def loadDeviceList(file):
    deviceList = None
    deviceFile = None
    try:
        deviceFile = open(file, 'r')
        while True:
            line = deviceFile.readline()
            if not line:
                break
            full = json.loads(line)
            deviceList = full.get("application_limit")
            for device in deviceList:
                device['type'] = deviceTypeNumbers.get(device.get("type"))
    finally:
        if deviceFile is not None:
            deviceFile.close()
    return deviceList 

def storeDeviceList(file, deviceList):
    for device in deviceList:
        device['type'] = deviceTypeReverseNumbers.get(device.get("type"))
    try:
        deviceFile = open(file, 'w')
        json.dump({"application_limit":deviceList}, deviceFile, separators=(',',':'))
    finally:
        if deviceFile is not None:
            deviceFile.close()
    for device in deviceList:
                device['type'] = deviceTypeNumbers.get(device.get("type"))
    return deviceList
    