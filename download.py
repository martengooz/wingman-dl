from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Chrome, Firefox, FirefoxProfile
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions

import requests
import bz2
import os
import argparse

STEAM_PAGE = "https://steamcommunity.com"

def parseArgs():
    parser = argparse.ArgumentParser(description='Download CS:GO Wingman matches from your community profile page.')
    parser.add_argument('destination',
                        metavar='destination',
                        type=str,
                        help='where to store the demos')
    parser.add_argument('-c', '--chrome', action='store_true',
                        help='use Chrome')
    parser.add_argument('-f', '--firefox', action='store_true',
                    help='use Firefox')
    parser.add_argument('-p', '--profile',
        metavar='profiledir',
        type=str,
        help='custom path to browser profile directory')
    return parser.parse_args()

def getWebDriver(args):
    """
    docstring
    """
    driver = None
    if args.chrome:
        options = ChromeOptions()
        options.page_load_strategy = 'eager'
        options.add_argument("--disable-extensions")
        userDataDir = os.getenv('LOCALAPPDATA') + "\\Google\\Chrome\\User Data" if args.profile == None else args.profile
        options.add_argument("user-data-dir="+ userDataDir)
        driver = Chrome(options=options)

    elif args.firefox:
        options = FirefoxOptions()
        options.page_load_strategy = 'eager'
        options.add_argument("--disable-extensions")
        profiles = os.listdir(os.getenv('APPDATA')+"\\Mozilla\\Firefox\\Profiles\\")
        default_profile = next(profile for profile in profiles if profile[-15:] == "default-release")
        userDataDir = os.getenv('APPDATA')+"\\Mozilla\\Firefox\\Profiles\\" + default_profile if args.profile == None else args.profile
        fp = FirefoxProfile(userDataDir)
        driver = Firefox(fp, options=options)

    elif args.edge:
        pass

    return driver

def getUser(driver):
    driver.get(STEAM_PAGE)
    try:
        driver.find_element_by_link_text("login")
        print("No user is logged in")
        return False
    except NoSuchElementException:
        profileLinkElement = driver.find_element_by_class_name("user_avatar")
        username = profileLinkElement.get_attribute('href').split("/")[-2]
        print(f"User {username} is logged in")
        return username


def getLinks(args):
    links = []
    with getWebDriver(args) as driver:
        user = getUser(driver)
        if user:
            # Get the demo download links
            driver.get(STEAM_PAGE + "/id/" + user + "/gcpd/730/?tab=matchhistorywingman")

            # TODO: Load more wingman matches
            try:
                linkElements = driver.find_elements_by_xpath('//td[@class="csgo_scoreboard_cell_noborder"]/a')
                for element in linkElements:
                    links.append(element.get_attribute('href'))
                print(f"Found {len(links)} demos")
            except NoSuchElementException:
                print("Could not find any recent matches") 
            driver.quit()
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
    print("Exiting")