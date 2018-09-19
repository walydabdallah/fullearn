import praw

reddit = praw.Reddit(client_id='Ncy3wGe7i_CcqA', \
                     client_secret='DbT67ln7EfU8GBSJLZrLgkD6Nhs', \
                     user_agent='fullearn-reddit', \
                     username='F22raptornuke', \
                     password='TaraChina1')
subreddit = reddit.subreddit("all")


def reddit_search(question, numResults):
    return subreddit.search(question, limit=numResults)
