##############################################################################################################################################################
################ US Patent Office Web Scraper
################ Given a Patent Number, program gets issue date, assignee, number of reference patents, reissue status, reference patent #, issue date, and assignee
################ Input: A file with a patent number on each line
################ Output: A file for each initial patent number with designated data
########################################################################################################################################################
import re
import urllib2
from bs4 import BeautifulSoup

class PatentScraper(object):
	### variables for and regular expression patterns for processing data
	def __init__(self):
		self.month_dict = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12, "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6, "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12}
		self.date_pattern = re.compile(r'[a-zA-Z]+\s\d{1,2}\D{1}\s\d{4}')
		self.reissue_pattern = re.compile(r'[R]{1}[E]{1}[0-9,]')
		self.number_pattern = re.compile(r'[0-9,]')
	
	### generate the url to be opened after being given the patent number
	def generateUrl(self, patentNumber):
		return "http://patft.uspto.gov/netacgi/nph-Parser?Sect1=PTO2&Sect2=HITOFF&p=1&u=%2Fnetahtml%2FPTO%2Fsearch-bool.html&r=1&f=G&l=50&co1=AND&d=PTXT&s1={0}.PN.&OS=PN/{0}&RS=PN/{0}".format(patentNumber)

	### open url and return the object containing the data from the url
	### return false if there is an error
	def openUrl(self, url):
		try:
			response = urllib2.urlopen(url)
			return response
		except (ValueError, urllib2.URLError), e:
			print e
			return False
	
	
	def setPage(self, patentNumber):
		## given a patent number, set the class object that holds the data for the given URL
		url = self.generateUrl(patentNumber)
		self.response = self.openUrl(url)
		if self.response == False:
			print "Failed opening."
			exit()
		
		## if successful, then start scraping data for relevant information
		self.processPage()
		self.searchReferencesLink()

	
	def processPage(self):
		## format url data into form more amenable for processing
		self.response = self.response.read()
		self.response = self.response.encode('ascii', 'ignore').decode('ascii')
		self.soup = BeautifulSoup(self.response)

		self.row_list = self.soup.find_all('tr')
		self.center_list = self.soup.find_all('center')


	def returnAssignee(self):
		# iterate through page to find the assignee of the page
		result_list = []
		for row in self.row_list:
				for string in row.stripped_strings:
					if re.match("Assignee", string) != None:
						for data in row.find_all('td'):
							for output in data.stripped_strings:
								result_list.append(output)
		return result_list

	def returnDate(self):
		
		year_check = 0
		month_check = 0
		issued_date = ""
	
		## iterate through rows in the page to find relevant string
		for row in self.row_list:

			for string in row.stripped_strings:
				string = string.lstrip()
				string = string.rstrip()
				length = len(string)
				## if string contains a date pattern, make sure it is the correct, most recent, issue date
				if re.match(self.date_pattern, string) != None:

					year_check_list = string.split(',')
					month_check_list = string.split(' ')
					year_check_list[1] = year_check_list[1].lstrip()

					year = year_check_list[1][0:4]
					month = month_check_list[0]
					month_number = self.month_dict[month]
					year = int(year)

					if year > year_check:
						issued_date = string
						year_check = year
						month_check = month_number

					elif year == year_check:
						if month_number > month_check:
							issued_date = string
							month_check = month_number
		
		return issued_date

	def searchReferencesLink(self):
		## search for the references link
		references_link = []

		for center in self.center_list:
			for bold in center.find_all('b'):
				for string in bold.stripped_strings:
					if re.match("References Cited", string):
						for a in bold.findAll('a',href=True):
							references_link.append(a['href'])
		## if references are found then pass the link to the function that opens reference URL
		if len(references_link) == 1:
			self.setReferencesFile(references_link[0])
		return 
	
	def setReferencesFile(self, referenceLink):
		#sets the object containing the data for the reference patents
		referenceUrl = "http://patft.uspto.gov{0}".format(referenceLink)
		self.reference_file = self.openUrl(referenceUrl)
		self.reference_file = self.reference_file.read()
		self.reference_file = self.reference_file.encode('ascii', 'ignore').decode('ascii')
		self.reference_file = BeautifulSoup(self.reference_file)



	def returnReferenceIDs(self):
		# retrieves the IDS from the reference file
		ids_list = []
		next_link = ""
		no_next_page_avaliable = True

		
		while no_next_page_avaliable == True:

			self.reference_table = self.reference_file.find_all('td')
			## iterates through all possible patents numbers
			## appends to ids_list if relevant id is found
			for data in self.reference_table:
				for a in data.find_all('a'):
		
					for img in a.find_all('img'):
						if img['alt'] == "[NEXT_LIST]":
							next_link += a['href']
							no_next_page_avaliable = False

					for string in a.stripped_strings:
						if re.match(self.number_pattern, string) != None or re.match(self.reissue_pattern, string) != None:
							ids_list.append(string)
			
			if no_next_page_avaliable == False:
				self.setReferencesFile(next_link)
				next_link = ""

				no_next_page_avaliable = True
			else:

				no_next_page_avaliable = False
		

		return ids_list



if __name__ == "__main__":

	patentObject = PatentScraper()
	filename = str(raw_input("Enter the file name that contains the patentNumbers you'd like to process: "))

	try:
		inputFile = open(filename, 'r')
	except:
		print "No file found with that name"
		exit()
	
	## each line represents a patent number to be processed
	
	for line in inputFile:
		line = line.strip('\n')
		outputFile = open(line, 'w')
		patentObject.setPage(line)
		
		outputFile.write("Primary Patent #: ")
		outputFile.write(line)
		outputFile.write("\n")
		
		# functions retrieve relevant issue data
		if re.match(r'[R]{1}[E]{1}[0-9,]', line):
			outputfile.write("Patent is a reissue." + "\n")
		outputFile.write("Primary Patent Issue date: ")
		outputFile.write(patentObject.returnDate())
		outputFile.write("\n")
		outputFile.write("Primary Patent Assignee: ")
		
		list_of_assignees = patentObject.returnAssignee()
		
		for element in list_of_assignees:
			outputFile.write(element)
			outputFile.write("\n")
		
		## return reference ids and retrieve the data for those reference IDS
		outputFile.write("Number of References: ")
		list_of_references = patentObject.returnReferenceIDs()
		outputFile.write(str(len(list_of_references)))
		outputFile.write("\n")
		count = 0
		if len(list_of_references) > 0:
			for reference in list_of_references:
				print count
				patentObject.setPage(reference)
				outputFile.write("Reference Patent #: ")
				outputFile.write(reference)
				outputFile.write("\n")
				outputFile.write("Reference Patent Issue date: ")
				outputFile.write(patentObject.returnDate())
				outputFile.write("\n")
				outputFile.write("Reference Patent Assignee: ")

				list_of_assignees = patentObject.returnAssignee()
				count += 1
				for element in list_of_assignees:
					outputFile.write(element)
					outputFile.write("\n")
		
		outputFile.close()







		
