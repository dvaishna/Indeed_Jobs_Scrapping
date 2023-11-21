import pandas as pd
import re
from datetime import datetime, timedelta

df = pd.read_csv("merged_file.csv")
# Company Column

# Handling the removal of duplicate header rows due to merging of files

# Check if 'Job Title' exists in the 'Job Title' column
if 'Job Title' in df['Job Title'].values:
    # Identify the index of the first occurrence of the header row with "Job Title"
    header_index = df[df['Job Title'] == 'Job Title'].index[0]

    # Drop rows where the "Job Title" column has the value "Job Title"
    df = df[df['Job Title'] != 'Job Title']
else:
    # 'Job Title' is not present, no modifications needed
    pass



# Handling Company field to remove gibberish/special characters

# Delete the rows where 'Company' column contains salary values
df = df[~df['Company'].str.contains(r'\d', na=False)]

# Drop rows where the company name starts with special characters, handling NaN values
df = df[~df['Company'].str.startswith(('/n')).fillna(False)]

# Handle special characters in the company names
df['Company'] = df['Company'].str.encode('ascii', 'ignore').str.decode('ascii')


# Location Column

df.dropna(subset=['Location'], inplace=True)

# Dictionary mapping state abbreviations to full names
state_abbreviations = {
    'CA': 'California',
    'IL': 'Illinois',
    'NY': 'New York',
    'GA': 'Georgia',
    'NC': 'North Carolina',
    'VA': 'Virginia',
    'FL': 'Florida',
    'WA': 'Washington',
    'MD': 'Maryland',
    'TX': 'Texas',
    'MA': 'Massachusetts'
}

# Create a mask for rows containing state abbreviations, excluding NaN values
mask_state = df['Location'].str.contains(r'\b(' + '|'.join(state_abbreviations.keys()) + r')\b', case=False, na=False)

# Extract City, State, and Postal code from the 'Location' column
location_pattern = r'(?P<City>[\w\s]+)?,\s*(?P<State>[\w\s]+)?\s*(?P<PostalCode>\d{5})?.*'
df[['City', 'State', 'Postal Code']] = df['Location'].str.extract(location_pattern)

# Update the 'State' column dynamically for rows not containing state abbreviations
df.loc[~mask_state, 'State'] = df.loc[~mask_state, 'Location'].str.extract(r'\b([\w\s]+)\b', expand=False).str.title()

# Update the 'State' column with full names for rows containing state abbreviations
df.loc[mask_state, 'State'] = df.loc[mask_state, 'State'].str.upper().map(state_abbreviations)

# Function to handle state abbreviations in 'Location' column
def handle_state_abbreviations(location, state, city):
    if pd.notnull(location):
        # Capture the state abbreviation followed by optional space and other characters
        state_match = re.search(r'\b[A-Za-z\s]+,\s([A-Za-z]{2})\s?[^\n]*', location)
        if state_match:
            state_abbreviation = state_match.group(1).strip()
            state = state_abbreviations.get(state_abbreviation, state)
    elif pd.notnull(state):
        state_abbreviation_match = re.search(r'\b(\w{2}\s?)\b', state)
        if state_abbreviation_match:
            state_abbreviation = state_abbreviation_match.group(1).strip()
            state = state_abbreviations.get(state_abbreviation, state)
    elif pd.notnull(city):
        state_match = re.search(r'\b(\w{2}\s?)\b', city)
        if state_match:
            state_abbreviation = state_match.group(1).strip()
            state = state_abbreviations.get(state_abbreviation, state)
            city = city.replace(state_abbreviation, '').strip()

    return location, city, state

