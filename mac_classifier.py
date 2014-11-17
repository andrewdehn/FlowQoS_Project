import os
import os.path
from threading import Thread
from threading import Lock
from time import sleep
import json

import findMAC

cwd = os.getcwd()
absPath = cwd + '/pox/flowqos/servicedef/'

macUpdateFilePath = absPath + 'macs_update.ini'
macRecordFilePath = absPath + 'macs.ini'

videoServiceType = 'VIDEO'
voipServiceType = 'VOIP'
gameServiceType = 'Game'
webServiceType = 'WEB'

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

class MacClassifier:
	def __init__(self, flowqos):
		#TODO Set some other variables to use
		
		
		# self.macs is a {MacAddress: ContentType}
		self.macs = {}
		self.macs_lock = Lock()
		self.macs.update(self.loadMacs())
		
		#Setup and start thread 
		self.thread = Thread(target = checkForMacUpdates)
		self.thread.daemon = True
		self.thread.start()
		
	def _loadMacs():
		buff = ''
		macRecordFile = open(macRecordFilePath)
		for line in macRecordFile.readlines():
			buff += line
		macRecordFile.close()
		#TODO decode JSON
		
	
	def _checkForMacUpdates():
		while True:
			if os.path.isFile(macUpdateFilePath) and not os.path.isFile(macUpdateFilePath + '.lock'):
				_applyMacUpdates()
	
	def _applyMacUpdates():
		#TODO replace macRecordFilePath contents with contents from macUpdateFilePath
		#TODO reapply macRecordFilePath rules, use some kind of 
		return
	
	def _addMac(macAddress):
		type = _findType(macAddress)
		self.macs_lock.acquire()
		self.macs.add({macAddress:type})
		self.macs_lock.release()
		return type
		
	def detectedMacAddress(macAddress):
		#TODO convert mac address to string or something if not already
		#TODO if not already in macs, update macs and macsRecordFile
		if macAddress not in self.macs:
			_addMac(macAddress)
			
	def _findType(macAddress):
		# Find details about the device
		macDesc = findMAC.getCompany(macAddress)
		deviceTypes = macDesc['devices']
		serviceTypes = []
		
		# Find all possible service types for the device
		for serviceType in deviceTypeIdentifiers:
			for dType in deviceTypeIdentifiers[serviceType]:
				if dType in deviceTypes:
					serviceTypes.append(serviceType)
					break
					
		# Determine what service type this is
		if len(serviceTypes) >= 1:
			return serviceType[0]
		elif videoServiceType in serviceTypes:
			return videoServiceType
		elif voipServiceType in serviceTypes:
			return voipServiceType
		elif gameServiceType in serviceTypes:
			return gameServiceType
		elif webServiceType in serviceTypes:
			return webServiceType
		else:
			return None
		


