#Or use the context manager
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.options import Options  

chrome_options = Options()
#chrome_options.add_argument("--headless")

with Chrome(chrome_options=chrome_options) as driver:
    driver.get("https://google.com")