# Extract 'Job Mode' and 'City', 'State', and handle state abbreviations in 'Location'
def extract_location(location, city, state):
    job_mode = None  # Initialize variables to None

    location, city, state = handle_state_abbreviations(location, state, city)

    if pd.notnull(city):
        # Extract 'Job Mode' from 'City' if it contains job mode information
        city = re.sub(r'\bin\b', '', str(city), flags=re.IGNORECASE).strip()  # Remove 'in' from the location names
        city_lower = str(city).lower()  # Convert to lowercase
        city_cleaned = re.sub(r'[^a-zA-Z\s]', '', city_lower)  # Remove non-alphabetic characters

        if 'hybrid' in city_cleaned:
            if 'hybrid remote' in city_cleaned:
                # state = state.replace('hybrid remote', '').strip()
                city = re.sub(r'hybrid remote', '', city, flags=re.IGNORECASE).strip()
            else:
                # state = state.replace('hybrid', '').strip()
                city = re.sub(r'hybrid', '', city, flags=re.IGNORECASE).strip()
            job_mode = 'Hybrid'
        elif 'remote' in city_cleaned:
            job_mode = 'Remote'
            # state = state.replace('remote', '').strip()
            city = re.sub(r'remote', '', city, flags=re.IGNORECASE).strip()
        elif 'inperson' in city_cleaned or 'in person' in city_cleaned:
            job_mode = 'In-person'
            city = city.strip()


    if pd.notnull(state):
        state = re.sub(r'\bin\b', '', str(state),
                                flags=re.IGNORECASE).strip()  # Remove 'in' from the location names
        state_lower = str(state).lower()  # Convert to lowercase
        state_cleaned = re.sub(r'[^a-zA-Z\s]', '', state_lower)  # Remove non-alphabetic characters


        if 'united states' in state_cleaned:
            job_mode = 'Remote'
            state = ''
        elif 'financial district area' in state_cleaned or 'macdill afb area' in state_cleaned:
            state = ''
        elif 'washington state' in state_cleaned:
            state = state_cleaned.replace('washington state', 'Washington').strip()
        elif 'new york state' in state_cleaned:
            state = state_cleaned.replace('new york state', 'New York').strip()
        elif 'northwest area' in state_cleaned:
            state = ''
        elif 'north austin area' in state_cleaned:
            state = ''
        elif 'temporarily remote  virginia' in state_cleaned:
            state = ''
        elif 'none' in state_cleaned:
            state = ''

        if 'hybrid' in state_cleaned:
            if 'hybrid remote' in state_cleaned:
                state = re.sub(r'hybrid remote', '', state, flags=re.IGNORECASE).strip()
            else:
                state = re.sub(r'hybrid', '', state, flags=re.IGNORECASE).strip()
            job_mode = 'Hybrid'
        elif 'remote' in state_cleaned:
            job_mode = 'Remote'
            state = re.sub(r'remote', '', state, flags=re.IGNORECASE).strip()
        elif 'inperson' in state_cleaned or 'in person' in state_lower:
            job_mode = 'In-person'
            state = state.strip()

    if job_mode == None:
        # Extract 'Job Mode' from 'City' if it contains job mode information
        location = re.sub(r'\bin\b', '', str(location), flags=re.IGNORECASE).strip()  # Remove 'in' from the location names
        location_lower = str(location).lower()  # Convert to lowercase
        location_cleaned = re.sub(r'[^a-zA-Z\s]', '', location_lower)  # Remove non-alphabetic characters

        if 'hybrid' in location_cleaned:
            job_mode = 'Hybrid'
        elif 'remote' in location_cleaned:
            job_mode = 'Remote'
        elif 'inperson' in location_cleaned or 'in person' in location_cleaned:
            job_mode = 'In-Person'
        else:
            job_mode = 'In-Person'

    if state == '':
        state = 'Not Available'

    return job_mode, city, state  # Return the modified city value

# Apply the extract_job_mode function to 'Location', 'City', and 'State' columns to create 'Job Mode' column
df['Job Mode'], df['City'], df['State'] = zip(
    *df.apply(lambda row: extract_location(row['Location'], row['City'], row['State']), axis=1))

# Remove job which is not in NA
df.drop(df[df['City'] == 'Pune'].index, inplace=True)

# Replace None values with Not Available
df['City'].replace(['', None], 'Not Available', inplace=True)


