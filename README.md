# ChatGPT Relationship Evaluation

Due to the large size of the raw dataset (~46GB), it is not included in this repository. If you would like access to the dataset, please contact us via email:
- **Kevin Leach**: kevin.leach@vanderbilt.edu  
- **Yu Huang**: yu.huang@vanderbilt.edu  
- **Haonan Hou**: haonan.hou@vanderbilt.edu  

## Data
This repository contains **sample** data from the study. The dataset is structured as follows:

- **pre_2022/** – Raw Reddit post data in JSON format. Each file follows the Reddit API structure, containing:
  - `title`, `selftext`: The original post content.
  - `num_comments`: Number of comments on the post.
  - `comments`: A list of comment objects, each containing metadata such as `author`, `score`, and `body`.

- **post_2022/** – Preprocessed Reddit data with numerical labels:
  - `99999` indicates the **original post (OP's text)**.
  - Any other number represents the **upvote count** of the corresponding comment.

## Code
The repository includes scripts for **data collection, OpenAI API evaluation, and analysis**:

- **`reddit_scraper.py`** – Scrapes Reddit posts and comments from relevant subreddits.
- **`pure_requester.py`** – Sends raw relationship posts and advice to OpenAI for ranking. NOTE: this might need update;
- **`variant_requester.py`** – A variation of `pure_requester.py`, incorporating additional contextual topics.
- **`comment_length_preference.py`** – Analyzes GPT's ranking preferences based on comment length.
- **`IRA_analysis.py`** – Measures inter-rater agreement between GPT rankings and human rankings.
- **`randomness_check.py`** – Evaluates the consistency of GPT-generated rankings.
