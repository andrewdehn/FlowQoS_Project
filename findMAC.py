import urllib2, csv

def getCompany(given):
	#Query API at macvendor
	query = "http://www.macvendorlookup.com/api/v2/" + given
	jsonResult = urllib2.urlopen(query).read()
	#Find company name returned by api (possible error if no company?)
	indexStart = jsonResult.find("company\":") + 10
	indexEnd = jsonResult.find(",\"addressL1")-1
	company = jsonResult[indexStart:indexEnd]
	#Create dictionary to return later, 'company' and 'devices' keys
	#'devices' is an array of all devices matched to the company
	toReturn = {'company' : company, 'devices' : []}
	#Open 'maclist.csv' to find what devices match the given company
	#CSV file, first entry in each row is device, rest are companies for that device
	with open('maclist.csv', 'r') as csvfile:
		reader = csv.reader(csvfile, delimiter=",")
		#Iterate through all rows, save device type
		#If match found in company list and MAC company, add device to toReturn
		#Match is based on first word of company returned ('Microsoft corp.' matches 'microsoft')
		for row in reader:
			#Take device type off of each row
			device = row.pop(0)
			for temp in row:
				if company.split(' ', 1)[0].lower() in temp.lower():
					curr = toReturn['devices']
					curr.append(device)
					toReturn['devices'] = curr
					break
	return toReturn
	
test = "00-23-14-66-4D-90"
test2 = "64-5A-04-C4-9C-D5"
company = getCompany(test2)
print company
