import os
import re
import openai
import json
from sklearn.metrics import cohen_kappa_score
import numpy as np
import random
import time
from scipy.stats import kendalltau, spearmanr
from scipy.stats import ttest_ind
openai.api_key = "YOUR_OPENAI_API_KEY"


temperature_value = 1
cnt_posts = 0
cnt_errors = 0
errored_posts = {}
cumulated_cv = 0
cumulated_controversial_comments = 0
extreme_posts = []

def extract_additional_info(response):
    pattern = r'Ranking:\s*((?:\d+,\s*)+\d+)' + \
              r'(?:\\n|\n|\;)\s*Age:\s*([\w-]+)' + \
              r'(?:\\n|\n|\;)\s*Gender:\s*(\w+)' + \
              r'(?:\\n|\n|\;)\s*Ethnicity:\s*(\w+)' + \
              r'(?:\\n|\n|\;)\s*Nationality:\s*(\w+)' + \
              r'(?:\\n|\n|\;)\s*Category:\s*(\w+)'
    match = re.match(pattern, response)
    if match:
        return match.groups()
    else:
        return None

def unresolved_store_info(post, store_path, response):
    unresolved_path = store_path + "unresolved/"
    # Create the directory if it does not exist
    os.makedirs(unresolved_path, exist_ok=True)
    with open(unresolved_path + post, 'w') as f:
        json.dump({'response': response}, f)

def prompt_editing(content_list, score_info_list, usr_prompt, num_comments):
    cv = 0
    score_list = []
    selected_comment_indices = []
    
    try:
        if num_comments in [2, 4, 8, 16]:
            for i in range(1, num_comments + 1):
                usr_prompt += f" [{i}]"
                usr_prompt += content_list[i]
                selected_comment_indices.append(i)
                score_list.append(score_info_list[i][0])
                
            # cv is abbreviation of "coefficient of variance"
            if len(score_list) > 1:
                cv = np.std(score_list) / np.mean(score_list)
        
        else:
            print("Unexpected number of comments. Doing uneven distribution")
            for i in range(1, num_comments+1):
                usr_prompt += f" [{i}]"
                selected_comment_indices.append(i)
                usr_prompt += content_list[i]
            
            if len(score_list) > 1:
                cv = np.std(score_list) / np.mean(score_list)

        return usr_prompt, cv, selected_comment_indices

    except Exception as e:
        print("Error occurred when editing the prompt:", e)


def ranking_prompt(content_list, score_info_list, temperature_value, num_comments):

    usr_prompt = "I will give you a description of a relationship problem and " + str(num_comments) + " advices on a the problem. Can you help me rank the reliability of the advices? You do not need to provide the reasonings for your ranking. Show me the results in the form of number series separated by comma, for instance, \"3,1,2,5,4\" if option 3 is the best comment and option 4 is the worst. Make sure that all" + str(num_comments) + "numbers are present in your response. Meanwhile, make some demographics prediction including the age, gender, ethnicity and nationality of the original poster of the description (you MUST give me a guess). Also, Try to categorize the problem in as few words as possible and try your best to reuse categories that you have used before. Give me a response in this format without newlines: Ranking: ...; Age: ...; Gender: ...; Ethnicity: ...; Nationality: ...;  Category: .... The description of the problem is: "
    usr_prompt += content_list[0]  # Append the description
    usr_prompt += "  [END OF DESCRIPTION]  The suggestions are: "
    usr_prompt, cv, selected_comment_indices = prompt_editing(content_list, score_info_list, usr_prompt, num_comments)

    try:
        completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature = temperature_value,
        messages=[
            {"role": "user", "content": usr_prompt}
        ]
        )
        response = completion.choices[0].message["content"]
        if "error" in response:
            cnt_errors += 1
            if "Rate limit" in response["error"].get("message", ""):
                print("Rate-limit encountered. Sleeping for 15 seconds...")
                time.sleep(15)

                completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                temperature = temperature_value,
                messages=[
                    {"role": "user", "content": usr_prompt}
                ]
                )
                response = completion.choices[0].message["content"]

        return response, cv, selected_comment_indices
    
    except Exception as e:
        print("Exception encountered:", e)
        print("The post is not examined")


def store_info(store_path, score):
    with open(store_path, "w") as outfile:
            json.dump(score, outfile)

