from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.packet.ethernet import ethernet, ETHER_BROADCAST
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.arp import arp
from pox.lib.addresses import IPAddr, EthAddr
from pox.lib.util import str_to_bool, dpidToStr
from pox.lib.revent import *
#import dpkt
import socket
#import libprotoident
import struct
import binascii, re
import json
import StringIO
from time import sleep
import sys

from mac_learner import MacLearner
from mac_classifier import MacClassifier
from application_classifier import ApplicationClassifier

log = core.getLogger()

baseDir = '/home/mininet/pox/pox/flowqos/'

class FlowQoS (EventMixin):
  
  def __init__ (self):

    core.openflow.addListeners(self)
    # Creating service-type to port mapping
    self.east_service_to_port = { 'DEFAULT': 1,
                        'VIDEO': 2,
                        'VOIP': 4,
                        'Game': 3,
                        'WEB': 1
                      }
    
    self.west_service_to_port = { 'DEFAULT': 1,
                        'VIDEO': 2,
                        'VOIP': 4,
                        'Game': 3,
                        'WEB': 1
                      }
    
    #self.east_dpid = int("0x0000baf8d9adad9f",16)
    #self.east_home_port = 1
    #self.west_dpid = int("0x000004a151a30fcc",16)
    #self.west_internet_port = 1
    self.east_dpid = int("0x0000000000000002",16)
    self.east_home_port = 1
    self.west_dpid = int("0x0000000000000001",16)
    self.west_internet_port = 10

    # Add handy function to console
    #core.Interactive.variables['lookup'] = self.lookup
    
    self.dir = baseDir
    self.log = log
    
    # Setup the MacLearner
    self.macLearner = MacLearner(self)

    # Setup the MacClassifier
    self.macClassifier = MacClassifier(self)
    self.macClassifier.startMonitorThread()
    self.macFlows = {}
    
    # Setup the ApplicationClassifier
    self.appClassifier = ApplicationClassifier(self)
    
    log.debug("FlowQoS startup complete")
    

  def _handle_ConnectionUp (self, event):
    log.debug("Connection %s" % (event.connection,))  
      
#     ## Packet going out from home to internet
#     msg = of.ofp_flow_mod()
#     msg.match.in_port = 1
#     msg.actions.append(of.ofp_action_output(port = 2))
#     event.connection.send(msg)
#   
#     ## Packet coming from internet to home
#     msg = of.ofp_flow_mod()
#     msg.match.in_port = 2
#     msg.actions.append(of.ofp_action_output(port = 1))
#     event.connection.send(msg)


  '''
    Configures the intermediate switches for the Mininet topology.
  '''
  def set_intermediates(self):
      msg1 = of.ofp_flow_mod()
      msg1.priority = 10
      msg1.match.in_port = 1
      msg1.actions.append(of.ofp_action_output(port = 2))
      msg2 = of.ofp_flow_mod()
      msg2.priority = 10
      msg2.match.in_port = 2
      msg2.actions.append(of.ofp_action_output(port = 1))
      
      core.openflow.getConnection(int("0x0000000000000003",16)).send(msg1)
      core.openflow.getConnection(int("0x0000000000000003",16)).send(msg2)
      core.openflow.getConnection(int("0x0000000000000004",16)).send(msg1)
      core.openflow.getConnection(int("0x0000000000000004",16)).send(msg2)
      core.openflow.getConnection(int("0x0000000000000005",16)).send(msg1)
      core.openflow.getConnection(int("0x0000000000000005",16)).send(msg2)
      core.openflow.getConnection(int("0x0000000000000006",16)).send(msg1)
      core.openflow.getConnection(int("0x0000000000000006",16)).send(msg2)


  def set_default_routing_west(self, event, devicePort):
    packet = event.parsed
    log.debug("Setting default routing from west event, dst=%s, devicePort=%i" % (str(packet.dst), devicePort))
    
    # East default configuration
    
    ## Packet going out from home to internet
    msg = of.ofp_flow_mod()
    msg.priority = 10
    msg.match.dl_type = packet.type
    msg.match.dl_src = packet.dst
#    if(packet.type == ethernet.IP_TYPE):
#        msg.match.nw_dst = packet.next.dstip
    msg.actions.append(of.ofp_action_output(port = self.east_service_to_port['DEFAULT']))
    #msg.actions.append(of.ofp_action_output(port = 1)) #this seems to be an artifact of OVS, commented out for mininet
    msg.actions.append(of.ofp_action_output(port = of.OFPP_CONTROLLER))
    core.openflow.getConnection(self.east_dpid).send(msg)

    ## Packet coming from internet to home
    msg = of.ofp_flow_mod()
    msg.priority = 10
    msg.match.dl_type = packet.type
