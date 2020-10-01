# wingman-dl

## Easy installation
The easiest way to run wingman-dl is to [download the exe](https://github.com/martengooz/wingman-dl/releases). 

Download the appropiate Webdriver for your browser:

**If running Chrome or Edge you will have to close all browser windows before running wingman-dl in order for it to use the logged in user.**
* [Chrome](https://chromedriver.chromium.org/downloads)
* [Edge](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/)

* [Firefox](https://github.com/mozilla/geckodriver/releases)

Save the webdriver .exe in the same directory as `wingman-dl.exe`.

Done!

## Install from source
Download the source and appropiate webdriver as specified in easy installation.

Install [Python 3.4+](https://www.python.org/downloads)

Install the required packages by running: 
```
pip install -r requirements.txt
```

## Usage
### Using the text menu
wingman-dl can be used by just running the application. It will prompt you for what browser to use and where to save the demos.

### Using the cli
wingman-dl can also be used with the command line without user input. If any of the required arguments are not provided, wingman-dl will prompt you for the missing ones.
```
usage: wingman-dl.py [BROWSER] [OPTIONS] [-d destination]

Required arguments:
  BROWSERS:
        -c, --chrome            Use Google Chrome
        -f, --firefox           Use Mozilla Firefox
        -e, --edge              Use Microsoft Edge

  -d, --destination destination Where to store the demos

optional arguments:
  -h, --help                    Show this help message and exit
  -p, --profile profiledir      Custom path to browser profile directory
  -k, --keep-compressed         Keep the compressed demo files after download
  -n, --no-exctraction          Don't extract the compressed demo files
  -w, --wait                    Start the brower and wait for login before continuing
```