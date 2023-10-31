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
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading



# Initialize empty lists for each filter
job_titles = []
job_companies = []
job_locations = []
dates = []
salary_list = []
job_data = []
job_others = []
job_experience = []


filter_list = [
    # {"Job": "Project Management", "Location": "California"},
    # {"Job": "Business Analyst", "Location": "California"},
    # {"Job": "Business Analyst", "Location": "New York"},
    #{"Job": "Data Scientist", "Location": "New York"}
     {"Job": "Project Management", "Location": "New York"},
     {"Job": "Business Analyst", "Location": "New York"}
    #{"Job": "chief technology officer", "Location": "California"}
    # {"Job": "chief operating officer", "Location": "California"},
     # {"Job": "chief technology officer", "Location": "California"}
]


# Use this Url and change city or role accordingly
def site_launch(accept_cookie):
    service = Service(
        executable_path=r'C:\Users\Public\WebDriver\chromedriver-win64\chromedriver.exe')
    options = webdriver.ChromeOptions()
    web_driver = webdriver.Chrome(service=service, options=options)
    web_driver.get("https://www.indeed.com/")
    time.sleep(5)
    web_driver.maximize_window()

    # Accept cookies if required
    if accept_cookie:
        try:
            verify_human_label = WebDriverWait(web_driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Verify you are human']")))

            verify_human_label.click()
        except Exception as e:
            print("Error clicking 'Verify you are human' label:", str(e))

    return web_driver


def job_search(web_driver: object, skill_txt: object, place_txt: object) -> object:
    # Find the skill and location input fields and populate them
    skill_element = web_driver.find_element(By.ID, "text-input-what")
    skill_element.click()
    time.sleep(1)
    skill_element.send_keys(Keys.CONTROL + "a" + Keys.DELETE);

    web_driver.execute_script("arguments[0].value = '';", skill_element)
    skill_element.send_keys(skill_txt)
    time.sleep(1)

    place_element = web_driver.find_element(By.ID, "text-input-where")
    place_element.click()
    time.sleep(1)
    place_element.send_keys(Keys.CONTROL + "a" + Keys.DELETE);

    web_driver.execute_script("arguments[0].value = '';", place_element)
    place_element.send_keys(place_txt)
    time.sleep(1)

    search_button = web_driver.find_element(By.CLASS_NAME, 'yosegi-InlineWhatWhere-primaryButton')
    search_button.click()
    time.sleep(1)


# Define a function to get job type and description when clicking the job title
def get_job_details(driver, job_element):
    job_exp = None
    job_type = None
    try:
        job_title = job_element.find_element(By.CLASS_NAME, "jobTitle")
        # Scroll into view of the job title element
        driver.execute_script("arguments[0].scrollIntoView(true);", job_title)
        time.sleep(1)

        # Click the job title
        job_title.click()
        time.sleep(randint(1, 2))


        # Find a job type element
        job_info_element = driver.find_element(By.ID, "salaryInfoAndJobType")
        job_type_element = job_info_element.find_element(By.CLASS_NAME, "css-k5flys")
        job_type = job_type_element.text.lstrip('=-')if job_type_element else "None"


        # Find an experience from job description
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
                    job_exp = first_list_item.strip()
                else:
                    job_exp = None
            else:
                # Use regular expressions to search for the experience requirement pattern
                experience_pattern = re.compile(r'(\d+\s?(?:-\s?\d+)?\s?(?:years?|y(?:ea)?r\'?s?)\s?(?:of)?)\s?(?:experience)?', re.IGNORECASE)

                # Search for the pattern within the job description text
                experience_matches = experience_pattern.findall(job_description_element)

                if experience_matches:
                    # Fetch the first value that matches the pattern
                    first_experience_value = experience_matches[0]
                    job_exp = first_experience_value
                else:
                    job_exp = None



    except NoSuchElementException:
        job_exp = None
        job_type = None

    return job_exp, job_type


def jobs(driver, filtered_job, job_titles, job_companies, job_locations, dates, salary_list, job_experience, job_others):
    while True:
        time.sleep(randint(2, 4))

        job_page = driver.find_element(By.ID, "mosaic-jobResults")
        jobs = job_page.find_elements(By.CLASS_NAME, "job_seen_beacon")

        for jj in jobs:
            # try:
            #     job_titles.append(jj.find_element(By.CSS_SELECTOR, 'h2.jobTitle span').text)
            # except NoSuchElementException:
            #     job_titles.append(None)

            job_titles.append(filtered_job) #DV

            # Find the element with class "company_location"
            company_location_element = jj.find_element(By.CLASS_NAME, "company_location")
            # Find the company name element within the company_location element
            job_companies.append(
                company_location_element.find_element(By.CSS_SELECTOR, 'span[data-testid="company-name"]').text)

            # Find the location element within the company_location element
            job_locations.append(
                company_location_element.find_element(By.CSS_SELECTOR, 'div[data-testid="text-location"]').text)

            dates.append(jj.find_element(By.CLASS_NAME, "date").text)

            try:
                salary_list.append(jj.find_element(By.CLASS_NAME, "salary-snippet-container").text)
            except NoSuchElementException:
                try:
                    salary_list.append(jj.find_element(By.CLASS_NAME, "estimated-salary").text)
                except NoSuchElementException:
                    salary_list.append(None)

            job_exp, job_type = get_job_details(driver, jj)
            job_experience.append(job_exp)
            job_others.append(job_type)
            # Go back to the original page
            driver.back()

            # Add a random delay to avoid being blocked
            time.sleep(randint(1, 3))

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


# Function for multithreading
def scrape_jobs_for_filter(filter_dict):
    driver = site_launch(accept_cookie=True)
    job_search(driver, filter_dict["Job"], filter_dict["Location"])
    jobs(driver, filter_dict["Job"], job_titles, job_companies, job_locations, dates, salary_list, job_experience, job_others)
    driver.quit()

# Create a list to hold thread objects
threads = []

# Start a thread for each filter
for filter_dict in filter_list:
    thread = threading.Thread(target=scrape_jobs_for_filter, args=(filter_dict,))
    threads.append(thread)
    thread.start()

# Wait for all threads to complete
for thread in threads:
    thread.join()

# Create DataFrames from the lists
title_df = pd.DataFrame(job_titles, columns=["Job Title"])
company_df = pd.DataFrame(job_companies, columns=["Company"])
location_df = pd.DataFrame(job_locations, columns=["Location"])
date_df = pd.DataFrame(dates, columns=["Date"])
salary_df = pd.DataFrame(salary_list, columns=["Salary"])
job_experience_df = pd.DataFrame(job_experience, columns=["Experience (Years)"])
others_df = pd.DataFrame(job_others, columns=["Job Type"])

# Concatenate DataFrames horizontally
result_df = pd.concat(
    [title_df, company_df, location_df, date_df, salary_df, job_experience_df, others_df], axis=1)


# Save to CSV file
result_df.to_csv('indeedJobs.csv', index=False)
