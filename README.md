# garmin-sleep-scraping
This repository represents my work to pull my sleep data from Garmin.  The virtual enviroment used to execute these scripts has been captured in the `environment.yml` file.

`scrape_garmin_sleep.py` crawls through webpages to capture data.  It uses the package selenium to drive a Firefox browser though Garmin's sign-in page, then visits the sleep webpage for each date in the desired date range.  This script is incomplete because it was discovered that requesting json files would provide more information for each day.

`get_garmin_sleep_json.py` requests sleep data in json format.  It uses the packages selenium and seleniumwire to drive a Firefox browser though Garmin's sign-in page, then gets the requests headers and cookies from the browser session.  These are required to give a valid json request to Garmin.  The Garmin json is then saved to a user-defined directory as well a processed form of the data in csv.  This script was based on https://github.com/kristjanr/my-quantified-sleep/blob/master/parse.py

Some additional discussion of this project has been posted here: https://buckeye17.github.io/Scraping-Garmin/