#Salary Column
salary_patterns = [
    r'\$\s?(\d+(?:,\d{3})*(?:\.\d{1,2})?)\s?a\s?year',  # $xxx,xxx a year
    r'^\$(\d+(\.\d{2})?) - \$(\d+(\.\d{2})?) an hour$',  # minimum and maximum for hour
    r'\$([\d.,]+)\s*an hour',  # hour only data
    r'\$\s?(\d+(?:,\d{3})*(?:\.\d{1,2})?)\s?a\s?week',  # $xxx,xxx a week
    r'\$\s?(\d+(?:,\d{3})*(?:\.\d{1,2})?)\s?a\s?day',  # $xxx,xxx a day
    r'^\$(\d+\.\d{2}) - \$(\d+\.\d{2}) a day$',  # for decimal day
    r'\$\s?([\d,]+)\s?-\s?\$\s?([\d,]+)\s?a\s?month',  # $xx,xxx - $xx,xxx a month
    r'\$\s?(\d+(?:,\d{3})*(?:\.\d{1,2})?)\s?a\s?month',  # $xxx,xxx a month
    r'\$\s?(\d{1,3},?\d{3})\s?-?\s?\$\s?(\d{1,3},?\d{3})\s?a\s?year', # $xx,xxx - $xx,xxx a year
    r'Estimated \$([\d.]+)K?\s?-?\s?\$([\d.]+)K?'  # Estimated $xx.xK - $xxK a year
]
def extract_salary(row):
    salary_string = str(row['Salary'])
    min_salary = None
    max_salary = None

    for pattern in salary_patterns:
        match = re.search(pattern, salary_string, re.IGNORECASE)
        if match:
            #For Hour Salary
            if 'an hour' in salary_string.lower():
                if re.match(r'^\$(\d+(\.\d{2})?) - \$(\d+(\.\d{2})?) an hour$', salary_string):
                    hour_match = re.search(r'^\$(\d+(\.\d{2})?) - \$(\d+(\.\d{2})?) an hour$', salary_string)
                    if hour_match:
                        min_salary_str = hour_match.group(1).replace(',', '') if hour_match.group(1) else None
                        max_salary_str = hour_match.group(3).replace(',', '') if hour_match.group(3) else None

                        if min_salary_str is not None:
                            min_salary = float(min_salary_str) * 40 * 52
                        if max_salary_str is not None:
                            max_salary = float(max_salary_str) * 40 * 52

                elif 'an hour' in salary_string.lower():
                    if 'from' in salary_string.lower():
                        min_salary_str = match.group(1).replace(',', '')
                        min_salary = float(min_salary_str) * 40 * 52
                        max_salary = None

                    elif 'up to' in salary_string.lower():
                        max_salary_str = match.group(1).replace(',', '')
                        max_salary = float(max_salary_str) * 40 * 52
                        min_salary = None
                    else:
                        max_salary_str = match.group(1).replace(',', '')
                        max_salary = min_salary = float(max_salary_str) * 40 * 52
                elif len(match.groups()) == 1:
                    # Pattern: $xx,xxx an hour
                    max_hourly_rate = float(match.group(1).replace(',', ''))
                    max_salary = float(max_salary_str) * 40 * 52
            # Year Salary
            if re.match(r'Estimated \$([\d.]+)K?\s?-?\s?\$([\d.]+)K?', salary_string):
                # Handle Estimated $xx.xK - $xxK a year
                min_salary = round(float(match.group(1)) * 1000)
                max_salary = round(float(match.group(2)) * 1000)

            elif re.match(r'\$\s?(\d{1,3},?\d{3})\s?-?\s?\$\s?(\d{1,3},?\d{3})\s?a\s?year', salary_string):
                # Handle yearly salary ranges
                year_match = re.search(r'\$\s?(\d{1,3},?\d{3})\s?-?\s?\$\s?(\d{1,3},?\d{3})\s?a\s?year', salary_string)
                min_salary_str = year_match.group(1).replace(',', '')
                max_salary_str = year_match.group(2).replace(',', '')
                min_salary = int(float(min_salary_str))
                max_salary = int(float(max_salary_str))
            elif 'a year' in salary_string.lower():
                if 'from' in salary_string.lower():
                    min_salary_str = match.group(1).replace(',', '')
                    min_salary = int(float(min_salary_str))
                    max_salary = None

                elif 'up to' in salary_string.lower():
                    max_salary_str = match.group(1).replace(',', '')
                    max_salary = int(float(max_salary_str))
                    min_salary = None
                else:
                    max_salary_str = match.group(1).replace(',', '')
                    max_salary = min_salary = int(float(max_salary_str))
            #For Month Salary
            elif 'a month' in salary_string.lower():
                if re.match(r'\$\s?([\d,]+)\s?-\s?\$\s?([\d,]+)\s?a\s?month', salary_string):
                    # Handle monthly salary ranges
                    month_match = re.search(r'\$\s?([\d,]+)\s?-\s?\$\s?([\d,]+)\s?a\s?month',salary_string)
                    min_salary_str = month_match.group(1).replace(',', '')
                    max_salary_str = month_match.group(2).replace(',', '')
                    min_salary = int(float(min_salary_str) * 12)
                    max_salary = int(float(max_salary_str) * 12)
                elif 'from' in salary_string.lower():
                    min_salary_str = match.group(1).replace(',', '')
                    min_salary = int(float(min_salary_str) * 12)
                    max_salary = None
                elif 'up to' in salary_string.lower():
                    max_salary_str = match.group(1).replace(',', '')
                    max_salary = int(float(max_salary_str) * 12)
                    min_salary = None
                else:
                    max_salary_str = match.group(1).replace(',', '')
                    max_salary = min_salary = int(float(max_salary_str) * 12)
            # For Week Salary
            elif 'a week' in salary_string.lower():
                if re.match(r'\$\s?([\d,]+)\s?-\s?\$\s?([\d,]+)\s?a\s?week', salary_string):
                    # Handle weekly salary ranges
                    Week_match = re.search(r'\$\s?([\d,]+)\s?-\s?\$\s?([\d,]+)\s?a\s?week', salary_string)
                    min_salary_str = Week_match.group(1).replace(',', '')
                    max_salary_str = Week_match.group(2).replace(',', '')
                    min_salary = int(float(min_salary_str) * 52)
                    max_salary = int(float(max_salary_str) * 52)
                elif 'from' in salary_string.lower():
                    min_salary_str = match.group(1).replace(',', '')
                    min_salary = int(float(min_salary_str) * 52)
                    max_salary = None
                elif 'up to' in salary_string.lower():
                    max_salary_str = match.group(1).replace(',', '')
                    max_salary = int(float(max_salary_str) * 52)
                    min_salary = None
                else:
                    max_salary_str = match.group(1).replace(',', '')
                    max_salary = min_salary = round(float(max_salary_str) * 52)
            # For Day Salary
            if re.match(r'^\$(\d+\.\d{2}) - \$(\d+\.\d{2}) a day$', salary_string):
                day_match = re.search(r'^\$(\d+\.\d{2}) - \$(\d+\.\d{2}) a day$', salary_string)
                min_salary_str = day_match.group(1).replace(',', '')
                max_salary_str = day_match.group(2).replace(',', '')
                min_salary = int(float(min_salary_str) * 20 * 12)
                max_salary = int(float(max_salary_str) * 20 * 12)
            elif 'a day' in salary_string.lower():
                if re.match(r'\$\s?([\d,]+)\s?-\s?\$\s?([\d,]+)\s?a\s?day', salary_string):
                    day_a_match = re.search(r'\$\s?([\d,]+)\s?-\s?\$\s?([\d,]+)\s?a\s?day', salary_string)
                    # Handle day salary ranges
                    min_salary_str = day_a_match.group(1).replace(',', '')
                    max_salary_str = day_a_match.group(2).replace(',', '')
                    min_salary = int(float(min_salary_str) * 20 * 12)
                    max_salary = int(float(max_salary_str) * 20 * 12)

                elif 'from' in salary_string.lower():
                    min_salary_str = match.group(1).replace(',', '')
                    min_salary = int(float(min_salary_str) * 20 * 12)
                    max_salary = None
                elif 'up to' in salary_string.lower():
                    max_salary_str = match.group(1).replace(',', '')
                    max_salary = int(float(max_salary_str) * 20 * 12)
                    min_salary = None
                else:
                    max_salary_str = match.group(1).replace(',', '')
                    max_salary = min_salary = round(float(max_salary_str) * 20 * 12)
    return min_salary, max_salary

