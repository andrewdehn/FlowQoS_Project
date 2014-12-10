FlowQoS
===============
FlowQoS is an SDN-based approach for application-based bandwidth allocation where users can allocate upstream and downstream bandwidths for different applications at a high level, offloading application identification to an SDN controller that dynamically installs traffic shaping rules for application flows. If it is unable to perform application-base allocation, the controller will install default flow rules based on the type of device, as determined by the device's MAC address. FlowQoS makes it easier for a typical user to configure priorities and facilitates more sophisticated per-flow application-based QoS, but doing so imposes its own set of challenges.

In this Github you can download the FlowQoS source code and the Openwrt with OpenVswitch kernel module for Netgear WNDR3800, as well as the mininet version to test with.


Follow the installation instructions appropriate to how you wish to run FlowQoS.

To run the controller code, cd to local pox directory and run: ./pox.py log.level --DEBUG flowqos.FlowQos flowqos.dns_spy

Installation Instructions:
=============================
* Ensure you have a version of Python 2.7 installed.
* Decide whether to use use the router topology or the mininet topology, follow the instructions in the appropriate section to set that up.
* Install POX and add it to your PYTHONPATH
    *https://github.com/noxrepo/pox.git
* Install libtrace-3.0.21 from the following address, pay attention to installation instructions.
    * http://research.wand.net.nz/software/libtrace/libtrace-3.0.21.tar.bz2
* Install libflowmanager-2.0.4 from the following address, pay attention to installation instructions.
    * http://research.wand.net.nz/software/libflowmanager/libflowmanager-2.0.4.tar.gz
* Install the modified libprotoident.
    * git clone https://github.com/sdonovan1985/libprotoident.git
    * cd into libprotoident/lib/
    * Modify the Makefile to alter the following variables
        * Change PYTHONLOCATION to point at your python libs. If you manually compiled and installed Python, it is most likely /usr/local/include/python2.7
        * Change LOCALHEADERLOCATION to the absolute path of libprotoident/lib/
    * Compile libprotoident
        * Run make to install
        * If compiling failes and reports a problem regarding libprotoident.o, try running make again without cleaning. You may have to try this several times before it works.
        * If you continue to have problems compiling libprotoident, try installing Python 2.7.3.
    * Add libprotoident/lib/ to your PYTHONPATH
    * Ensure that you can import libprotoident
* Create a flowqos directory in your pox/pox, then copy the contents of the controller directory to your pox/pox/flowqos
* Open FlowQos.py and modify baseDir to reflect the directory where the FlowQoS package was copied to.

  
Configuring Mininet:
=======================
* Install mininet.
* Add mininet to your PYTHONPATH, ensure that it is added for root as well.
* Run the mininetFlowqos.py from the mininet directory with root privileges to create the topology.

Configuring Router:
======================
This section needs to be completed by someone who can configure the router.

Things to be completed:
==========================
* The IP blocking security feature has not yet been fully installed, since there is not use using it on the mininet topology. If you wish to experiment with the IP blocking security feature, see the securityCheck() function in FlowQos.py

Known Bugs:
==============
* It seems that the first set of packets of a flow are not routed properly according to the rules installed on the OVS switchs. The second set of packets always seems to go through, however.