#    msg.match.nw_src = packet.next.dstip
    msg.match.dl_dst = packet.dst
    msg.actions.append(of.ofp_action_output(port = event.port))
    #msg.actions.append(of.ofp_action_output(port = 1)) #this seems to be an artifact of OVS, commented out for mininet
    msg.actions.append(of.ofp_action_output(port = of.OFPP_CONTROLLER))
    core.openflow.getConnection(self.east_dpid).send(msg)

    # West default configuration

    ## Packet going out from home to internet
    msg = of.ofp_flow_mod()
    msg.priority = 10
    msg.match.dl_type = packet.type
#    msg.match.nw_dst = packet.next.dstip
    msg.match.dl_src = packet.dst
    msg.actions.append(of.ofp_action_output(port = self.west_internet_port))
    #msg.actions.append(of.ofp_action_output(port = 1)) #this seems to be an artifact of OVS, commented out for mininet
    msg.actions.append(of.ofp_action_output(port = of.OFPP_CONTROLLER))
    core.openflow.getConnection(self.west_dpid).send(msg)

    ## Packet going out from internet to home
    msg = of.ofp_flow_mod()
    msg.priority = 10
    msg.match.dl_type = packet.type
#    msg.match.nw_src = packet.next.dstip
    msg.match.dl_dst = packet.dst
    msg.actions.append(of.ofp_action_output(port = self.west_service_to_port['DEFAULT']))
    #msg.actions.append(of.ofp_action_output(port = 1)) #this seems to be an artifact of OVS, commented out for mininet
    msg.actions.append(of.ofp_action_output(port = of.OFPP_CONTROLLER))
    core.openflow.getConnection(self.west_dpid).send(msg)
  
  def set_default_routing_east(self, event):
    packet = event.parsed
    devicePort = event.port
    log.debug("Setting default routing from east event, src=%s, devicePort=%i" % (str(packet.src), devicePort))
    
    # East default configuration
    
    ## Packet going out from home to internet
    msg = of.ofp_flow_mod()
    msg.priority = 10
    msg.match.dl_type = packet.type
    msg.match.dl_src = packet.src
#    if(packet.type == ethernet.IP_TYPE):
#        msg.match.nw_dst = packet.next.dstip
    msg.actions.append(of.ofp_action_output(port = self.east_service_to_port['DEFAULT']))
    #msg.actions.append(of.ofp_action_output(port = 1)) #this seems to be an artifact of OVS, commented out for mininet
    msg.actions.append(of.ofp_action_output(port = of.OFPP_CONTROLLER))
    core.openflow.getConnection(self.east_dpid).send(msg)

    ## Packet coming from internet to home
    msg = of.ofp_flow_mod()
    msg.priority = 10
    msg.match.dl_type = packet.type
#    msg.match.nw_src = packet.next.dstip
    msg.match.dl_dst = packet.src
    msg.actions.append(of.ofp_action_output(port = event.port))
    #msg.actions.append(of.ofp_action_output(port = 1)) #this seems to be an artifact of OVS, commented out for mininet
    msg.actions.append(of.ofp_action_output(port = of.OFPP_CONTROLLER))
    core.openflow.getConnection(self.east_dpid).send(msg)

    # West default configuration

    ## Packet going out from home to internet
    msg = of.ofp_flow_mod()
    msg.priority = 10
    msg.match.dl_type = packet.type
#    msg.match.nw_dst = packet.next.dstip
    msg.match.dl_src = packet.src
    msg.actions.append(of.ofp_action_output(port = self.west_internet_port))
    #msg.actions.append(of.ofp_action_output(port = 1)) #this seems to be an artifact of OVS, commented out for mininet
    msg.actions.append(of.ofp_action_output(port = of.OFPP_CONTROLLER))
    core.openflow.getConnection(self.west_dpid).send(msg)

    ## Packet going out from internet to home
    msg = of.ofp_flow_mod()
    msg.priority = 10
    msg.match.dl_type = packet.type
