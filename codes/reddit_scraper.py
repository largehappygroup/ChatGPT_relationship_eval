#!/usr/bin/env python
# coding: utf-8

# In[33]:


# Ver 4.1
# Added the ability to search months until the end of the year

# Reddit Scraper Version 4.0
# The scraper can now repeatedly search until user chooses to quit
# Added the function to search for a particular month's posts
# Addressed the issue of not being able to search for December's posts
# Added attempt to resolve request error code 504 and error code 500
# Improved readibility of the debugging information
# Improved human conversational element


# In[ ]:


# Takes in the authentication info(auth, data and headers), returning the access token as string
def get_new_token(auth, data, headers):
    res = requests.post('https://www.reddit.com/api/v1/access_token', auth=auth, data = data, headers=headers)
    return res.json()['access_token']


# In[34]:


from psaw import PushshiftAPI
import praw
import requests
import time
import datetime as dt

# Introducing developer account information (AUTH)
client_id = 'YOUR_CLIENT_ID'
client_secret = 'YOUR_CLIENT_SECRET'
auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
user_agent = "Relationship Advisor"

# The account information (DATA)
data = {
'grant_type': 'password',
'username': 'YOUR_USERNAME',
'password': 'YOUR_PASSWORD',
}

# Setting up the pre-authorized headers (HEADERS)
pre_authorized_headers = {'User-Agent': user_agent}

# Get access token with AUTH, DATA, and HEADERS
token = get_new_token(auth, data, pre_authorized_headers)

# Update the authorized headers
headers = pre_authorized_headers
headers['Authorization'] = 'bearer {}'.format(token)

# Setting up a PRAW reddit instance
r = praw.Reddit(client_id=client_id,
                client_secret=client_secret,
                user_agent=client_secret)

# Setting up a Pushshift API with PRAW reddit instance to obtain the most updated data
api=PushshiftAPI(r)


# In[35]:


# Filters the submission such that deleted posts and removed posts are excluded
# Returns the list of "meaningful" urls
def filter_submission(raw_posts):
    alpha_urls = []
    for submission in raw_posts:
        if ((submission.selftext != '[removed]') and (submission.selftext != '[deleted]')):
            alpha_urls.append(submission.url)
    
    return alpha_urls


# In[36]:


# Get posts from a certain subreddit within a specified period of time
def get_posts_for_time_period(sub, after, before):
    print("Querying pushshift...")
    result = list(api.search_submissions(subreddit=sub,
                                     after=after,
                                     before=before))
    
    print("Single query completed.")
    return filter_submission(result)


# In[37]:


from datetime import datetime

# Retrieving the posts from a specific subreddit within a specified time period
# Start date should be a more recent date compared to the end date
# Start date is non-inclusive, while the end date is inclusive. (Will collect data on end date and day before start date)
# Searching backwards with regard of time
def retrieve_subs_time(start, end, sub):
    print("Starting the pushshift searching process between", datetime.fromtimestamp(end), "and", datetime.fromtimestamp(start))
    day_in_second = 86400
    
    # The more recent date
    before_timestamp = start
    
    # The more ancient date
    after_timestamp = start - day_in_second
    
    print("Now searching for posts between", datetime.fromtimestamp(after_timestamp), "and", datetime.fromtimestamp(before_timestamp))
    data = get_posts_for_time_period(sub, after_timestamp, before_timestamp)
    all_data = data
    after_timestamp -= day_in_second
    before_timestamp -= day_in_second
    
    while(before_timestamp > end):
        time.sleep(2)
        print("Now searching for posts between", datetime.fromtimestamp(after_timestamp), "and", datetime.fromtimestamp(before_timestamp))
        data = get_posts_for_time_period(sub, after_timestamp, before_timestamp)
        all_data.extend(data)
        after_timestamp -= day_in_second
        before_timestamp -= day_in_second
        
    print("Done with pushshift searching between", datetime.fromtimestamp(end), "and", datetime.fromtimestamp(start))
    return all_data


# In[38]:


import requests
import json
import sys

average_request_period = 1

