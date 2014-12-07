import urllib, urllib2, csv
#'1.22.26.83' <--bad IP example
#'8.8.8.8' <--good IP example

spamFilePath = "Webportal/FlowQoS GUI/spam.cfg"

#Return TRUE if in spam blacklist, false otherwise
def isSpam(IP):
	#URL of site search is on. The site returns "Listed! see why" between lhsbl blocklist and whitelist if the site
	#is spam, so search for that. May run into issues if site is not correct (just assuming it is for now) or if error 
	#in connecting to site (no handler for connection issues or timeouts)
	url = "http://www.blacklistalert.org/"
	#Control input box is named 'q'
	form_data = {'q': IP}
	#Submit request and receive response
	params = urllib.urlencode(form_data)
	response = urllib2.urlopen(url, params)
	data = response.read()
	#Scan response between two headers for "Listed!". If found, IP is listed as spam
	ind1 = data.find("in LHSBL Blocklists")
	ind2 = data.find("in LHSBL Whitelists")
	findListed = data.find("Listed!", ind1, ind2)
	if findListed == -1:
		return False
	else:
		return True
        
class SpamChecker:

    def __init__(self, flowqos):
        self.flowqos = flowqos0
        
    def checkSpam(self, ipAddress):
        ipAddress = str(ipAddress)
        
        ipList = loadIpList(self.flowqos.dir + spamFilePath)
        ipObj = None
        for ip in ipList:
            if (ip.get("IP") == ipAddress):
                ipObj = ip
        if ipObj is not None:
            if(ipObj.get("blocked") == "1"):
                return True
            return False
        else:
            blocked = isSpam(ipAddress)
            ipList.append({"IP":ipAddress,"blocked":blocked,"user_defined":False})
            storeIpList(self.flowqos.dir + spamFilePath, ipList)
            return blocked
        return None
        

def loadIpList(file):
    ipList = None
    ipFile = None
    try:
        ipFile = open(file, 'r')
        while True:
            line = ipFile.readline()
            if not line:
                break
            full = json.loads(line)
            ipList = full.get("application_limit")
    finally:
        if ipFile is not None:
            ipFile.close()
    return ipList 

def storeIpList(file, ipList):
    try:
        ipFile = open(file, 'w')
        json.dump({"application_limit":deviceList}, deviceFile, separators=(',',':'))
    finally:
        if ipFile is not None:
            ipFile.close()
    return ipList
        
        
        
##Test case 1
#test = '8.8.8.8'
#print "Testing google IP 8.8.8.8, so should return false..."
#print isSpam(test)
#print "Testing example spam site 1.22.26.83. Should return true. Returns..."
#print isSpam("1.22.26.83")