#    msg.match.nw_src = packet.next.dstip
    msg.match.dl_dst = packet.src
    msg.actions.append(of.ofp_action_output(port = self.west_service_to_port['DEFAULT']))
    #msg.actions.append(of.ofp_action_output(port = 1)) #this seems to be an artifact of OVS, commented out for mininet
    msg.actions.append(of.ofp_action_output(port = of.OFPP_CONTROLLER))
    core.openflow.getConnection(self.west_dpid).send(msg)
  
  def set_service_routing (self, packetType, internetIp, localMac, serviceType, devicePort, priority):
    log.debug("Setting %s service routing between %s and %s, over device port %i" % (serviceType, str(internetIp), str(localMac), devicePort))
    
    # East configuration
    
    ## Packet going out from home to internet
    msg = of.ofp_flow_mod()
    msg.priority = priority
    msg.match.dl_type = packetType
    msg.match.nw_dst = internetIp
    msg.match.dl_src = localMac
    msg.actions.append(of.ofp_action_output(port = self.east_service_to_port[serviceType]))
    msg.actions.append(of.ofp_action_output(port = of.OFPP_CONTROLLER))
    core.openflow.getConnection(self.east_dpid).send(msg)

    ## Packet coming from internet to home
    msg = of.ofp_flow_mod()
    msg.priority = priority
    msg.match.dl_type = packetType
    msg.match.nw_src = internetIp
    msg.match.dl_dst = localMac
    msg.actions.append(of.ofp_action_output(port = devicePort))
    msg.actions.append(of.ofp_action_output(port = of.OFPP_CONTROLLER))
    core.openflow.getConnection(self.east_dpid).send(msg)

    # West configuration

    ## Packet going out from home to internet
    msg = of.ofp_flow_mod()
    msg.priority = priority
    msg.match.dl_type = packetType
    msg.match.nw_dst = internetIp
    msg.match.dl_src = localMac
    msg.actions.append(of.ofp_action_output(port = self.west_internet_port))
    msg.actions.append(of.ofp_action_output(port = of.OFPP_CONTROLLER))
    core.openflow.getConnection(self.west_dpid).send(msg)

    ## Packet going out from internet to home
    msg = of.ofp_flow_mod()
    msg.priority = priority
    msg.match.dl_type = packetType
    msg.match.nw_src =internetIp
    msg.match.dl_dst = localMac
    msg.actions.append(of.ofp_action_output(port = self.west_service_to_port[serviceType]))
    msg.actions.append(of.ofp_action_output(port = of.OFPP_CONTROLLER))
    core.openflow.getConnection(self.west_dpid).send(msg)

  def securityCheck(self, event):
    return False
    
  '''
  Returns dictionary containing 'serviceType' and 'priority'. Returns None if there is no service type available.
  '''
  def serviceType(self, event):
    packet = event.parsed
    type = None
    # Get application type
    type = self.appClassifier.applicationServiceType(event)
    if type is not None:
        return {'serviceType':type, 'priority':60, 'from': 'appClassifier'}
    
    # Get mac application type
    if(event.dpid == self.east_dpid):
        type = self.macClassifier.deviceServiceType(packet.src)
    if(event.dpid == self.west_dpid):
        type = self.macClassifier.deviceServiceType(packet.dst)
    if type is not None:
        return {'serviceType':type, 'priority':50, 'from':'macClassifier'}
    
    return None
  
  def _handle_PacketIn (self, event):
    #self.set_intermediates()
    packet = event.parsed
    
    #log.debug("PacketIn from %s on port %s" % (packet.src, event.port))
    
    ## Check packet for security purposes
    #TODO
    
    devicePort = None
    internetIp = None
    localMac = None
    if(event.dpid == self.east_dpid and event.port not in self.east_service_to_port.values()):
        log.debug("PacketIn east from %s on port %s" % (packet.src, event.port))
        devicePort = event.port
        localMac = packet.src
        if packet.type == ethernet.IP_TYPE:
            internetIp = packet.next.dstip
        self.macLearner.detectedDevice(packet.src, devicePort)
        # Setup the default routing
        self.set_default_routing_east(event)
    elif(event.dpid == self.west_dpid and event.port not in self.west_service_to_port.values()):
        log.debug("PacketIn west from %s on port %s" % (packet.src, event.port))
        devicePort = self.macLearner.whereDevice(packet.dst)
        localMac = packet.dst
        if packet.type == ethernet.IP_TYPE:
            internetIp = packet.next.srcip
        # If device is known to the controller
        if devicePort is not None:
            # Setup default routing
            self.set_default_routing_west(event, devicePort)
    
    serviceDict = None
    ## Determine the service type and priority if 
    if devicePort is not None:
        serviceDict = self.serviceType(event)
        log.debug("Flow service detected: %s" % (serviceDict))
        if serviceDict is not None:
            serviceType = serviceDict.get('serviceType')
            priority = serviceDict.get('priority')
            ## Apply the service type appropriately
            if internetIp is not None:
                self.set_service_routing(packet.type, internetIp, localMac, serviceType, devicePort, priority)
                #if(service.get('from') == 'macClassifier'):
                #    if self.macFlows.get(localMac) is None:
                #        self.macFlows[localMac] = 
        
    
    '''
    if(event.dpid == self.east_dpid):
        if(event.port in self.east_service_to_port.values()):
            out_port = self.macLearner.whereDevice(packet.dst)
            if out_port is not None:
                #send out appropriate port
            else:
                #send out all device ports
        else:
            self.macLearner.detectedDevice(packet.dst, event.port)
            #send out via service type
    elif(event.dpid == self.west_dpid):
        
    
    if(event.dpid == self.east_dpid and event.parsed.src == EthAddr("00:00:00:00:00:01")):
        log.debug("East 01 on port %i" % (event.port))
        rule = self.macClassifier.detectedDeviceRule(event)
        if rule is not None:
            self.service_port_routing(rule, event.port)
    '''
    

def launch ():
  
  log.debug("Starting FlowQoS")
  core.registerNew(FlowQoS)
  
