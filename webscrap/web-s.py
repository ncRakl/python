from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.command import Command
from selenium.common.exceptions import TimeoutException
from random import randint
import json
import re
import http.client
import socket

LOADING_ELEMENT_XPATH = '//div[@class="spinner-overlay"]'

class swSpider():

	def __init__(self):
		self.url_to_crawl = "https://swarfarm.com/bestiary/"
		self.monsters = []

	def get_status(self):
		try:
			self.driver.execute(Command.STATUS)
			return "Alive"
		except (socket.error, http.client.CannotSendRequest):
			return "Dead"

	def start_driver(self):
		print('\t\tstarting driver...')
		chrome_options = Options()
		chrome_options.add_argument("--headless")
		chrome_options.add_argument("disable-infobars")
		chrome_options.add_argument("--disable-extensions")
		chrome_options.add_argument("--no-sandbox")
		chrome_options.add_argument("--disable-dev-shm-usage")
		self.driver = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', chrome_options=chrome_options)

	def close_driver(self):
		print('\t\tclosing driver...')
		self.driver.quit()
		print('\t\t\tclosed!')

	def get_page(self, url):
		print('\tgetting page...')
		if self.get_status() == "Alive":
			self.close_driver()
			self.start_driver()
		else:
			self.start_driver()
		self.driver.get(url)

	def wait_for_loader(self):
		print('\twaiting for loader to vanish...')
		while True:
			try:
				WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, LOADING_ELEMENT_XPATH)))
			except TimeoutException:
				break

	def grabMonsters(self):
		print('grabbing monsters...')
		self.get_page(self.url_to_crawl)
		# De la page x à ...
		for x in range(12):
			self.wait_for_loader()
			print('\tScanning page '+str(x+1)+'...')
			# On charge le code html dans content
			content = self.driver.page_source
			# On instancie un BeautifulSoup avec content
			self.soup = BeautifulSoup(content, 'html.parser')
			# Pour chaque monstre de la page
			for monster in self.soup.find_all('tr', attrs={'role':'row', 'class':None}):
				data = {} # Pour stocker les infos du monstre
				infos = monster.find_all('td') # Récupère les éléments td
				url = re.sub('/bestiary/', '', infos[1].find('a', href=True)['href'])
				
				name = re.sub('\s+', '', infos[1].text)
				stars = re.sub('\s+', '', infos[2].text)
				family = re.sub('\s+', '', infos[6].text)
				awakensto = re.sub('\s+', '', infos[5].text)
				element = re.sub('\s+', '', infos[3].text)
				# Si le monstre est éveillé alors ...
				if awakensto == '' and family != '':
					data['name'] = name
					data['stars'] = str(int(stars)-1)
					data['family'] = family
					data['element'] = element
					data['url'] = url
				# Si data n'est pas vide, on rajoute les données à la variable monsters
				if data:
					self.monsters.append(data)

			# Navigation vers la page suivante
			pageBtn = self.driver.find_elements_by_xpath('//div[@class="panel-heading"]/div[@class="btn-group pull-right"]/button')
			pageBtn[len(pageBtn)-1].click()
		self.completeMonsters()

	def completeMonsters(self):
		print('Completing monsters...')
		for monster in self.monsters:
			print('\n')
			print('Parsing '+monster['name']+' data...')
			self.get_page(self.url_to_crawl + monster['url'])
			content = self.driver.page_source
			self.soup = BeautifulSoup(content, 'html.parser')
			rows = self.soup.find_all('div', attrs={'class':'col-lg-6'})
			if(len(rows)>2):
				skills = rows[2].find('div', attrs={'class':'row condensed'})
			else:
				skills = rows[0].find('div', attrs={'class':'row condensed'})
			i=1
			monster['skills'] = {}
			for skill in skills.find_all('div', attrs={'class':['col-lg-3','col-lg-4']}):
				monster['skills'][i] = {}
				monster['skills'][i]['title'] = skill.find('p', attrs={'class':'panel-title'}).text
				for box in skill.find_all('li', attrs={'class':'list-group-item'}):
					heading = ''
					if box.find('p', attrs={'class':'list-group-item-heading'}):
						heading = box.find('p', attrs={'class':'list-group-item-heading'}).text

					if heading == '':
						monster['skills'][i]['desc'] = re.sub('\s+', ' ', box.find('p').text.strip().replace('\n',''))
					elif heading == 'Level-up Progress:':
						monster['skills'][i]['skillup'] = {}
						j=2
						for skillup in box.find_all('li'):
							monster['skills'][i]['skillup'][j] = {}
							monster['skills'][i]['skillup'][j] = 'Lv'+str(j)+': '+skillup.text
							j = j+1
					elif heading == 'Multiplier Formula:':
						monster['skills'][i]['mult'] = box.find('p', attrs={'class':None}).text
				i=i+1
			print(json.dumps(monster, ensure_ascii=False, indent=4))

	def parse(self):
		self.start_driver()
		self.grabMonsters()
		self.close_driver()

		if self.monsters:
			return self.monsters
		else:
			return False, False

#"""
sw = swSpider()
monsters = sw.parse()

with open('monsters.json', 'w') as f:
	json.dump(sw.monsters, f, ensure_ascii=False, indent=4)
#"""

"""
with open('monsters.json') as json_file:
	data = json.load(json_file)
	result = []
	for monster in data:
		if monster['family']=='Sylph':
			result.append(monster)

print(json.dumps(result, ensure_ascii=False, indent=4))
"""