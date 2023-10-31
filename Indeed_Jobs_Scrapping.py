# webscrapping using Selenium, linkedin
import re
from random import randint

from selenium import webdriver
import time
import pandas as pd
import os

from selenium.common import NoSuchElementException
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

import csv
import getpass
import logging
import os
from selenium.webdriver.support import ui

# Initialize empty lists for each filter
job_titles = []
job_companies = []
job_locations = []
dates = []
salary_list = []
job_data = []
job_descr = []
job_others = []
job_experience = []

filter_list = [
    {"Job": "Project Management", "Location": "California"},
    {"Job": "Business Analyst", "Location": "California"},
    {"Job": "Business Analyst", "Location": "New York"},
    {"Job": "Data Scientist", "Location": "New York"},
    {"Job": "Project Management", "Location": "New York"},
    {"Job": "Business Analyst", "Location": "New York"},
    # {"Job": "chief technology officer", "Location": "California"}
]

# Use this Url and change city or role accordingly
def site_launch(accept_cookie):
    service = Service(
        executable_path=r'C:\Users\dvaishn2\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe')
    options = webdriver.ChromeOptions()
    web_driver = webdriver.Chrome(service=service, options=options)
    web_driver.get("https://www.indeed.com/")
    time.sleep(5)
    web_driver.maximize_window()

    # Accept cookies if required
    if accept_cookie:
        try:
            verify_human_label = web_driver.find_element(By.XPATH, "//span[text()='Verify you are human']")
            time.sleep(randint(2, 4))
            verify_human_label.click()
        except Exception as e:
            print("Error clicking 'Verify you are human' label:", str(e))

    return web_driver

def job_search(web_driver, skill_txt, place_txt):
    # Find the skill and location input fields and populate them
    skill_element = web_driver.find_element(By.ID, "text-input-what")
    skill_element.click()
    time.sleep(1)
    skill_element.send_keys(Keys.CONTROL + "a" + Keys.DELETE);

    driver.execute_script("arguments[0].value = '';", skill_element)
    skill_element.send_keys(skill_txt)
    time.sleep(1)

    place_element = web_driver.find_element(By.ID, "text-input-where")
    place_element.click()
    time.sleep(1)
    place_element.send_keys(Keys.CONTROL + "a" + Keys.DELETE);

    driver.execute_script("arguments[0].value = '';", place_element)
    place_element.send_keys(place_txt)
    time.sleep(1)

    search_button = driver.find_element(By.CLASS_NAME, 'yosegi-InlineWhatWhere-primaryButton')
    search_button.click()
    time.sleep(1)

