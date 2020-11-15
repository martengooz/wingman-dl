import os
from types import CodeType
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
from selenium.common.exceptions import NoSuchElementException, InvalidArgumentException, TimeoutException, WebDriverException

STEAM_PAGE = "https://steamcommunity.com"


def parseArgs():
    """
    Handle command line arguments
    """
    parser = ArgumentParser(
        description='Download CS:GO Wingman matches from your community profile page.')
    browserGroup = parser.add_mutually_exclusive_group()
    browserGroup.add_argument('-c', '--chrome', action='store_true',
                              help='use Google Chrome')
    browserGroup.add_argument('-f', '--firefox', action='store_true',
                              help='use Mozilla Firefox')
    browserGroup.add_argument('-e', '--edge', action='store_true',
                              help='use Microsoft Edge')
    parser.add_argument('-p', '--profile',
                        metavar='profiledir',
                        type=str,
                        help='custom path to browser profile directory')
    parser.add_argument('-k', '--keep-compressed', action='store_true',
                        help="keep the compressed demo files after download")
    parser.add_argument('-n', '--no-extraction', action='store_true',
                        help="don't extract the compressed demo files")
    parser.add_argument('-w', '--wait', action='store_true',
                        help="start the broswer and wait for login before continuing")
    parser.add_argument('-d', '--destination',
                        metavar='destination',
                        type=str,
                        help='where to store the demos')
    return parser.parse_args()


def getMissingArguments(args):
    """
    If required arguments are missing, prompt for them 
    """
    args.missingRequired = False
    # Missing browser
    if not args.chrome and not args.edge and not args.firefox:
        args.missingRequired = True
        while(True):
            print()
            print("Which browser do you want to use?")
            print("1. Google Chrome")
            print("2. Mozilla Firefox")
            print("3. Microsoft Edge")
            browser = input("Please type a number [default 1]: ")
            if browser == "":
                args.chrome = True
                break
            try:
                browser = int(browser)
            except:
                continue
            if browser == 1:
                args.chrome = True
                break
            elif browser == 2:
                args.firefox = True
                break
            elif browser == 3:
                args.edge = True
                break
            else:
                continue

        # Ask whether the user is logged in
        if not args.wait:
            while(True):
                print()
                print("Are you already logged in?")
                print("1. Yes")
                print("2. No, I need to log in first (will open a new browser window)")
                loggedin = input("Please type a number (default 1): ")
                if loggedin == "":
                    break
                try:
                    loggedin = int(loggedin)
                except:
                    continue
                if loggedin == 1:
                    break
                elif loggedin == 2:
                    args.wait = True
                    break
                else:
                    continue

    if not args.destination:
        args.missingRequired = True
        customDestination = False
        while(True):
            print()
            print("Where do you want to save the demos?")
            print("1. The same directory as this program")
            print("2. My Downloads")
            print("3. Other (please specify next)")
            destination = input("Please type a number (default 1): ")
            if destination == "":
                args.destination = os.path.abspath(".")
                break
            try:
                destination = int(destination)
            except:
                continue
            if destination == 1:
                args.destination = os.path.abspath(".")
                break
            elif destination == 2:
                args.destination = os.getenv("USERPROFILE") + "\\Downloads"
                break
            elif destination == 3:
                customDestination = True
                break
            else:
                continue

        if customDestination:
            while(True):
                try:
                    path = input("Path to download directory: ")
                    if os.path.isdir(path):
                        args.destination = path
                        break
                    else:
                        print(
                            "Couldn't find that directory, please choose another or create it first!")
                except:
                    print(
                        "Couldn't find that directory, please choose another or create it first!")

    if args.missingRequired:
        print()
        print("Are these settings ok?")
        print("Will launch in " + getBrowserName(args))
        if args.wait:
            print(
                "Will open a new browser window and wait for you to login before scanning for demos")
        print("Demos will be saved to " + os.path.abspath(args.destination))
        res = input("Is this correct? [Y/N] (default Y):")
        if res.upper() == "Y" or res == "":
            print("Ok, starting wingman-dl")
        else:
            print("Ok, winman-dl aborted")
            exit()

    return args


