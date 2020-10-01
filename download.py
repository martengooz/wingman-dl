from selenium.common.exceptions import NoSuchElementException, InvalidArgumentException
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
    try: # Check for login button on homepage
        driver.find_element_by_link_text("login")
        
        return False
    except NoSuchElementException: # Desired outcome, user is logged in
        profileLinkElement = driver.find_element_by_class_name("user_avatar") # top right profile pic 
        username = profileLinkElement.get_attribute('href').split("/")[-2]
        return username


def getLinks(args):
    links = []
    try:
        with getWebDriver(args) as driver:
            user = getUser(driver)
            if user:
                print(f"User {user} is logged in")
                # Get the demo download links
                driver.get(STEAM_PAGE + "/id/" + user + "/gcpd/730/?tab=matchhistorywingman")
                # TODO: Load more wingman matches
                linkElements = driver.find_elements_by_xpath('//td[@class="csgo_scoreboard_cell_noborder"]/a') # td: cell for download button, a: download link
                for element in linkElements:
                    links.append(element.get_attribute('href'))
                print(f"Found {len(links)} demos")
            else:
                print("ERROR: No user is logged in")
            driver.quit()
    except InvalidArgumentException:
        print("ERROR: Browser is already running. Please close all instances of it before running this software.")
    except NoSuchElementException:
        print("ERROR: Could not find any recent matches")     
    return links

def downloadDemos(args, links):
    try:
        alreadyDownloaded = os.listdir(args.destination)
    except:
        print(f"ERROR: Failed to read destination path {args.destination}. Make sure you have the right permissions and that the directory exist.") 
        return
    skippedDemos = 0
    downloadedDemos = 0
    erroredDemos = 0
    for link in links:
        demoname = link.split("/")[-1]
        unzippedname = demoname[:-4]
        
        # Check if already downloaded
        if unzippedname in alreadyDownloaded:
            print(f"Skipping {demoname} (already downloaded)")
            skippedDemos += 1
            continue
        
        # Download
        print("Downloading", demoname)
        r = requests.get(link)
        if r.ok:
            # Write compressed demo to disk
            try: 
                with open(args.destination + "/" + demoname , 'wb') as f:
                    f.write(r.content)
            except: 
                print(f"ERROR: Could not write demo {demoname} to disk")
                erroredDemos += 1
                continue
            
            # Unzip the compressed demo
            try:
                print("Unzipping", unzippedname.split("/")[-1])
                with bz2.BZ2File(args.destination + "/" + demoname) as compressed:
                    data = compressed.read()
                    open(args.destination + "/" + unzippedname, 'wb').write(data)
            except: 
                print(f"ERROR: Could not extract demo {demoname}")
                erroredDemos += 1
                continue
            
            # Delete compressed demo
            try:
                print("Removing", demoname)
                os.remove(args.destination + "/" + demoname)
            except:
                print(f"ERROR: Could not delete {demoname}")
                erroredDemos += 1
                continue
            downloadedDemos += 1
        else:
            print(f"ERROR: Could not download the demo. Maybe the steam download servers are down or link broken. Link: {link}")
    return skippedDemos, downloadedDemos, erroredDemos 

def printResult(res):
    skippedDemos, downloadedDemos, erroredDemos = res
    print()
    print("RESULTS:")
    print("Downloaded", downloadedDemos)
    print("Skipped", skippedDemos)
    print("Failed", erroredDemos)
    print()

if __name__ == "__main__":
    args = parseArgs()
    links = getLinks(args)
    res = downloadDemos(args, links)
    printResult(res)