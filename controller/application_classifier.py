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

from mac_classifier import MacClassifier

log = core.getLogger()
list_udp=[]
list_tcp=[]
clean_list_udp=[]
clean_list_tcp=[]
flows=[]
TCP=[]
UDP=[]
flows_dict={}


class ApplicationClassifier:
  def __init__ (self, flowqos):
    self.flowqos = flowqos

  '''
  Returns the name of the service type for this packet, or None if there is no type.
  '''
  def applicationServiceType(self, event):
    packet = event.parsed
    
    if packet.type != ethernet.ARP_TYPE and packet.type != ethernet.IPV6_TYPE:
      if packet.next.protocol != ipv4.ICMP_PROTOCOL:
        if packet.next.next.dstport == 80 or packet.next.next.dstport == 443:
            #DNS flow Classification
          if packet.next.next.dstport != 53 or packet.next.next.srcport != 53:
            #print packet.next.dstip
            dnsname = core.DNSSpy.lookup(packet.next.dstip)
            if (dnsname is not None):
              service = core.DNSSpy.getType(dnsname)
              print 'dnsname: %s' % dnsname +'Type : %s' %service
              #print 'servicetype:'
              #print service
#              east_port = self.east_service_to_port[service]
#              west_port = self.west_service_to_port[service]
              #print east_port, west_port
#              self.send_flow_mod(packet, east_port, west_port, event)
              return service
        else:
          #flowQos classification
          #Check is the ip source  and destination exist in the dictionary
          
          f=open (self.flowqos.dir + 'flow_dict2.json','r') 
          for obj in json_decoder(f): 
            flows_dict.update(obj)
            #flows_dict = json.load(f)
            key = str(packet.find("ipv4").srcip)+','+str(packet.find("ipv4").dstip)
            #print key
            if key in flows_dict:
              service = flows_dict[key]
              print key +' ->  ' +service
              if service == 'P2P':
                service2 = 'VIDEO'
#                east_port = self.east_service_to_port[service2]
#                west_port = self.west_service_to_port[service2]
                #print east_port, west_port
#                self.send_flow_mod(packet, east_port, west_port, event)
                return service2
                #check application type and send the packet to the outplut port
              return service
            else:
              if packet.find("udp"):
                list_udp.append([DottedIPToInt(str(packet.find("ipv4").srcip)), 
                                 DottedIPToInt(str(packet.find("ipv4").dstip)), 
                                 packet.find("udp").srcport, 
                                 packet.find("udp").dstport, 
                                 shiftpyaload(str(packet.find("udp").payload)[0:4]), 
                                 len(packet.find("udp").payload) ,
                                 chr(17 & 0xFF)])
                                
              if packet.find("tcp"):
                list_tcp.append([DottedIPToInt(str(packet.find("ipv4").srcip)), 
                                 DottedIPToInt(str(packet.find("ipv4").dstip)), 
                                 packet.find("tcp").srcport, 
                                 packet.find("tcp").dstport, 
                                 shiftpyaload(str(packet.find("tcp").payload)[0:4]), 
                                 len(packet.find("tcp").payload) ,
                                 chr(6 & 0xFF)])
                              
                #remove all the flow entries that have payload length that is equal to zero such ACK
            clean_list_udp=clean(list_udp)
            clean_list_tcp=clean(list_tcp)
                
                #Extractinf TCP flows in a new list
            for i in range(len(clean_list_tcp)):
              for j in range(i+1, len(clean_list_tcp)):
                if isSame(clean_list_tcp[i],clean_list_tcp[j]):
                  clean_list_tcp[i].append(clean_list_tcp[j][4]) #payload sever
                  clean_list_tcp[i].append(clean_list_tcp[j][5]) #length payload server
                  TCP.append(clean_list_tcp[i])
                  break
                  #Extracting the UDP flows in a new list
            for k in range(len(list_udp)):
              for l in range(k+1, len(list_udp)):
                if isSame(list_udp[k],list_udp[l]):
                  list_udp[k].append(list_udp[l][4]) #payload sever
                  list_udp[k].append(list_udp[l] [5]) #length payload server
                  TCP.append(list_udp[k])
                  break

            flows=TCP+UDP
            # Save all the flows in one single file
            thefile = open(self.flowqos.dir + "log_flows.txt", "w")
            for item in flows:
              thefile.write("%s\n" % item)
            thefile.close()
            # classification and writing output in a file
            classified_flows=[]
            for item in flows:
              libprotoident.lpi_init_library()
              classified_flows.append([IntToDottedIP(item[0]),
                                       IntToDottedIP(item[1]),
                                       libprotoident.lpi_shim_guess_protocol(item[4],
                                                                             item[7],
                                                                             item[0],
                                                                             item[1],
                                                                             item[2],
                                                                             item[3],
                                                                             item[5],
                                                                             item[8],
                                                                             item[6])])
              libprotoident.lpi_free_library()
              if item in classified_flows:
                if item[2]!='Unknown':
                	print item
                
            thefile2 = open(self.flowqos.dir + "log_classification.txt", "w")
            for item2 in classified_flows:
            	thefile2.write("%s\n" % item2)
            thefile2.close()
                  
                  
                  
            for element in classified_flows:
                if element[2]=='Unknown' and element[1]+','+element[1] in flows_dict:
                    continue
                elif element[2]!='Unknown' and element[1]+','+element[1] in flows_dict:
                    del flows_dict[element[1]+','+element[1]]
                    flows_dict[element[0]+','+element[1]]=element[2]
                else:
                    flows_dict[element[0]+','+element[1]]=element[2]
            

            for key in flows_dict.keys():
                if type(key) is not str:
                    try:
                        flows_dict[str(key)]=flows_dict[key]
                    except:
                        try:
                          flows_dict[repr(key)]=flows_dict[key]
                        except:
                          pass
            f2=open (self.flowqos.dir + 'flow_dict2.json','w+')
            json.dump(flows_dict,f2)
                        
            #print flows_dict
            # print flows_dict.keys()	
            f2.close()
          f.close()
          
          f=open (self.flowqos.dir + 'flow_dict2.json','r') 
          for obj in json_decoder(f): 
            flows_dict.update(obj)
            key = str(packet.find("ipv4").srcip)+','+str(packet.find("ipv4").dstip)
            if key in flows_dict:
              service = flows_dict[key]
              print key +' ->  ' +service
              if service == 'P2P':
                service2 = 'VIDEO'
                return service2
              return service
          f.close()
  
    return None

