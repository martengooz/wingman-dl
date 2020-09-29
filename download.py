#Or use the context manager
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.support.ui import WebDriverWait


chrome_options = Options()
#chrome_options.add_argument("--headless")
chrome_options.add_argument("user-data-dir=C:/Users/snobben/AppData/Local/Google/Chrome/User Data")

with Chrome(options=chrome_options) as driver:
    driver.implicitly_wait(15)
    driver.get("https://steamcommunity.com/id/martengooz/gcpd/730/?tab=matchhistorywingman")
    elements = driver.find_elements_by_xpath('//td[@class="csgo_scoreboard_cell_noborder"]/a')
    for element in elements:
        print(element.get_attribute('href'))

