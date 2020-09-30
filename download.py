from selenium.webdriver import Chrome, Firefox, FirefoxProfile
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions

import requests
import bz2
import os
import argparse

def parseArgs():
    parser = argparse.ArgumentParser(description='Download CS:GO Wingman matches from your community profile page.')
    parser.add_argument('destination',
                        metavar='destination',
                        type=str,
                        help='where to store the demos')

    parser.add_argument('-c', '--chrome', action='store_true',
                        help='use Chrome')
    parser.add_argument('-u', '--user-data-dir',
                        metavar='datadir',
                        type=str,
                        help='custom path to chrome data dir (default %%LOCALAPPDATA%%/Google/Chrome/User Data)')

    parser.add_argument('-f', '--firefox', action='store_true',
                    help='use Firefox')

    return parser.parse_args()

def getLinks(args):
    links = []
    STEAM_PAGE = "https://steamcommunity.com"
    if args.chrome:
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--disable-extensions")
        userDataDir = os.getenv('LOCALAPPDATA') + "\\Google\\Chrome\\User Data" if args.user_data_dir == None else args.user_data_dir
        chrome_options.add_argument("user-data-dir="+ userDataDir)
        print("Starting Chrome, please wait...")
        with Chrome(options=chrome_options) as driver:
            driver.get(STEAM_PAGE)
            profileLinkElement = driver.find_element_by_class_name("user_avatar")
            username = profileLinkElement.get_attribute('href').split("/")[-2]
            driver.get(STEAM_PAGE + "/id/" + username + "/gcpd/730/?tab=matchhistorywingman")
            linkElements = driver.find_elements_by_xpath('//td[@class="csgo_scoreboard_cell_noborder"]/a')
            for element in linkElements:
                links.append(element.get_attribute('href'))
            driver.quit()
    if args.firefox:
        firefox_options = FirefoxOptions()
        firefox_options.add_argument("--disable-extensions")
        userDataDir = os.getenv('APPDATA')+"\\Mozilla\\Firefox\\Profiles\\n35rrdqb.default-release" if args.user_data_dir == None else args.user_data_dir ## Fix
        userDataDir = userDataDir.replace("\\", "/")
        print(userDataDir)
        fp = FirefoxProfile(userDataDir)
        print("Starting Firefox, please wait...")
        with Firefox(fp, options=firefox_options) as driver:
            driver.get(STEAM_PAGE)
            driver.implicitly_wait(10) # Remove
            profileLinkElement = driver.find_element_by_class_name("user_avatar")
            username = profileLinkElement.get_attribute('href').split("/")[-2]
            driver.get(STEAM_PAGE + "/id/" + username + "/gcpd/730/?tab=matchhistorywingman")
            linkElements = driver.find_elements_by_xpath('//td[@class="csgo_scoreboard_cell_noborder"]/a')
            for element in linkElements:
                links.append(element.get_attribute('href'))
            driver.quit()
    print("Found", len(links), "demos")
    return links

def downloadDemos(args, links):
    for link in links:
        demoname = link.split("/")[-1]
        unzippedname = args.destination + "/" + demoname[:-4]

        print("Downloading", demoname)
        r = requests.get(link)
        with open(args.destination + "/" + demoname , 'wb') as f:
            f.write(r.content)

        print("Unzipping", unzippedname.split("/")[-1])
        with bz2.BZ2File(args.destination + "/" + demoname) as compressed:
            data = compressed.read()
            open(unzippedname, 'wb').write(data)
        
        print("Removing", demoname)
        os.remove(args.destination + "/" + demoname)

if __name__ == "__main__":
    args = parseArgs()
    links = getLinks(args)
    downloadDemos(args, links)