def json_decoder(fo): 
    buff = '' 
    decode = json.JSONDecoder().raw_decode 
    while True: 
        line = fo.readline() 
        if not line: 
            break 
        buff += line 
       # print('BUFF: {}'.format(buff)) 
        try: 
            obj, i = decode(buff) 
            buff = buff[i:].lstrip() 
            yield obj 
        except ValueError as e: 
            print('ERR: {}'.format(e)) 
            sleep(0.01) # select will probably be a better option :)         

def AsciitoHex(b):
    a=""
    for x in b:
        a = a + (hex(ord(x)))[2:4]
        return a

def isSame(a, b):
    #print "checking ", a , b
    value=''
    if a[0] == b[1] and a[1] == b[0] and a[2] == b[3] and a[3] == b[2] and value not in b and value not in a:
        #print "same"
        return True
    else:
        #print "different"
        return False

        shifting

def shifting(b):
    #a =b[::-1]
    if a == "" or len(a) != 4:
       return 0
    else:
       #payload=struct.unpack('!I',a)
       payload=struct.unpack('!I',b[0:4])
       return payload[0]


def clean(a):
    value=0
    b=[]
    for element in a:
        if value not in element:
            b.append(element)
    return b


def shiftpyaload(b):
    a=b[::-1]
    if a == "" or len(a) != 4:
        return 0
    else:
        payload=struct.unpack('!I',a[0:4])
        return payload[0]


def DottedIPToInt( dotted_ip ):
        exp = 3
        intip = 0
        for quad in dotted_ip.split('.'):
                intip = intip + (int(quad) * (256 ** exp))
                exp = exp - 1
        return(intip)


def IntToDottedIP( intip ):
        octet = ''
        for exp in [3,2,1,0]:
                octet = octet + str(intip / ( 256 ** exp )) + "."
                intip = intip % ( 256 ** exp )
        return(octet.rstrip('.'))


def asciirepl(match):
  # replace the hexadecimal characters with ascii characters
  s = match.group()
  return binascii.unhexlify(s)


def reformat_content(data):
  p = re.compile(r'\\x(\w{2})')
  return p.sub(asciirepl, data)


def jdefault(o):
    return o.__dict__

  
