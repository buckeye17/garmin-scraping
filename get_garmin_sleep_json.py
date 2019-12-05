"""
Pull my Garmin sleep data via json requests.

This script was adapted from: https://github.com/kristjanr/my-quantified-sleep
The aforementioned code required the user to manually define
headers and cookies.  It also stored all of the data within Night objects.

My modifications include using selenium to drive a Firefox browser.  This avoids
the hassle of get headers and cookies (the cookies would have to be updated
everytime the Garmin session expired).  It also segments data requests because
Garmin will respond with an error if more than 32 days are requested.  Lastly,
data is stored as a pandas dataframe and then written to a user-defined directory
as a csv file.
"""

#import base packages
import datetime, json, re
from itertools import chain

#import pip-installed packages
import pytz, requests
import numpy as np
import pandas as pd
from seleniumwire import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

#import custom project packages
from night import Night

#input variables
proj_path = "C:/Users/adiad/Anaconda3/envs/BasicDataScience/Projects/my_sleep/" #read/write data dir
run_browser_headless = True #will hide Firefox during execution if True
browser_action_timeout = 20 #max time (seconds) for browser wait operations
start_date = '2017-03-01' #first date to pull sleep data
end_date = str(datetime.date.today() - datetime.timedelta(days = 1)) #last date to pull sleep data
user_name = "email address" #Garmin username
password = "password" #Garmin password
signin_url = "https://connect.garmin.com/signin/" #Garmin sign-in webpage
sleep_url_base = "https://connect.garmin.com/modern/sleep/" #Garmin sleep base URL (sans date)
sleep_url_json_req = "https://connect.garmin.com/modern/proxy/wellness-service/wellness/dailySleepsByDate"

def download(start_date, end_date, headers, session_id):
    params = (
        ('startDate', start_date),
        ('endDate', end_date),
        ('_', session_id),
    )

    response = requests.get(sleep_url_json_req, headers=headers, params=params)
    if response.status_code != 200:
        print("RESPONSE ERROR RECEIVED:")
        print('Status code: %d' % response.status_code)
        response_dict = json.loads(response.content.decode('UTF-8'))
        print('Content: %s' % response_dict["message"])
        raise Exception
    return response

def download_to_json(start_date, end_date, headers, session_id):
    import chardet
    response = download(start_date, end_date, headers, session_id)

    # most responses are ascii without decoding
    # sporadically a response will have an unknown encoding
    # the behavior cannot be reproduced consistently
    # so a solution was not found

    # installing the brotli package seems to have resolved it.
    # apparently json.loads() will decode with brotli once it is installed

    # The following commented-out code will help investigate the problem
    #print("The response is encoded with:", chardet.detect(response.content))
    #if chardet.detect(response.content)["encoding"] == None:
    #    print("The response content is:")
    #    print(brotli.decompress(response.content))

    return json.loads(response.content)

def download_to_file(start_date, end_date, data_path, headers, session_id):
    data = download_to_json(start_date, end_date, headers, session_id)
    with open(data_path + 'sleep_data.json', 'w') as fp:
        json.dump(data, fp)

def load_data(data_path):
    with open(data_path + 'sleep_data.json', 'r') as fp:
        return json.load(fp)

def converter(data, return_df=True):
    #define functions which pass through None value because
    #datetime functions don't accept value None
    def sleep_timestamp(val):
        if val == None:
            return None
        else:
            return datetime.datetime.fromtimestamp(val / 1000, pytz.utc)
    
    def sleep_timedelta(val):
        if val == None:
            return None
        else:
            return datetime.timedelta(seconds=val)

    #initialize variables
    if return_df:
        nights = pd.DataFrame(columns=["Prev_Day", "Bed_time", "Wake_Time",
                                        "Awake_Dur", "Light_Dur", "Deep_Dur", "Total_Dur",
                                        "Nap_Dur", "Window_Conf"])
        i = 0
    else:
        nights = []
    
    for d in data:
        bed_time = sleep_timestamp(d['sleepStartTimestampGMT'])
        wake_time = sleep_timestamp(d['sleepEndTimestampGMT'])
        previous_day = datetime.date(*[int(datepart) for datepart in d['calendarDate'].split('-')]) - datetime.timedelta(days=1)
        deep_duration = sleep_timedelta(d['deepSleepSeconds'])
        light_duration = sleep_timedelta(d['lightSleepSeconds'])
        total_duration = sleep_timedelta(d['sleepTimeSeconds'])
        awake_duration = sleep_timedelta(d['awakeSleepSeconds'])
        nap_duration = sleep_timedelta(d['napTimeSeconds'])
        window_confirmed = d['sleepWindowConfirmed']

        if return_df:
            nights.loc[i] = [previous_day, bed_time, wake_time, awake_duration, 
                            light_duration, deep_duration, total_duration,
                            nap_duration, window_confirmed]
            i += 1
        else:
            night = Night(bed_time, wake_time, previous_day, deep_duration, light_duration, total_duration, awake_duration)
            nights.append(night)
    
    return nights