# Collects the post data in json format. Takes in a list of urls and the headers information
def get_post_json(urls, headers, auth, data, pre_authorized_headers):
    
    temp_collection = []
    print("Requesting the JSON object based on urls...")
    print("There are", len(urls), "submissions to collect this time.")
    count_collected = 0
    start_at = time.time()
    time_mark = start_at
    
    for post_url in urls:
        
        # Adjust the Reddit url such that it leads to the website via oauth
        oauth_url = 'https://oauth.reddit.com' + post_url[22:]
        
        pre_request_time = time.time()
        try:
            # Send the request to get json on two-second-per-request manner
            request = requests.get(oauth_url, headers = headers)
        except requests.exceptions.RequestException as e:
            print ('Exception encountered:', e.__class__.__name__)
            if (e.__class__.__name__ == 'TimeoutError'):
                print("Timeout exception")
                print("Current url is:",  post_url)
                print("Oauth url is:", oauth_url)
                print("Retrying...")
                request = requests.get(oauth_url, headers = headers)
            if (e.__class__.__name__ == 'ConnectionError'):
                print("Connection Error exception")
                print("Current url is:",  post_url)
                print("Oauth url is:", oauth_url)
                
                # Check if it's just a link to the ads
                if ("reddit" not in post_url):
                    print("The link is likely not a valid post. Skipping...")
                    continue

                print("Retrying...")
                
                # Extra layer of safety
                try:
                    request = requests.get(oauth_url, headers = headers)
                except requests.exceptions.RequestException as e:
                    print ('Exception encountered:', e.__class__.__name__)
                    if (e.__class__.__name__ == 'TimeoutError'):
                        print("Timeout exception")
                        print("Current url is:",  post_url)
                        print("Oauth url is:", oauth_url)
                        print("Retrying...")
                        request = requests.get(oauth_url, headers = headers)
                    if (e.__class__.__name__ == 'ConnectionError'):
                        print("Connection Error exception")
                        print("Current url is:",  post_url)
                        print("Oauth url is:", oauth_url)
                        print("Retrying...")
                        request = requests.get(oauth_url, headers = headers)
        
        if (time.time() - pre_request_time > 10):
            print("The scraping process paused for", time.time() - pre_request_time, "second. Now resumed.")
        
        # Check if the request is still valid. Retrieve a new token if necessary (get status code 401).
        if (request.status_code == 401):
            print("NOTE: Error code 401/unauthorized is displayed. The access token is likely expired")
            print("Reauthorizing and retrieving new access token...")
            token = get_new_token(auth, data, pre_authorized_headers)
            headers['Authorization'] = 'bearer {}'.format(token)
            request = requests.get(oauth_url, headers = headers)
            
            if (request.status_code == 200):
                print("Request now returns status code 200. Should be good to go")
        
        # If status code is 429, wait for the ratelimit to reset
        if (request.status_code == 429):
            print("NOTE: Error code 429/too many requests is displayed. The next reset is:",
                  request.headers['x-ratelimit-reset'], 'second')
            print("Waiting for the ratelimit to reset...")
            time.sleep(request.headers['x-ratelimit-reset'])
            request = requests.get(oauth_url, headers = headers)
            
            if (request.status_code == 200):
                print("Request now returns status code 200. Should be good to go")
        
        # If status code is 504, retry the request. If the status code is still 504, skip this particular url.
        if (request.status_code == 504):
            print("NOTE: Error code 504/Gateway_Timeout is displayed.")
            print("Current post url is:", post_url)
            print("Attempting to sleep for 2 second and retry")
            time.sleep(2)
            request = requests.get(oauth_url, headers = headers)
            if (request.status_code == 504):
                print("NOTE: Request still gets error code 504. Attempting to skip this url.")
                break
            
            if (request.status_code == 200):
                print("Request now returns status code 200. Should be good to go")
                
        # If status code is 500, retry the request. If the status code is still 504, skip this particular url.
        if (request.status_code == 500):
            print("NOTE: Error code 500/Internal_Server_Error is displayed.")
            print("Current post url is:", post_url)
            print("Attempting to sleep for 2 second and retry")
            time.sleep(2)
            request = requests.get(oauth_url, headers = headers)
            if (request.status_code == 500):
                print("NOTE: Request still gets error code 500. Attempting to skip this url.")
                break
            
            if (request.status_code == 200):
                print("Request now returns status code 200. Should be good to go")
        
        # If the status code is not seen, I will let the program end to see the error.
        if (request.status_code != 200):
            print("NOTE: unprecedented status code returned. The code is:", request.status_code)
            print("Please check the developer interface of request module documentation")
            print("Current post url is:", post_url)
            print("Attempting to sleep for 2 second and retry")
            time.sleep(2)
            request = requests.get(oauth_url, headers = headers)
            if (request.status_code == 200):
                print("Request now returns status code 200. Should be good to go")


        # Check if the ratelimit is met. If so, sleep until ratelimit resets
        if(request.headers['x-ratelimit-remaining'] == 0):
            print("The ratelimit has been reached for this time period. Pause for", request.headers['x-ratelimit-reset'], "second")
            time.sleep(request.headers['x-ratelimit-reset'])
        # If the ratelimit is not met, optimize the rate of sending requests
        # If the remaining requests allowed is less than reset, sleep for 1 second for each request
        elif (request.headers['x-ratelimit-remaining'] <= request.headers['x-ratelimit-reset']):
            time.sleep(average_request_period)
        # If the remaining requests allowed is greater than reset, send request without pausing program
        
        # Store the request in json format with type 'str', then append it to the list
        post_json = request.json()
        temp_collection.append(post_json)
        
        # Debugging information
        count_collected += 1
        if ((count_collected % 100) == 0):
            set_completion_time = time.time() - time_mark
            time_mark = time.time()
            print("Complete collecting a set of 100 posts. Time taken for this set is:", set_completion_time, "second")
            print("Total number of posts collected so far:", count_collected)
            print("Number of remaining posts to collect:", len(urls) - count_collected)
            print("Progress ratio(%):", ((count_collected/len(urls)) * 100))
            print("Ratelimit conditions:")
            print("x-ratelimit-remaining:", request.headers['x-ratelimit-remaining'], "requests")
            print("x-ratelimit-used:", request.headers['x-ratelimit-used'], "requests")
            print("x-ratelimit-reset in:", request.headers['x-ratelimit-reset'], "seconds")
            print("")
        
    print("Done with the JSON object collection.")
    print("Total time spent:", time.time() - start_at, "second, which is", (time.time() - start_at) / 60, "minutes")

    return temp_collection


