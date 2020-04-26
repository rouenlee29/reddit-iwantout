from csv import writer

def scrape_iwantout(reddit, limit, write_filename):
    
    hot_posts = reddit.subreddit('IWantOut').hot(limit=limit)
    count = 0
    failed_ids = []

    for post in hot_posts: 

        try:
            # get contents of post 
            submission = reddit.submission(url=post.url)
            contents = submission.selftext

            with open(write_filename, 'a+', newline='',encoding='utf-8') as write_obj:
                csv_writer = writer(write_obj)
                # Add contents of list as last row in the csv file
                csv_writer.writerow([post.id, post.title,post.created, post.num_comments, post.url, contents])
            count += 1

        except:
            failed_ids.append(post.id)

    print(f"saved {count} posts to {write_filename}")
    print(f"{len(failed_ids)} failed ids")