def getWebDriver(args):
    """
    Get the appopiate driver for chosen browser
    """
    driver = None
    if args.chrome:
        options = ChromeOptions()
        options.page_load_strategy = 'eager'
        # Default profile directory
        userDataDir = os.getenv(
            'LOCALAPPDATA') + "\\Google\\Chrome\\User Data" if args.profile == None else args.profile
        options.add_argument("user-data-dir=" + userDataDir)
        driver = Chrome(options=options)

    elif args.firefox:
        options = FirefoxOptions()
        options.page_load_strategy = 'eager'
        # Default profile directory
        profiles = os.listdir(os.getenv('APPDATA') +
                              "\\Mozilla\\Firefox\\Profiles\\")
        # "xxxxxxxx.default-release" is the default profile for Release versions v67+
        default_profile = next(
            profile for profile in profiles if profile[-15:] == "default-release")
        userDataDir = os.getenv('APPDATA')+"\\Mozilla\\Firefox\\Profiles\\" + \
            default_profile if args.profile == None else args.profile
        fp = FirefoxProfile(userDataDir)
        driver = Firefox(fp, options=options)

    elif args.edge:
        options = EdgeOptions()
        options.page_load_strategy = 'eager'
        options.use_chromium = True
        # Default profile directory
        userDataDir = os.getenv(
            'LOCALAPPDATA') + "\\Microsoft\\Edge\\User Data" if args.profile == None else args.profile
        options.add_argument("user-data-dir=" + userDataDir)
        driver = Edge(options=options)

    return driver


def getBrowserName(args):
    if args.chrome:
        return "Chrome"
    elif args.firefox:
        return "Firefox"
    elif args.edge:
        return "Edge"
    return ""


def getUser(args, driver):
    """
    Get the logged in user
    """
    driver.get(STEAM_PAGE)
    try:  # Check for login button on homepage
        driver.find_element_by_link_text("login")
        if args.wait:  # Wait for login
            profileLinkElement = WebDriverWait(driver, 600).until(
                EC.presence_of_element_located((By.CLASS_NAME, "user_avatar")))
            username = profileLinkElement.get_attribute('href').split("/")[-2]
            return username
        return False
    except NoSuchElementException:  # Desired outcome, user is logged in
        profileLinkElement = driver.find_element_by_class_name(
            "user_avatar")  # top right profile pic
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
                if user.isdigit():
                    statlink = STEAM_PAGE + "/profiles/" + user + "/gcpd/730/?tab=matchhistorywingman"
                else:
                    statlink = STEAM_PAGE + "/id/" + user + "/gcpd/730/?tab=matchhistorywingman"
                driver.get(statlink)
                # TODO: Load more wingman matches
                # td: cell for download button, a: download link
                linkElements = driver.find_elements_by_xpath(
                    '//td[@class="csgo_scoreboard_cell_noborder"]/a')
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
    except WebDriverException:
        if args.chrome:
            print("ERROR: Could not find chromedriver.exe")
            print("Please download the correct version from https://chromedriver.chromium.org/ and put in the same directory as wingman-dl.exe")
        if args.firefox:
            print("ERROR: Could not find geckodriver.exe")
            print("Please download the correct version from https://github.com/mozilla/geckodriver/releases and put in the same directory as wingman-dl.exe")
        if args.firefox:
            print("ERROR: Could not find msedgedriver.exe")
            print("Please download the correct version from https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/ and put in the same directory as wingman-dl.exe")
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
        print(
            f"ERROR: Failed to read destination path {args.destination}. Make sure you have the right permissions and that the directory exist.")
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
                with open(args.destination + "/" + demoname, 'wb') as f:
                    f.write(r.content)
            except:
                print(f"ERROR: Could not write demo {demoname} to disk")
                erroredDemos += 1
                continue

            # Unzip the compressed demo
            if not args.no_extraction:
                try:
                    print("Unzipping", unzippedname.split("/")[-1])
                    with BZ2File(args.destination + "/" + demoname) as compressed:
                        data = compressed.read()
                        open(args.destination + "/" +
                             unzippedname, 'wb').write(data)
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
            print(
                f"ERROR: Could not download the demo. Maybe the steam download servers are down or link broken. Link: {link}")
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
    args = getMissingArguments(args)
    links = getLinks(args)
    res = downloadDemos(args, links)
    printResult(res)
    if args.missingRequired:  # Wait for user input before exiting
        input()