# In[39]:


# Create a folder for the monthly data if it does not exist
def create_folder(year, month):
    folder_name = str(year) + "_" + str(month)
    path = '/home/haonan/relationship_advisor_data/' + folder_name
    isExist = os.path.exists(path)
    if not isExist:
        os.makedirs(path)
        print("path:", path, "created")
        
    return (path + "/")


# In[40]:


import json

def write_json_file(post, directory):
    # Create json file
    data = json.dumps(post, indent = 6, sort_keys = True)
    
    path = directory + post[0]['data']['children'][0]['data']['name'] + ".json"

    with open(path, 'w') as f:
        json.dump(data, f, sort_keys = True)


# In[41]:


import os
from calendar import monthrange

# A prototype for get posts by year
def get_post_by_month(year, month):
    
    print("\nStarting the search for the posts in month", month, "in year", year, "\n")
    
    # Create a folder for the monthly data if it does not exist
    folder_path = create_folder(year, month)
    
    if (month == 12):
        start_time = int(dt.datetime(year + 1, 1, 1).timestamp())
    else:
        start_time = int(dt.datetime(year, month + 1, 1).timestamp())
        
    end_time = int(dt.datetime(year, month, 1).timestamp())
    
    post_urls = retrieve_subs_time(start_time, end_time, 'relationships')
    posts_json = get_post_json(post_urls, headers, auth, data, pre_authorized_headers)
    
    for post in posts_json:
        write_json_file(post, folder_path)


# In[42]:


def get_post_by_year(year):
    print("\nStarting the search for the posts in year", year,"\n")
    for i in range (12):
        get_post_by_month(year, i + 1)


# In[48]:


def initiation():    
    search_preference = input(("Would you like to search by year or search by month? Enter year or month:\n")).lower()
    if (search_preference == 'year'):
        target_year = int(input("Which year would you like to search?\n"))
        get_post_by_year(target_year)
    elif (search_preference == 'month'):
        target_year = int(input("Gotcha. First tell me which year?\n"))
        target_month = int(input("Understood. Please tell me which month in that year? Enter integer between 1 and 12:\n"))
        month_search_preference = input(("Got it. Would you like to start from this month and search til the end of the year? Press y for yes and n for no:\n")).lower()
        if (month_search_preference == 'y'):
            for i in range (12):
                if (i + 1 < target_month):
                    continue
                else:
                    get_post_by_month(target_year, i + 1)
        else:
            get_post_by_month(target_year, target_month)
    else:
        print(search_preference, "is not a valid input. Please try again")


# In[49]:


print("Welcome to Reddit Scraper version 4.0!\n")
user_indicator = 'y'

while (user_indicator == 'y'):
    initiation()
    user_input = input("\nCompleted one target search. Do you want to do another search? Enter y as yes and enter q as quit:\n").lower()
    while (user_input != 'y' and user_input != 'q'):
        print("Invalid input. Please try again.")
        user_input = input("\nDo you want to do another search? Enter y as yes and enter q as quit:\n").lower()
        
    user_indicator = user_input
    
print("The program is about to quit. Have a good one!")
