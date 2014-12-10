#! /usr/bin/python

import inspect
import os
import atexit
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.topo import SingleSwitchTopo
from mininet.node import RemoteController

from mininet.link import Intf
import sys



def printNow(line):
    print(line)
    sys.stdout.flush()




printNow("Creating Mininet")

#net = Mininet(link = TCLink,
#                  controller=lambda name: RemoteController(name, ip='127.0.0.1'),
#                  listenPort=6633, autoSetMacs=True)
#controllerObj = RemoteController('FlowQoS') #, ip='127.0.0.1')
#printNow("Controller listening %s" % (controllerObj.checkListening()))
net = Mininet(link = TCLink,
                  controller = None,
                  listenPort=6633, autoSetMacs=True)
net.addController( 'c0', controller=RemoteController, ip='127.0.0.1', port=6633 )

hconfig = {'inNamespace':True}

web_link_config = {'bw': 5}
video_link_config = {'bw': 10}
game_link_config = {'bw': 15}
voip_link_config = {'bw': 4}
host_link_config = {}

west_switch_config = {'dpid': "%016x" % (1)}
east_switch_config = {'dpid': "%016x" % (2)}

#web_switch_config = {'dpid': "%016x" % (3)}
#video_switch_config = {'dpid': "%016x" % (4)}
#game_switch_config = {'dpid': "%016x" % (5)}
#voip_switch_config = {'dpid': "%016x" % (6)}

printNow("Creating Switches")
westSwitch = net.addSwitch('ws', **west_switch_config)
eastSwitch = net.addSwitch('es', **east_switch_config)
printNow("Linking Switches")
net.addLink(westSwitch, eastSwitch, port1=1, port2=1, **web_link_config)
net.addLink(westSwitch, eastSwitch, port1=2, port2=2, **video_link_config)
net.addLink(westSwitch, eastSwitch, port1=3, port2=3, **game_link_config)
net.addLink(westSwitch, eastSwitch, port1=4, port2=4, **voip_link_config)

printNow("Creating Internet Host")
internet = net.addHost('www', **hconfig)
net.addLink(internet, westSwitch, port2=10, **host_link_config)

laptop_config = {'mac':'F0-DE-F1-09-95-5F'}
printNow("Creating Laptop Host")
laptop = net.addHost('h1', **laptop_config)
printNow("Setting laptop MAC address")
#laptop.addIntf(Intf('h1-eth0', node=laptop))
#laptop.setMAC('F0-DE-F1-09-95-5F')#, intf=laptop.intf(intf='eth0'))
printNow("Linking laptop to eastSwitch")
net.addLink(laptop, eastSwitch, port2=10, **host_link_config)

printNow("Starting Network")
net.start()

CLI(net)

net.stop()


