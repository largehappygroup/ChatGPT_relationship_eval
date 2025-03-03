import os
import json
from scipy.stats import kendalltau

def kendalltau_calculation(ranking_1, ranking_2):
    return kendalltau(ranking_1, ranking_2)

file_groups = {}
errored_posts = []
cumulated_different_rankings = 0
cumulated_severe_disagreement = 0
cumulated_KT_score = 0
num_pairs = 0
cumulated_complete_consistency = 0

path_selected = input("What is the folder to examine?")
home_path = "/home/haonan/" + path_selected + "/"
num_comments = int(input("What is the number of comments?"))
if num_comments not in [2, 4, 8]:
    raise ValueError("Number of comments should be 2, 4, or 8.")

file_names = os.listdir(home_path)
file_names.sort()

for file in file_names:
    try:
        if any(file.startswith(item) for item in errored_posts):
            continue
        sample = open(home_path + file)
        json_str = json.load(sample)

        response = json_str['gpt_ranking']
        gpt_ranking = response.split(", ")
        if "." in gpt_ranking[-1]:
            gpt_ranking[-1] = gpt_ranking[-1][:-1]
        if len(gpt_ranking) <= 1:
            gpt_ranking = response.split(",")
            if len(gpt_ranking) <= 1:
                raise ValueError("Invalid gpt_ranking list length")

        final_ranking = [int(item) for item in gpt_ranking]

        if len(final_ranking) != num_comments:
            raise ValueError("Invalid gpt_ranking list length")

        if file[:-1] not in file_groups:
            file_groups[file[:-1]] = []

        file_groups[file[:-1]].append(final_ranking)

    except Exception as e:
        errored_posts.append(file[:-1])
        file_groups.pop(file[:-1], None)
        print("Exception encountered:", e)
        print("The file", file, "is not examined")

# Removing groups that don't have exactly 4 files
for key in list(file_groups.keys()):
    if len(file_groups[key]) != 4:
        file_groups.pop(key)

cnt_rankings = sum([len(v) for v in file_groups.values()])
cnt_posts = len(file_groups)

for group, rankings in file_groups.items():
    group_num_rankings = 0
    group_severe_disagreement = 0
    total_KT_score = 0

    try:
        seen_rankings = set()
        for i in range(len(rankings)):
            for j in range(i + 1, len(rankings)):
                ranking_1 = rankings[i]
                ranking_2 = rankings[j]
                seen_rankings.add(str(ranking_1))
                seen_rankings.add(str(ranking_2))

                KT_score = kendalltau_calculation(ranking_1, ranking_2).correlation

                total_KT_score += KT_score
                if KT_score < 0:
                    group_severe_disagreement += 1
                    
                num_pairs += 1

        average_KT_score = total_KT_score / num_pairs
        cumulated_different_rankings += len(seen_rankings)
        cumulated_severe_disagreement += group_severe_disagreement
        cumulated_KT_score += average_KT_score
        if (len(seen_rankings) == 1):
            cumulated_complete_consistency += 1

        # print(seen_rankings)

    except Exception as e:
        print("Exception encountered:", e)
        print("The post", group, "is not examined")

def store_info():
    global cnt_posts, cumulated_different_rankings, cumulated_severe_disagreement, cumulated_KT_score, cumulated_complete_consistency, num_pairs

    # Interactive prompt for selecting the store path
    store_path = input("Enter the path to store the information: ")

    # Open the file for writing
    with open(store_path, "w") as outfile:
        # Store each piece of information
        outfile.write(f"For {cnt_posts} posts, {cnt_rankings} rankings, {num_pairs} pairs of rankings\n")
        outfile.write(f"The rankings are consistent for {cumulated_complete_consistency} times with rate of {float(cumulated_complete_consistency / cnt_posts)}\n")
        outfile.write(f"Cumulated Different rankings: {cumulated_different_rankings}\n")
        outfile.write(f"On average, for each 4 rankings of the same question, GPT generates {float(cumulated_different_rankings / cnt_posts)} different rankings\n")
        outfile.write(f"Cumulated Severe Disagreement: {cumulated_severe_disagreement} among {num_pairs} pairs of rankings\n")
        outfile.write(f"Average Severe disagreement for rankings of the same question: {float(cumulated_severe_disagreement / num_pairs)}\n")
        outfile.write(f"Cumulated Average Kendall's Tau Score (Agreement Level): {cumulated_KT_score}\n")
        outfile.write(f"Average Kendall's Tau Score (Agreement Level): {float(cumulated_KT_score / cnt_posts)}\n")

        # As a feedback to the user
        print("Information successfully stored to:", store_path)

print(f"For {cnt_posts} posts, {cnt_rankings} rankings, {num_pairs} pairs of rankings")
print(f"The rankings are consistent for {cumulated_complete_consistency} times with rate of {float(cumulated_complete_consistency / cnt_posts)}")
print("Cumulated Different rankings: ", cumulated_different_rankings)
print(f"On average, for each 4 rankings of the same question, GPT generates {float(cumulated_different_rankings / cnt_posts)} different rankings")
print(f"Cumulated Severe Disagreement: {cumulated_severe_disagreement} among {num_pairs} pairs of rankings")
print("Average Severe disagreement for rankings of the same question:", float(cumulated_severe_disagreement / num_pairs))
print("Cumulated Average Kendall's Tau Score: (Agreement Level)", cumulated_KT_score)
print("Average Kendall's Tau Score: (Agreement Level)", float(cumulated_KT_score / cnt_posts))
store_info()