#ENOUGH FUNCTIONS, START DOING STUFF

print("")
opts = webdriver.FirefoxOptions()
if run_browser_headless:
    opts.set_headless()
    assert opts.headless  # Operating in headless mode

#open firefox and goto Garmin's sign-in page
print("Opening Firefox")
driver = webdriver.Firefox(firefox_options=opts) #this webdriver is from seleniumwire package
driver.get(signin_url)

#wait until sign-in fields are visible
wait = WebDriverWait(driver, browser_action_timeout)
wait.until(ec.frame_to_be_available_and_switch_to_it(("id","gauth-widget-frame-gauth-widget")))
wait.until(ec.presence_of_element_located(("id","username")))

#write login info to fields, then submit
print("Signing in to connect.garmin.com")
element = driver.find_element_by_id("username")
element.send_keys(user_name)
element = driver.find_element_by_id("password")
element.send_keys(password)
element.send_keys(Keys.RETURN)

wait.until(ec.url_changes(signin_url)) #wait until landing page is requested
driver.switch_to.default_content() #get out of iframe

#get dummy webpage to obtain all request headers
print("Loading dummy page to obtain headers")
driver.get(sleep_url_base + start_date)
request = driver.wait_for_request(sleep_url_base + start_date, timeout=browser_action_timeout)

#close the Firefox browser
driver.close()
print("Headers obtained and Firefox has been closed")

#print("The request headers are:")
#print(request.headers)
#transfer request headers
headers = {
    "cookie": request.headers["Cookie"],
    "referer": sleep_url_base + start_date,
    "accept-encoding": request.headers["Accept-Encoding"],
    "accept-language": request.headers["Accept-Language"],
    "user-agent": request.headers["User-Agent"],
    #"nk": "NT",
    "accept": request.headers["Accept"],
    "authority": request.headers["Host"],
    #"x-app-ver": "4.25.3.0",
    "upgrade-insecure-requests": request.headers["Upgrade-Insecure-Requests"]
}
#print("Captured headers are:"
#print(headers)

#get the session id from the headers
re_session_id = re.compile("(?<=\$ses_id:)(\d+)")
session_id = re_session_id.search(str(request.headers)).group(0)

#Garmin will throw error if request time span exceeds 32 days
#therefore, request 32 days at a time

#define function which returns a list of tuples, 
# each tuple including no more than [period_days]
def segment_period(start, end, period_days):
    curr_start = start
    delta = period_days - datetime.timedelta(days=1)
    curr_end = start
    while curr_end < end:
        if curr_end + delta > end:
            curr_end = end
        else:
            curr_end = curr_start + delta
        yield (curr_start, curr_end)
        curr_start += delta + datetime.timedelta(days=1)

period_list = segment_period(
    datetime.datetime.strptime(start_date, "%Y-%m-%d").date(),
    datetime.datetime.strptime(end_date, "%Y-%m-%d").date(),
    datetime.timedelta(days=32))

data = [] #list of jsons, one per time period
for date_tuple in period_list:
    print("Getting data for period: [%s, %s]" % (date_tuple[0], date_tuple[1]))
    data.append(download_to_json(date_tuple[0], date_tuple[1], headers, session_id))

#combine list of jsons into one large json
data = list(chain.from_iterable(data))

#save raw Garmin json to project folder
with open(proj_path + 'sleep_data.json', 'w') as fp:
    json.dump(data, fp)

#obtain list of unique fields in json
#fields_ls = []
#for day in data:
#    row_fields_ls = [attr for attr, val in day.items()]
#    fields_ls.append(row_fields_ls)
#fields = np.unique(fields_ls)
#print("The json field names are:", fields)

#save processed data to project folder as csv
nights_df = converter(data)
nights_df.to_csv(proj_path + "sleep_dataframe.csv")