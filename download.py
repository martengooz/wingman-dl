import os
import requests
from bz2 import BZ2File
from argparse import ArgumentParser
from selenium.webdriver import Chrome, Firefox, FirefoxProfile
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from msedge.selenium_tools.webdriver import WebDriver as Edge
from msedge.selenium_tools.options import Options as EdgeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, InvalidArgumentException, TimeoutException

STEAM_PAGE = "https://steamcommunity.com"

def parseArgs():
    """
    Handle command line arguments
    """
    parser = ArgumentParser(description='Download CS:GO Wingman matches from your community profile page.')
    parser.add_argument('destination',
                        metavar='destination',
                        type=str,
                        help='where to store the demos')
    parser.add_argument('-c', '--chrome', action='store_true',
                        help='use Google Chrome')
    parser.add_argument('-f', '--firefox', action='store_true',
                    help='use Mozilla Firefox')
    parser.add_argument('-e', '--edge', action='store_true',
                    help='use Microsoft Edge')
    parser.add_argument('-p', '--profile',
        metavar='profiledir',
        type=str,
        help='custom path to browser profile directory')
    parser.add_argument('-k', '--keep-compressed', action='store_true',
                help="keep the compressed demo files after download")
    parser.add_argument('-n', '--no-exctraction', action='store_true',
                help="don't extract the compressed demo files")
    parser.add_argument('-w', '--wait', action='store_true',
                help="start the brower and wait for login before continuing")
    return parser.parse_args()

def getWebDriver(args):
    """
    Get the appopiate driver for chosen browser
    """
    driver = None
    if args.chrome:
        options = ChromeOptions()
        options.page_load_strategy = 'eager'
        options.add_argument("--disable-extensions")
        userDataDir = os.getenv('LOCALAPPDATA') + "\\Google\\Chrome\\User Data" if args.profile == None else args.profile # Default profile directory
        options.add_argument("user-data-dir="+ userDataDir)
        driver = Chrome(options=options)

    elif args.firefox:
        options = FirefoxOptions()
        options.page_load_strategy = 'eager'
        options.add_argument("--disable-extensions")
        profiles = os.listdir(os.getenv('APPDATA')+"\\Mozilla\\Firefox\\Profiles\\") # Default profile directory
        default_profile = next(profile for profile in profiles if profile[-15:] == "default-release") # "xxxxxxxx.default-release" is the default profile for Release versions v67+
        userDataDir = os.getenv('APPDATA')+"\\Mozilla\\Firefox\\Profiles\\" + default_profile if args.profile == None else args.profile
        fp = FirefoxProfile(userDataDir)
        driver = Firefox(fp, options=options)

    elif args.edge:
        options = EdgeOptions()
        options.page_load_strategy = 'eager'
        options.use_chromium = True
        options.add_argument("--disable-extensions")
        userDataDir = os.getenv('LOCALAPPDATA') + "\\Microsoft\\Edge\\User Data" if args.profile == None else args.profile # Default profile directory
        options.add_argument("user-data-dir="+ userDataDir)
        driver = Edge(options=options)

    return driver

def getUser(args, driver):
    """
    Get the logged in user
    """
    driver.get(STEAM_PAGE)
    try: # Check for login button on homepage
        driver.find_element_by_link_text("login")
        if args.wait: # Wait for login
            profileLinkElement = WebDriverWait(driver, 600).until(
            EC.presence_of_element_located((By.CLASS_NAME, "user_avatar")))
            username = profileLinkElement.get_attribute('href').split("/")[-2]
            return username
        return False
    except NoSuchElementException: # Desired outcome, user is logged in
        profileLinkElement = driver.find_element_by_class_name("user_avatar") # top right profile pic 
        username = profileLinkElement.get_attribute('href').split("/")[-2]
        return username
    except TimeoutException: 
        print("Could not detect a user login within 10 minutes")
        return False


def getLinks(args):
    """
    Scan the steam community page for wingman demo links
    """
    links = []
    try:
        with getWebDriver(args) as driver:
            user = getUser(args, driver)
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
    """
    Download demos from the accumulated links
    """
    skippedDemos = 0
    downloadedDemos = 0
    erroredDemos = 0

    try:
        alreadyDownloaded = os.listdir(args.destination)
    except:
        print(f"ERROR: Failed to read destination path {args.destination}. Make sure you have the right permissions and that the directory exist.") 
        return

    for link in links:
        demoname = link.split("/")[-1]
        unzippedname = demoname[:-4]
        
        # Check if already downloaded
        if unzippedname in alreadyDownloaded or demoname in alreadyDownloaded:
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
            if not args.no_exctraction:
                try:
                    print("Unzipping", unzippedname.split("/")[-1])
                    with BZ2File(args.destination + "/" + demoname) as compressed:
                        data = compressed.read()
                        open(args.destination + "/" + unzippedname, 'wb').write(data)
                except: 
                    print(f"ERROR: Could not extract demo {demoname}")
                    erroredDemos += 1
                    continue
            
            # Delete compressed demo
            if not args.keep_compressed:
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
    """
    Prints the number of downloaded, skipped and errored demos
    """
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