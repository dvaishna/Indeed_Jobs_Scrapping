# webscrapping using Selenium, Indeed
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
import concurrent.futures
from selenium.common.exceptions import StaleElementReferenceException



# Initialize empty lists for each filter
job_titles = []
job_companies = []
job_locations = []
dates = []
salary_list = []
job_data = []
job_others = []
job_experience = []


# Load the Excel file and specify the sheet name
df = pd.read_excel("input_jobs.xlsx", sheet_name="Job_Inputs", names=["Job", "Location"])

# Convert the DataFrame into a list of dictionaries
filter_list = df.to_dict(orient="records")


# Use this Url and change city or role accordingly
def site_launch(accept_cookie):
    service = Service(
        executable_path=r'C:\Users\Public\WebDriver\chromedriver-win64\chromedriver.exe')
    options = webdriver.ChromeOptions()
    web_driver = webdriver.Chrome(service=service, options=options)
    web_driver.get("https://www.indeed.com/")
    time.sleep(randint(3, 5))
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
    time.sleep(randint(1, 2))
    skill_element.send_keys(Keys.CONTROL + "a" + Keys.DELETE);

    web_driver.execute_script("arguments[0].value = '';", skill_element)
    skill_element.send_keys(skill_txt)
    time.sleep(randint(1, 2))

    place_element = web_driver.find_element(By.ID, "text-input-where")
    place_element.click()
    time.sleep(randint(1, 2))
    place_element.send_keys(Keys.CONTROL + "a" + Keys.DELETE);

    web_driver.execute_script("arguments[0].value = '';", place_element)
    place_element.send_keys(place_txt)
    time.sleep(randint(1, 2))

    search_button = web_driver.find_element(By.CLASS_NAME, 'yosegi-InlineWhatWhere-primaryButton')
    search_button.click()
    time.sleep(randint(1, 2))

# Define a function to extract the salary pattern from the job description
def extract_salary_pattern(job_description):
    # Regular expression to find salary patterns
    salary_pattern = re.compile(r'(\$[0-9,]+)(?:\s*-\s*(\$[0-9,]+))?')

    # Search for salary patterns in the text
    matches = salary_pattern.findall(job_description)

    # Extract and join the first tuple
    if matches:
        first_range = "-".join(matches[0])
    else:
        return None


# Define a function to get job type and description when clicking the job title
def get_job_details(driver, job_element, salary_list, sal_flag):
    job_exp = None
    job_type = None
    try:
        job_title = job_element.find_element(By.CLASS_NAME, "jobTitle")
        # Scroll into view of the job title element
        driver.execute_script("arguments[0].scrollIntoView(true);", job_title)
        time.sleep(randint(1, 2))

        # Click the job title
        job_title.click()
        time.sleep(randint(1, 2))


        # Find a job type element
        try:
            job_info_element = driver.find_element(By.ID, "salaryInfoAndJobType")
            try:
                job_type_element = job_info_element.find_element(By.CLASS_NAME, "css-k5flys")
                job_type = job_type_element.text.lstrip('=-') if job_type_element else "None"
            except NoSuchElementException:
                job_type = "None"
            try:
                if sal_flag == 1:
                    job_salary_element = job_info_element.find_element(By.CLASS_NAME, "css-2iqe2o")
                    job_salary = job_salary_element.text.lstrip('=-') if job_salary_element else "None"
                    salary_list.append(job_salary)
                    sal_flag = 0
            except NoSuchElementException:
                sal_flag = 1
        except NoSuchElementException:
            job_type = "None"


        # Find an experience from job description
        job_description_element = driver.find_element(By.ID, "jobDescriptionText").text

        # Fetch the salary hidden in job description
        if sal_flag == 1:
            salary_range = extract_salary_pattern(job_description_element)
            salary_list.append(salary_range)

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

            # Regular expression pattern to match the first number
            pattern = r'(?<!\w)\d+(?:\.\d+)?'

            # Search for the pattern in the text
            match = re.search(pattern, first_list_item)

            if match:
                job_exp = match.group()
            else:
                job_exp = None

        else:
            # Use regular expressions to search for the experience requirement pattern
            experience_pattern = re.compile(
                r'(\d+\+?\s?(?:years?|y(?:ea)?r\'?s?)\s?(?:of)?)\s?(?:experience)?|(\d+\s?(?:-\s?\d+)?\s?(?:years?|y(?:ea)?r\'?s?)\s?(?:of)?)\s?(?:experience)?',
                re.IGNORECASE)
            # Search for the pattern within the job description text
            experience_matches = experience_pattern.findall(job_description_element)

            if experience_matches:
                experience_value = None

                for match in experience_matches:
                    for group in match:
                        if group:
                            experience_value = group
                            break
                    if experience_value:
                        break

                # If you want to remove any non-numeric characters, you can do it like this:
                if experience_value:
                    experience_value = re.sub(r'[^\d+-]', '', experience_value)
                    experience_value = experience_value.replace("-","to")
                job_exp = experience_value
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
            try:
                job_titles.append(filtered_job)

                company_location_element = None

                for _ in range(3):  # Retry up to 3 times
                    try:
                        # Find the element with class "company_location"
                        company_location_element = jj.find_element(By.CLASS_NAME, "company_location")
                        break # If successful, break the retry loop
                    except StaleElementReferenceException:
                        continue # Retry if a stale element reference is encountered

                if company_location_element:
                    company_name_element = company_location_element.find_element(By.CSS_SELECTOR,
                                                                                 'span[data-testid="company-name"]').text
                    location_element = company_location_element.find_element(By.CSS_SELECTOR,
                                                                             'div[data-testid="text-location"]').text
                else:
                    company_name_element = "None"
                    location_element = "None"

                date_element = jj.find_element(By.CLASS_NAME, "date").text

                job_companies.append(company_name_element)
                job_locations.append(location_element)
                dates.append(date_element)

                sal_flag = 0
                try:
                    salary_list.append(jj.find_element(By.CLASS_NAME, "salary-snippet-container").text)
                except NoSuchElementException:
                    try:
                        salary_list.append(jj.find_element(By.CLASS_NAME, "estimated-salary").text)
                    except NoSuchElementException:
                        sal_flag = 1

                job_exp, job_type = get_job_details(driver, jj, salary_list, sal_flag)
                job_experience.append(job_exp)
                job_others.append(job_type)

                # Go back to the original page
                driver.back()

                # Add a random delay to avoid being blocked
                time.sleep(randint(1, 3))

            except NoSuchElementException:
                job_companies.append("None")
                job_locations.append("None")
                dates.append("None")

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


# Create a list to hold filter_dict arguments
filter_dicts = filter_list

# Define the maximum number of threads to run concurrently
max_threads = 5  # Adjust this value as needed

# Create a ThreadPoolExecutor
with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
    executor.map(scrape_jobs_for_filter, filter_dicts)

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
