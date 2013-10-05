import json
import csv
import httplib
import urllib
from pprint import pprint

studentHistory = []
jasperSyllabus = None
jasperHandShakeParam = ''

#load kvc syllabus
kvc_json_data = open('oi38249376_kvc.json')
kvcData = json.load(kvc_json_data)
#pprint(data)
kvc_json_data.close()

def processPlanlets(planlets):
	for planlet in planlets:
		processPlanlet(planlet)

def processPlanlet(planlet):
	if planlet['planletType'] == 'CONTAINER':
		processPlanlets(planlet['childPlanlets'])
	else:
		processStudyItems(planlet['studyItems'])

def processStudyItems(studyItems):
	items = []
	
	for studyItem in studyItems:
		item = processStudyItem(studyItem)
		if not item is None:
			#pprint(item)
			f = open('output.csv', 'a')
			f.write(item['name'] + '\t' + item['createdAt'] + '\t' + item['updatedAt'] + '\n')

			#items.append([item['name'], item['createdAt'], item['updatedAt']])

	#print(items[0])
	#writeToCsv(items)
				

def processStudyItem(studyItem):
	result = studyItem

	if studyItem['status'] == 'COMPLETE':
		itemName = studyItem['name']
		if itemName.find('u003csupu003eu0026reg;u003c/supu003e') >= 0:
			itemName = itemName.replace('u003csupu003eu0026reg;u003c/supu003e', '')
			result['name'] = itemName
	else:
		result = None

	return result

def writeToCsv(items):
	
	
	#with open('output.csv', 'wb') as csvfile:
		csvWriter = csv.writer(csvfile, delimiter=',')
		csvWriter.writerow(items)

def doJasperInitHandhake():
	enParam = "enParams=" + jasperHandShakeParam
	headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "application/json"}
	conn = httplib.HTTPConnection("jasper.kaptest.com")
	conn.request("POST", "/initHandshake.aspx", enParam, headers)
	response = conn.getresponse()
	if response.status == 200:
		jasperCookie = response.getheader('set-cookie')

	conn.close()

	if jasperCookie != '':
		jasperSyllabus = getJasperSyllabus(jasperCookie)

def getJasperSyllabus(jasperCookie):
	headers = {"Accept": "application/json", "Cookie": jasperCookie}
	conn = httplib.HTTPConnection("jasper.kaptest.com")
	conn.request("GET", "/apps/delivery/xpathdata.aspx?objectType=syllabus&format=jsonNew", "", headers)
	response = conn.getresponse()
	if response.status == 200:
		global jasperSyllabus
		jasperSyllabus = json.loads(response.read())

	conn.close()

def processJasperSyllabusSections(sections):
	for section in sections:
		if section.get('sequence', None) is not None:
			processJasperSyllabusSequences(section['sequence'])
			
		if section.get('multiUseSequences', None) is not None:
			processJasperSyllabusSequences(section['multiUseSequences']['sequence'])

		if section.get('section', None) is not None:
			processJasperSyllabusSections(section['section'])
			

def processJasperSyllabusSequences(sequences):
	global studentHistory

	for sequence in sequences:
		print sequence['title'], sequence['name']
		if sequence['status'] == 'Completed':
			if not isInStudentHistory(sequence['name']):
				studentHistoryItem = {}
				studentHistoryItem['assetCode'] = sequence['name']
				studentHistoryItem['assetPath'] = sequence['path']
				studentHistoryItem['name'] = sequence['title']
				studentHistoryItem['dateCompleted'] = sequence['dateCompleted']

				studentHistory.append(studentHistoryItem)

def isInStudentHistory(assetCode):
	result = False

	for studentHistoryItem in studentHistory:
		if studentHistoryItem['assetCode'] == assetCode:
			result = True

	return result

def processKvcAssignments(assignments):
	global studentHistory

	for assignment in assignments:
		if not assignment['grade']['dateCompleted'] is None:
			assetcode = ''
			assetpath = ''
			if not assignment['assetCode'] is None:
				assetcode = assignment['assetCode']
				assetpath = assetcode

			studentHistoryItem = {}
			lastIndex = assetcode.rfind('/')
			if lastIndex >= 0:
				assetcode = assetcode[lastIndex + 1:]

			studentHistoryItem['assetCode'] = assetcode
			studentHistoryItem['assetPath'] = assetpath
			studentHistoryItem['name'] = assignment['name']
			studentHistoryItem['dateCompleted'] = assignment['grade']['dateCompleted']

			studentHistory.append(studentHistoryItem)

			# get jasper handshake param
			global jasperHandShakeParam
			if assetcode != '' and jasperHandShakeParam == '':
				jasperHandShakeParam = assignment['courseParameter'][0]['value']
			

def processKvcSyllabus(lessons):
	for lesson in lessons:
		if len(lesson['assignment']) > 0:
			processKvcAssignments(lesson['assignment'])

	#get jasper syllabus
	doJasperInitHandhake()

	if not jasperSyllabus is None:
		processJasperSyllabusSections(jasperSyllabus['syllabus']['section']['section'])

#doJasperInitHandhake()
processKvcSyllabus(kvcData['syllabus']['lesson'])
#pprint(studentHistory)




