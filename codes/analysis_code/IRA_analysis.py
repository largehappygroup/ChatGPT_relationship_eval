import os
import json
from sklearn.metrics import cohen_kappa_score
from sklearn.metrics import mean_squared_error
import numpy as np
from scipy.stats import kendalltau, spearmanr

cnt_posts = 0
cumulated_CK_score = 0
cumulated_SR_score = 0
cumulated_KT_score = 0
cumulated_PA_score = 0
cumulated_ICC_score = 0
ICC_scores = []
cv_list = []

trust_dict = {'num_posts': 0, 'agg_ICC': 0, 'agg_KT': 0, 'agg_SR': 0, 'agg_CK': 0, 'agg_CK': 0, 'agg_PA': 0}
family_dict = {'num_posts': 0, 'agg_ICC': 0, 'agg_KT': 0, 'agg_SR': 0, 'agg_CK': 0, 'agg_CK': 0, 'agg_PA': 0}
communication_dict = {'num_posts': 0, 'agg_ICC': 0, 'agg_KT': 0, 'agg_SR': 0, 'agg_CK': 0, 'agg_CK': 0, 'agg_PA': 0}
infidelity_dict = {'num_posts': 0, 'agg_ICC': 0, 'agg_KT': 0, 'agg_SR': 0, 'agg_CK': 0, 'agg_CK': 0, 'agg_PA': 0}
financial_dict = {'num_posts': 0, 'agg_ICC': 0, 'agg_KT': 0, 'agg_SR': 0, 'agg_CK': 0, 'agg_CK': 0, 'agg_PA': 0}

# inter-rater-agreement calculation
# Both gpt_ranking and reddit_ranking should ideally be integers
def cohen_kappa_calculation(gpt_ranking, reddit_ranking):
    return cohen_kappa_score(gpt_ranking, reddit_ranking)

def kendalltau_calculation(gpt_ranking, reddit_ranking):
    return kendalltau(gpt_ranking, reddit_ranking)

def spearman_rank_calculation(gpt_ranking, reddit_ranking):
    return spearmanr(gpt_ranking, reddit_ranking)

def percent_agreement(human_ranks, gpt_ranks):
    assert len(human_ranks) == len(gpt_ranks), "The two lists must have the same length"
    agree_count = sum(1 for h, g in zip(human_ranks, gpt_ranks) if h == g)
    return agree_count / len(human_ranks)

def calculate_icc(human_ranks, gpt_ranks):
    if len(human_ranks) != len(gpt_ranks):
        return -1
    assert len(human_ranks) == len(gpt_ranks), "The two lists must have the same length"
    n = len(human_ranks)
    mean_human = np.mean(human_ranks)
    mean_gpt = np.mean(gpt_ranks)
    msb = (sum([(mean_human - x)**2 + (mean_gpt - y)**2 for x, y in zip(human_ranks, gpt_ranks)])) / n
    mse = mean_squared_error(human_ranks, gpt_ranks)
    return (msb - mse) / (msb + (n-1)*mse)

def store_in_dict(var, target_dict):
    if (var in target_dict):
        target_dict[var] += 1
    else:
        target_dict[var] = 1

def post_analysis(post, home_path, human_ranking):
    post_path = home_path + post
    global cnt_posts, trust_dict, family_dict, infidelity_dict, financial_dict, communication_dict
    global cumulated_CK_score, cumulated_SR_score, cumulated_KT_score, cumulated_PA_score, cumulated_ICC_score
    global ICC_scores, cv_list

    sample = open(post_path)
    json_str = json.load(sample)
    cv = float(json_str['cv'])
    category = json_str['category'].lower()
    gpt_ranking = json_str['gpt_ranking']

    ICC_score = calculate_icc(human_ranking, gpt_ranking)
    KT_score = kendalltau_calculation(human_ranking, gpt_ranking)[0]
    SR_score = spearman_rank_calculation(human_ranking, gpt_ranking)[0]
    CK_score = cohen_kappa_calculation(human_ranking, gpt_ranking)
    PA_score = percent_agreement(human_ranking, gpt_ranking)

    cv_list.append(cv)
    ICC_scores.append(ICC_score)

    cumulated_ICC_score += ICC_score
    cumulated_KT_score += KT_score
    cumulated_SR_score += SR_score
    cumulated_CK_score += CK_score
    cumulated_PA_score += PA_score

    if (category == 'trust'):
        trust_dict['num_posts'] += 1
        trust_dict['agg_ICC'] += ICC_score
        trust_dict['agg_SR'] += SR_score
        trust_dict['agg_KT'] += KT_score
        trust_dict['agg_CK'] += CK_score
        trust_dict['agg_PA'] += PA_score
    
    if (category == 'family'):
        family_dict['num_posts'] += 1
        family_dict['agg_ICC'] += ICC_score
        family_dict['agg_SR'] += SR_score
        family_dict['agg_KT'] += KT_score
        family_dict['agg_CK'] += CK_score
        family_dict['agg_PA'] += PA_score

    if (category == 'infidelity'):
        infidelity_dict['num_posts'] += 1
        infidelity_dict['agg_ICC'] += ICC_score
        infidelity_dict['agg_SR'] += SR_score
        infidelity_dict['agg_KT'] += KT_score
        infidelity_dict['agg_CK'] += CK_score
        infidelity_dict['agg_PA'] += PA_score

    if (category == 'financial'):
        financial_dict['num_posts'] += 1
        financial_dict['agg_ICC'] += ICC_score
        financial_dict['agg_SR'] += SR_score
        financial_dict['agg_KT'] += KT_score
        financial_dict['agg_CK'] += CK_score
        financial_dict['agg_PA'] += PA_score

    if (category == 'communication'):
        communication_dict['num_posts'] += 1
        communication_dict['agg_ICC'] += ICC_score
        communication_dict['agg_SR'] += SR_score
        communication_dict['agg_KT'] += KT_score
        communication_dict['agg_CK'] += CK_score
        communication_dict['agg_PA'] += PA_score

