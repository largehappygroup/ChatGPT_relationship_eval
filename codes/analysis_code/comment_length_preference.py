import os
import json
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
from collections import Counter

cnt_posts = 0
cnt_strict_preference = 0
cnt_loose_preference = 0

cumulated_first_two_longer = 0
cumulated_preference_length_diff = 0
cumulated_no_pref_length_diff = 0

# Download stopwords from nltk
nltk.download('stopwords')
nltk.download('punkt')

# Get English stopwords
stop_words = set(stopwords.words('english'))

def lexical_diversity(text):
    # Tokenize the text into individual words
    words = word_tokenize(text)

    # Remove stopwords and punctuation
    words = [word for word in words if word not in stop_words and word.isalpha()]

    # If the list of words is empty, return 0 to avoid ZeroDivisionError
    if not words:
        return 0

    # Get the frequency of each word
    word_freq = Counter(words)

    # The type-token ratio (TTR) is the number of unique words (types) divided by the total number of words (tokens)
    return len(word_freq) / len(words)


def post_analysis(post, home_path, num_comments):
    global cnt_posts, cnt_strict_preference, cnt_loose_preference
    global cumulated_first_two_longer, cumulated_preference_length_diff, cumulated_no_pref_length_diff

    post_path = home_path + post
    sample = open(post_path)
    json_str = json.load(sample)

    gpt_ranking = json_str['gpt_ranking']
    choices = [json_str['comment ' + str(gpt_ranking[i])] for i in range(num_comments)]
    
    # Check if all comments are in strictly increasing order
    if all(len(choices[i]) > len(choices[i+1]) for i in range(num_comments-1)):
        cnt_strict_preference += 1
    
    if len(choices[0]) > len(choices[-1]):  # compare first and last
        cnt_loose_preference += 1

    for i, choice in enumerate(choices):
        globals()[f'cumulated_{i+1}_choice_length'] += len(choice)
        globals()[f'cumulated_{i+1}_choice_diversity'] += lexical_diversity(choice)

    if num_comments >= 4:  # the following logic is valid only for 4 or more comments
        first_last_length_diff = len(choices[0]) - len(choices[-1])

        if len(choices[0]) + len(choices[1]) > len(choices[2]) + len(choices[3]):
            cumulated_first_two_longer += 1

        if len(choices[0]) > len(choices[-1]):
            cumulated_preference_length_diff += first_last_length_diff
        else:
            cumulated_no_pref_length_diff += first_last_length_diff

    cnt_posts += 1

relative_path = input("Enter the name of the folder storing the information: ")
num_comments = int(input("Enter the number of comments: "))

for i in range(1, num_comments + 1):
    globals()[f'cumulated_{i}_choice_length'] = 0
    globals()[f'cumulated_{i}_choice_diversity'] = 0

home_path = "/home/haonan/" + relative_path + "/"
post_names = os.listdir(home_path)

for post in post_names:
    try:
        post_analysis(post, home_path, num_comments)
    except Exception as e:
        print(f"{e} encountered for {post}")

print(f"Total of {cnt_posts} posts examined")
print(f"Total of {cnt_posts} posts examined")
for i in range(num_comments):
    cumulated_choice_length = globals()[f'cumulated_{i+1}_choice_length']
    cumulated_choice_diversity = globals()[f'cumulated_{i+1}_choice_diversity']
    print(f"Average length of choice {i+1} is {cumulated_choice_length / cnt_posts}")
    print(f"Average lexical diversity of choice {i+1} is {cumulated_choice_diversity / cnt_posts}")
print(f"Found {cnt_strict_preference} 'strict' preferences and {cnt_loose_preference} 'loose' preferences.")
print(f"When ChatGPT prefers the longer comment, the average length difference between first choice and fourth choice is {float(cumulated_preference_length_diff / cnt_posts)}")
print(f"When ChatGPT does NOT prefer the longer comment, the average length difference between first choice and fourth choice is {float(cumulated_no_pref_length_diff / cnt_posts)}")

def store_info(file_path, num_comments):
    with open(file_path, 'w') as f:
        f.write(f"Total of {cnt_posts} posts examined\n")
        for i in range(num_comments):
            cumulated_choice_length = globals()[f'cumulated_{i+1}_choice_length']
            cumulated_choice_diversity = globals()[f'cumulated_{i+1}_choice_diversity']
            f.write(f"Average length of choice {i+1} is {cumulated_choice_length / cnt_posts}\n")
            f.write(f"Average lexical diversity of choice {i+1} is {cumulated_choice_diversity / cnt_posts}\n")
        
        f.write(f"Found {cnt_strict_preference} 'strict' preferences and {cnt_loose_preference} 'loose' preferences.\n")
        
        if num_comments >= 4:
            f.write(f"Number of posts where the combined length of the first two choices is longer than the combined length of the last two: {cumulated_first_two_longer}\n")
            f.write(f"When ChatGPT prefers the longer comment, the average length difference between the first choice and last choice is {float(cumulated_preference_length_diff / cnt_posts)}\n")
            f.write(f"When ChatGPT does NOT prefer the longer comment, the average length difference between the first choice and last choice is {float(cumulated_no_pref_length_diff / cnt_posts)}\n")

# Call the function like this:
file_path = input("Enter the path to store the information: ")
store_info(file_path, num_comments)