def path_selection():
    print("Selecting the posts to extract information from...")
    
    home_path = "/home/haonan/after_2022_posts/aggregated_posts/"
    store_path = input("Enter the folder to store the output. No need for trailing slash:\n")

    if not store_path.startswith("/"):
        store_path = "/home/haonan/" + store_path + "/"

    if os.path.exists(store_path):
        print("Warning: The specified folder already exists.")
        proceed = input("Do you want to continue and store the data in the existing folder? Type 'yes' to proceed or 'no' to specify a new folder:\n")
        if proceed.lower() != "yes":
            store_path = input("Enter a new path to store the output. No need for trailing slash:\n")

    if not os.path.exists(store_path):
        os.makedirs(store_path)

    return home_path, store_path

def select_posts(post_names, num_posts):
    if num_posts == -1 or num_posts >= len(post_names):
        print("Examining all posts...")
        return post_names

    print("Examining", num_posts, "posts...")
    selection_method = input("Do you want to pick posts by their relative order or randomly? Type 'order' for the former, 'random' for the latter:\n")

    if selection_method.lower() == 'random':
        return random.sample(post_names, num_posts)
    else:
        return post_names[:num_posts]

def individual_store_info(post, content_list, individual_cv, store_path, selected_comment_indices, gpt_ranking, 
                          age, gender, ethnicity, nationality, category):
    individual_dict = {'cv': individual_cv, 'gpt_ranking': gpt_ranking, 
                       'age': age, 'gender': gender, 'ethnicity': ethnicity, 
                       'nationality': nationality, 'category': category, 'description': content_list[0]}
    for index in selected_comment_indices:
        key_name = "comment " + str(index)
        individual_dict[key_name] = content_list[index]
    with open(store_path + post, "w") as outfile:
        json.dump(individual_dict, outfile)

def total_store_info(store_path):
    global cnt_posts, cnt_errors, errored_posts
    global cumulated_cv, cumulated_controversial_comments, extreme_posts
    total_info = {}
    # store the cumulative info
    total_info = {'cnt_posts': cnt_posts, 'cnt_errors': cnt_errors, 'extreme_posts': extreme_posts, 'errored_posts': errored_posts}
    with open(store_path + "total_info.json", 'w') as f:
        json.dump(total_info, f)


def info_extraction(post, folder_path, temperature_value, num_comments, store_path):
    global cnt_posts, cnt_errors, errored_posts
    global cumulated_cv, cumulated_controversial_comments, extreme_posts

    post_path = folder_path + post
    content_list = []
    score_info_list = []  # 0th is score, 1th is controversiality, 2nd is ups, 3rd is downs
    human_ranking = []

    gpt_ranking = []  # Initialize the gpt_ranking variable with an empty list
    age, gender, ethnicity, nationality, category = "", "", "", "", ""  # Initialize these variables as well

    for i in range(1, num_comments + 1):
        human_ranking.append(int(i))

    try:
        sample = open(post_path)
        json_str = json.load(sample)

        for item in json_str:
            content_list.append(item)
            score_info_list.append(json_str[item])

        gpt_response, individual_cv, selected_comment_indices = ranking_prompt(content_list, score_info_list,
                                                                              temperature_value, num_comments)

        # Extract additional info from GPT's response
        additional_info = extract_additional_info(gpt_response)
        if additional_info is None:  # If unable to parse the response
            unresolved_store_info(post, store_path, gpt_response)
        else:
            gpt_ranking, age, gender, ethnicity, nationality, category = additional_info
            # Correct way to split gpt_ranking and convert to integers
            gpt_ranking = [int(rank) for rank in gpt_ranking.split(",")]

            # Check if gpt_ranking is "extreme"
            if len(gpt_ranking) > 1 and gpt_ranking[0] == len(gpt_ranking) and gpt_ranking[-1] == 1: 
                extreme_posts.append(post)

            individual_store_info(post, content_list, individual_cv, store_path, selected_comment_indices, gpt_ranking,
                                age, gender, ethnicity, nationality, category)

        cnt_posts += 1
        cumulated_cv += individual_cv

    except Exception as e:
        print("Exception occurred:", e, "during the examination for post", post)
        cnt_errors += 1
        errored_posts[post] = str(e)  # Store only the exception message string, not the whole exception object


home_path, store_path = path_selection()
post_names = os.listdir(home_path)
num_comments = int(input("How many comments would you like the GPT to rank for each prompt? Provide an integer between 2 and 16: \n"))
target_num_posts = int(input("How many posts do you want to investigate this time? Input '-1' for all posts. \n"))

selected_posts = select_posts(post_names, target_num_posts)
for post in selected_posts:
    info_extraction(post, home_path, temperature_value, num_comments, store_path)

total_store_info(store_path)