def store_info():
    global cnt_posts, trust_dict, family_dict, infidelity_dict, financial_dict, communication_dict
    global cumulated_CK_score, cumulated_SR_score, cumulated_KT_score, cumulated_PA_score, cumulated_ICC_score
    global ICC_scores, cv_list

    cv_IRA_correlation = spearman_rank_calculation(cv_list, ICC_scores)
    
    # Interactive prompt for selecting the store path
    store_path = input("Enter the path to store the information: ")

    # Open the file for writing
    with open(store_path, "w") as outfile:
        # Store each piece of information
        outfile.write(f"For {cnt_posts} posts: \n")
        outfile.write(f"CV_IRA correlation coefficient:{cv_IRA_correlation[0]}, p_value: {cv_IRA_correlation[1]}\n")
        outfile.write(f"CV_IRA correlation coefficient:{cv_IRA_correlation[0]}, p_value: {cv_IRA_correlation[1]}\n")
        outfile.write(f"Intotal, the average IRA in CK is {float(cumulated_CK_score / cnt_posts)} with {cnt_posts} posts\n")
        outfile.write(f"Intotal, the average IRA in KT is {float(cumulated_KT_score / cnt_posts)} with {cnt_posts} posts\n")
        outfile.write(f"Intotal, the average IRA in SR is {float(cumulated_SR_score / cnt_posts)} with {cnt_posts} posts\n")
        outfile.write(f"Intotal, the average IRA in PA is {float(cumulated_PA_score / cnt_posts)} with {cnt_posts} posts\n")
        outfile.write(f"Intotal, the average IRA in ICC is {float(cumulated_ICC_score / cnt_posts)} with {cnt_posts} posts\n")

        # Print and store the category information
        categories = [trust_dict, family_dict, infidelity_dict, financial_dict, communication_dict]
        categories_names = ["trust", "family", "infidelity", "financial", "communication"]
        for category, name in zip(categories, categories_names):
            info_str = (f"For {name} category with {category['num_posts']} posts\n"
                        f"For {name} category, the average IRA in ICC is {float(category['agg_ICC']) / float(category['num_posts'])} with {category['num_posts']} posts. The average SR is {float(category['agg_SR']) / float(category['num_posts'])}. The average KT is {float(category['agg_KT']) / float(category['num_posts'])}. The average CK is {float(category['agg_CK']) / float(category['num_posts'])}. The average PA is {float(category['agg_PA']) / float(category['num_posts'])}\n")
            print(info_str)
            outfile.write(info_str)

human_ranking = []
relative_path = input("Enter the name of the folder storing the information: ")
num_comments = int(input("Enter the number of comments: "))
for i in range(1, num_comments + 1):
    human_ranking.append(i)
    
home_path = "/home/haonan/" + relative_path + "/"
post_names = os.listdir(home_path)
post_names.sort()

# Interactive prompt for selecting the starting and ending file
starting_file = input(f"Enter the name of the starting file (or 'all' to select all files in {home_path}): ")
if starting_file == "all":
    start_idx = 0
else:
    start_idx = post_names.index(starting_file) if starting_file in post_names else 0

ending_file = input("Enter the name of the ending file (or leave blank to continue to the end): ")
end_idx = post_names.index(ending_file) if ending_file in post_names else len(post_names)

# Loop through the posts starting and ending at the specific files
for post in post_names[start_idx:end_idx]:
    try:
        post_analysis(post, home_path, human_ranking)
        cnt_posts += 1
    except Exception as e:
        print(f"{e} encountered for {post}")

store_info()