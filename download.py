from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options  
import requests
import bz2
import os

DOWNLOAD_DIR = "D:/Users/snobben/dev/wingman-dl/"

chrome_options = Options()
#chrome_options.add_argument("--headless")
chrome_options.add_argument("user-data-dir=C:/Users/snobben/AppData/Local/Google/Chrome/User Data")

def removeFiles(files):
    for file in files:
        os.remove(file)

with Chrome(options=chrome_options) as driver:
    driver.implicitly_wait(15)
    driver.get("https://steamcommunity.com/id/martengooz/gcpd/730/?tab=matchhistorywingman")
    elements = driver.find_elements_by_xpath('//td[@class="csgo_scoreboard_cell_noborder"]/a')
    links = []
    for element in elements:
        links.append(element.get_attribute('href'))
    
    for link in links:
        demoname = link.split("/")[-1]
        r = requests.get(link)
        with open(DOWNLOAD_DIR + demoname , 'wb') as f:
            f.write(r.content)
    
        with bz2.BZ2File(DOWNLOAD_DIR + demoname) as compressed:
            data = compressed.read()
            newfilepath = DOWNLOAD_DIR + demoname[:-4]
            open(newfilepath, 'wb').write(data)
        
        os.remove(DOWNLOAD_DIR + demoname)