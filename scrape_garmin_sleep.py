"""
This script was written to scrape my sleep data from
Garmin's website.  It uses the selnium package to
drive Firefox and get data from a webpage for each
desired date.

This script was not finished because I discovered how
to obtain sleep data from Garmin in json format.  This
alternate method provides more detailed data than is
exposed on the website
""" 

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
import datetime
import re
import time

#input variables
user_name = "email address"
password = "password"
begin_date = datetime.date(2017, 5, 24) #y, m, d
end_date = None
signin_url = "https://connect.garmin.com/signin/"
sleep_url_base = "https://connect.garmin.com/modern/sleep/"

driver = webdriver.Firefox() #open firefox
driver.get(signin_url) #goto sign-in page

#wait until sign-in fields are visible
wait = WebDriverWait(driver, 20)
wait.until(ec.frame_to_be_available_and_switch_to_it(("id","gauth-widget-frame-gauth-widget")))
wait.until(ec.presence_of_element_located(("id","username")))

#write login info to fields, then submit
element = driver.find_element_by_id("username")
element.send_keys(user_name)
element = driver.find_element_by_id("password")
element.send_keys(password)
element.send_keys(Keys.RETURN)

wait.until(ec.url_changes(signin_url)) #wait until landing page is requested
driver.switch_to.default_content() #get out of iframe

#create list of dates to pull data from
if end_date == None:
    end_date = datetime.date.today()
numdays = (end_date - begin_date).days
date_list = [begin_date - datetime.timedelta(days=x) for x in range(4)]

#make regex expressions to test webpage content
re_no_sleep_data = re.compile("No sleep data")
re_unmeasurable = re.compile("UNMEASURABLE")
re_sleep_data = re.compile(r'Sleep Stages(.*)$')

#pull data for each date
for date in date_list:
    #get webpage for date
    print(sleep_url_base + str(date))
    driver.get(sleep_url_base + str(date))

    #wait until Sleep header DOM element appears 
    wait.until(ec.presence_of_element_located(("xpath","//h1[contains(@class, 'SleepPage')]")))

    #get sleep data block
    sleep_block = wait.until(ec.presence_of_element_located(("xpath","/html/body/div[1]/div[3]/div[2]")))

    if sleep_block.text == "":
        print("Waiting 5 more seconds")
        time.sleep(5)
        sleep_block = wait.until(ec.presence_of_element_located(("xpath","/html/body/div[1]/div[3]/div[2]")))

    print(repr(sleep_block.text))

    #sort out whether data is present on this date
    if re_no_sleep_data.search(sleep_block.text):
        print("No sleep data present")
    elif re_unmeasurable.search(sleep_block.text):
        print("Unmeasurable")
    else:
        line_tokens = sleep_block.text.split("\n")
        anchor_ind = [i for i, elem in enumerate(line_tokens) if 'Sleep Stages' in elem]
        slept_txt = line_tokens[anchor_ind[0] + 1]
        slept_txt_tokens = slept_txt.split(" ")
        
    print("------------------")

    if ec.presence_of_element_located(("css selector","#pageContainer div div.marTopMD div div div")):
        a = 1
    #val = driver.find_element_by_xpath("//div[starts-wth(@class, 'SleepGauge_donutCenter')]")

#driver.close()