# Apply the function to 'Salary' column and create new columns
df[['Minimum Salary', 'Maximum Salary']] = df.apply(extract_salary, axis=1, result_type='expand')

# Group by 'Location' and 'Job Title' columns and fill NaN values with the mean of each group
df['Minimum Salary'] = df['Minimum Salary'].fillna(df.groupby(['State', 'Job Title'])['Minimum Salary'].transform('mean'))
df['Maximum Salary'] = df['Maximum Salary'].fillna(df.groupby(['State', 'Job Title'])['Maximum Salary'].transform('mean'))

df.dropna(subset=['Minimum Salary'], inplace=True)
df.dropna(subset=['Maximum Salary'], inplace=True)

# Round off the float values to integers
df['Minimum Salary'] = df['Minimum Salary'].round().astype(int)
df['Maximum Salary'] = df['Maximum Salary'].round().astype(int)

# Date Column

# Define your regex patterns
regex_patterns = [
    r'Employer\nActive (\d+) day(s)? ago',
    r'Posted\nPosted (\d+) day(s)? ago',
    r'Employer\nActive (\d+) days? ago',
    r'Posted\nPosted (\d+) days? ago',
    r'Employer\nActive (\d+)\+\s*day(s)? ago',
    r'Posted\nPosted (\d+)\+\s*day(s)? ago',
    r'Hiring ongoing',
    r'Today',
    r'Just posted',
]