def jobs(job_titles, job_companies, job_locations, dates, salary_list, job_others, job_experience, job_descr):

    while True:
        time.sleep(randint(2, 4))

        job_page = driver.find_element(By.ID, "mosaic-jobResults")
        jobs = job_page.find_elements(By.CLASS_NAME, "job_seen_beacon")

        for jj in jobs:
            job_titles.append(jj.find_element(By.CLASS_NAME, "jobTitle").text)

            # Find the element with class "company_location"
            company_location_element = jj.find_element(By.CLASS_NAME, "company_location")
            # Find the company name element within the company_location element
            job_companies.append(company_location_element.find_element(By.CSS_SELECTOR, 'span[data-testid="company-name"]').text)

            # Find the location element within the company_location element
            job_locations.append(company_location_element.find_element(By.CSS_SELECTOR, 'div[data-testid="text-location"]').text)

            dates.append(jj.find_element(By.CLASS_NAME, "date").text)

            try:
                salary_list.append(jj.find_element(By.CLASS_NAME, "salary-snippet-container").text)
            except NoSuchElementException:
                try:
                    salary_list.append(jj.find_element(By.CLASS_NAME, "estimated-salary").text)
                except NoSuchElementException:
                    salary_list.append(None)

            # 10/25, Wednesday
            try:
                # Find the element with class "metadataContainer" using a CSS selector
                metadata_container = jj.find_element(By.CSS_SELECTOR, ".metadataContainer")

                # Find all child elements with class "metadata" within metadata_container
                metadata_elements = metadata_container.find_elements(By.CLASS_NAME, "metadata")

                # Extract and concatenate the text content using a list comprehension
                concatenated_values = "@".join(element.text for element in metadata_elements)

                # Append the concatenated values to the job_others list
                job_others.append(concatenated_values)
            except NoSuchElementException:
                job_others.append(None)

            try:
                # Find the job description element
                tile_ele = jj.find_element(By.CLASS_NAME, "jobTitle")
                tile_ele.click()

                time.sleep(randint(2, 4))

                job_description_element = driver.find_element(By.ID, "jobDescriptionText").text

                experience_paragraph = None
                try:
                    experience_paragraph = driver.find_element(By.XPATH, "//p[contains(text(), 'Experience:')]")
                except NoSuchElementException:
                    pass

                # Check if there's an element with "Experience:" <p> tag
                if experience_paragraph:
                    # Find the first list item (li) element within the ul
                    experience_label = driver.find_element(By.XPATH, "//p[contains(text(), 'Experience:')]")
                    first_list_item = experience_label.find_element(By.XPATH, "following-sibling::ul/li[1]").text

                    if first_list_item:
                        job_experience.append(first_list_item.strip())
                    else:
                        job_experience.append(None)
                else:
                    pattern = r'(\d+\s?(?:-\s?\d+)?\s?(?:years?|y(?:ea)?r\'?s?)\s?(?:of)?)\s?(?:experience)?'
                    # Use regular expressions to search for the experience requirement pattern
                    experience_pattern = re.compile(pattern, re.IGNORECASE)

                    # Search for the pattern within the job description text
                    experience_matches = experience_pattern.findall(job_description_element)

                    if experience_matches:
                        # Fetch the first value that matches the pattern
                        first_experience_value = experience_matches[0]
                        job_experience.append(first_experience_value)
                    else:
                        job_experience.append(None)

                # Go back to the original page
                driver.back()

            except NoSuchElementException:
                job_experience.append(None)

            # Add a random delay to avoid being blocked
            time.sleep(randint(2, 4))

        # Scroll down to trigger loading of more job listings
        actions = ActionChains(driver)
        next_button = None

        try:
            next_button = driver.find_element(By.XPATH, "//a[@data-testid='pagination-page-next']")

            while not next_button.is_displayed():
                actions.send_keys(Keys.PAGE_DOWN).perform()
                time.sleep(randint(2, 4))
        except NoSuchElementException:
            break  # No "Next" button found, exit the loop

        # Click the "Next Page" button
        try:
            time.sleep(randint(2, 4))
            next_button.click()
        except NoSuchElementException:
            break


cookie = True
driver = site_launch(accept_cookie=cookie)

# # Iterate through the filter_dict and perform job searches
# for filter_key, filter_value in filter_dict.items():
#     job_search(driver, filter_key, filter_value)
#     jobs(job_titles, job_companies, job_locations, dates, salary_list)

# Iterate through the filter_list and perform job searches
for filter_dict in filter_list:
    job_search(driver, filter_dict["Job"], filter_dict["Location"])
    # time.sleep(50000)
    jobs(job_titles, job_companies, job_locations, dates, salary_list, job_others, job_experience, job_descr)


# Create DataFrames from the lists
title_df = pd.DataFrame(job_titles, columns=["Job"])
company_df = pd.DataFrame(job_companies, columns=["Company"])
location_df = pd.DataFrame(job_locations, columns=["Location"])
date_df = pd.DataFrame(dates, columns=["Date"])
salary_df = pd.DataFrame(salary_list, columns=["Salary"])
others_df = pd.DataFrame(job_others, columns=["Other Details"])
job_experience_df = pd.DataFrame(job_experience, columns=["Experience (Years)"])
job_descr_df = pd.DataFrame(job_descr, columns=["Job Description"])

# Concatenate DataFrames horizontally
result_df = pd.concat([title_df, company_df, location_df, date_df, salary_df, others_df, job_experience_df, job_descr_df], axis=1)

# Save to CSV file
result_df.to_csv('indeed_jobs.csv', index=True)

# Quit the web driver
driver.quit()








