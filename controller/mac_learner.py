

'''
MAC learner for FlowQoS
'''
class MacLearner:
    
    def __init__(self, flowqos):
        self.flowqos = flowqos
        self.devices = {}
        self.ports = {}

    '''
    Records the port of a specific MAC address. Returns True if the MAC address was already recorded, False otherwise.
    '''
    def detectedDevice(self, mac, port):
        result = None
        dPorts = self.devices.values()
        if dPorts is not None:
            result = port in dPorts
        if port not in self.flowqos.east_service_to_port.values():
            self.devices[mac] = port
            self.ports[port] = mac
        return result
    
    '''
    Returns the port of the given MAC address, or None if not recorded.
    '''
    def whereDevice(self, mac):
        return self.devices.get(mac)
        
    '''
    Returns a list of ports that devices are / can be on.
    '''
    def devicePorts(self):
        return self.devices.values()