def calculate_date(match, base_date):
    days_ago = int(match.group(1))
    return (base_date - timedelta(days=days_ago)).strftime('%m-%d-%Y')

def extract_dates(text):
    today = datetime.now()
    dynamic_days = None

    if isinstance(text, str):
        for pattern in regex_patterns:
            match = re.search(pattern, text)
            if match:
                if pattern == "Hiring ongoing" or pattern == "Today" or pattern == "Just posted":
                    return today.strftime('%m-%d-%Y'), None
                else:
                    dynamic_days = int(match.group(1))
                    if pattern.startswith("Employer\\nActive"):
                        return calculate_date(match, today), None
                    elif pattern.startswith("Posted\\nPosted"):
                        return None, calculate_date(match, today)

        try:
            if dynamic_days:
                return (today - timedelta(days=dynamic_days)).strftime('%m-%d-%Y'), None
            else:
                return None, None
        except Exception as e:
            return None, None
    else:
        return None, None


# Apply the function to create new columns "Active_date" and "Posted_date"
df[['Employer_Active_date', 'Job_Posted_date']] = df['Date'].apply(extract_dates).apply(pd.Series)

# Job Type Column

# Create labels for the job categories
df['Job category'] = df['Job Type'].fillna('Not Available')

# Define rules for categorization

# Define rules for categorization
categorization_rules = {
    'Freelance': [
        r'Full-time, Contract, Freelance',
        r'Contract, Freelance',
        r'Full-time, Freelance'
    ],
    'Contract': [
        r'Full-time, Contract',
        r'full-time, temporary, contract',
        r'Contract, Temp-to-hire',
        r'Temporary, Full-time',
        r'Temporary, contract',
        r'Temporary, Full-time, Contract',
        r'Full-time, Contract, Internship|Contract, Internship',
        r'Contract, Non-tenure(, Full-time)?'
    ],
    'Internship': [
        r'Full-time, internship(, Seasonal,)?',
        r'Internship, Non-tenure',
        r'Part-time, Internship',
        r'Part-time, Full-time, Internship',
        r'Temporary, Part-time, Internship',
        r'Seasonal, Internship',
        r'Full-time, Contract, Internship|Contract, Internship',
        r'Part-time, Contract, Internship',
        r'Temporary, Part-time, Full-time, Contract, Internship',
        r'Part-time, Seasonal, Full-time, Internship',
        r'Temporary, Internship',
        r'Permanent, Part-time, Internship',
        r'Permanent, Internship'
    ],
    'Apprenticeship': [
        r'Full-time, apprenticeship',
        r'Part-time, Apprenticeship'
    ],
    'Non-tenure': [
        r'Full-time, Non-tenure',
        r'Contract, Non-tenure(, Full-time)?',
        r'Full-time, Tenured, Tenure track, Non-tenure'
    ],
    'Tenure track': [
        r'Full-time, Tenured, Tenure track|Full-time, Tenure track|Tenured, Tenure track',
        r'Full-time, Tenure track, Non-tenure'
    ],
    'Full-time': [
        r'Full-time, Temporary|Temporary, Full-time',
        r'Full-time, part-time, Contract|Full-time, Part-time',
        r'Full-time, Tenured, Tenure track|Full-time, Tenure track|Tenured, Tenure track',
        r'Temporary, Full-time',
        r'Temporary, Temp-to-hire, Full-time',
        r'Temporary, Temp-to-hire, Full-time',
        r'Temporary, Part-time, Seasonal',
        r'Full-time, Seasonal',
        r'Permanent, Full-time, Contract',
        r'Permanent, Full-time',
        r'Full-time, Contract',
        r'Temp-to-hire, Full-time'
    ],
    'Part-time': [
        r'Part-time, Full-time, Internship',
        r'Part-time, Internship',
        r'Part-time, Full-time|Part-time, Contract',
        r'Part-time, Contract, Internship',
        r'Part-time, Full-time, Freelance'
    ],
    'Temporary': [
        r'Temporary, Full-time',
        r'Temporary, Per diem, Freelance',
        r'Temporary, Part-time',
        r'Temporary, Part-time, Temp-to-hire',
        r'Temporary, Freelance',
        r'Temporary, Temp-to-hire',
        r'Temporary, Permanent',
        r'Temporary, Permanent, Contract',
        r'Temp-to-hire, Contract'
    ],

    'Seasonal': [
        r'part-time, Seasonal, Full-time',
        r'Seasonal, Full-time',
        r'Temporary, Part-time, Seasonal'
    ],

    'PRN': [
        r'Full-time, PRN'
    ],
    'Travel healthcare': [
        r'Travel healthcare, Full-time'
    ],
    'Permanent': [
        r'Permanent, Full-time|Full-time, Permanent',
        r'Permanent, Contract',

    ],
    'Tenure': [
        r'Tenure track, Non-tenure'
    ],
    'Not available': [
        r'None'
    ]
}

compiled_patterns = {category: [re.compile(pattern, re.IGNORECASE) for pattern in patterns] for category, patterns in categorization_rules.items()}

# Function to apply categorization
def apply_categorization(text):
    for category, patterns in compiled_patterns.items():
        for pattern in patterns:
            if pattern.search(text):
                return category
    return text  # Return original text if no match is found

# Apply categorization to 'Job category' column
df['Job category'] = df['Job category'].apply(apply_categorization)

# Handle blank or missing values
df['Job category'] = df['Job category'].str.strip().replace(r'^\s*$', 'Not Available', regex=True)


# Experience Column:
# Function to handle various types in 'Experience (Years)' column
def preprocess_experience(experience):
    if pd.notna(experience):
        if isinstance(experience, (int, float)):
            return str(int(experience))  # Convert numeric values to strings
        elif isinstance(experience, str):
            return experience
    return 'Not Available'  # Handle other data types or missing data

# inserting preprocessing function to 'Experience (Years)' column
df['Experience (Years)'] = df['Experience (Years)'].apply(preprocess_experience)

# Define the modified extract_numeric_experience function
def extract_numeric_experience(experience):
    if experience == 'N/A':
        return 'Not Available'

    # Define a comprehensive regular expression pattern to match various experience formats
    pattern = r'(\d+(?:to\d+)?)\s*(?:year|yr|yrs)?'

    match = re.search(pattern, experience)
    if match:
        numeric_part = match.group(1)
        if 'to' in numeric_part:
            numeric_part = numeric_part.split('to')[-1]  # Get the last value in the range

        if numeric_part.isdigit() and int(numeric_part) <= 30:
            return numeric_part

    return 'Not Available'  # If no valid numeric experience is found, return 'N/A'

# Apply the modified function to 'Experience (Years)' column
df['Experience_years'] = df['Experience (Years)'].apply(extract_numeric_experience)

# Display the entire DataFrame
print(df)

selected_columns = ['Job Title', 'Company', 'City', 'State',
					'Postal Code', 'Job Mode', 'Minimum Salary', 'Maximum Salary',
					'Employer_Active_date' ,'Job_Posted_date', 'Job category',
					'Experience_years']  # Removing the duplicate columns and keeping required


#Save the result to a CSV file
df[selected_columns].to_csv('cleaned_file.csv', index=False)

print(df)
