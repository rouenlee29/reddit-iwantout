from csv import writer
import csv
import datetime
import re

def save_outputs_from_generator(output_csv, gen_obj, mode = 'a+', newline='', encoding='utf-8'):
    """
    Loops through gen_obj, and saves each result as a row in output_csv
   
    output_csv : String, filename of csv
    gen_obj : Generator function
    
    """
    
    with open(output_csv, mode, newline = newline, encoding = encoding) as write_obj:

        for r in gen_obj:
            # Add contents of list as last row in the csv file
            csv_writer = writer(write_obj)
            csv_writer.writerow(r)
    
    print(f"wrote to {output_csv}")
    
def get_data(reddit, limit, subreddit = 'IWantOut'):
    
    """
    Get relevant data from reddit API
    
    """
    try:
        hot_posts = reddit.subreddit(subreddit).hot(limit=limit)
        count = 0
        failed_ids = []

        for post in hot_posts: 
            # get contents of post 
            submission = reddit.submission(url=post.url)
            contents = submission.selftext

            yield [post.id, post.title,post.created, post.num_comments, post.url, contents]
    except:
        pass
    
 

    
def convert_date(dt):
    """
    convert date from integer to year/month/date format 
    
    """
    
    try:
        date = datetime.datetime.fromtimestamp(int(round(float(dt))))
        return date.strftime("%Y-%m-%d")
    except: 
        return None
    
def extract_data_from_raw(raw_csv,encoding='utf-8'):
    """
    reads and transforms raw data 
    """
    
    
    def extract_title(title):
        """
        Extact identity, origin, destination from post 

        """
        try:
            title = title.lower()
            identity = re.findall(r"[0-9][0-9][a-z]", title)[0].strip()
            job_and_countries = " ".join(title.split(identity)[1:])
            countries = re.findall(r"[a-z]+[\s]?->[\s]?.*", job_and_countries)
            job = " ".join(job_and_countries.split(countries[0])).strip()
            origin = countries[0].split("->")[0].strip()
            destination = countries[0].split("->")[1].strip()

            return identity, origin, destination,job

        except:

            return None, None, None, None
    
    first_row = True
    
    with open(raw_csv,encoding=encoding) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        for row in readCSV:
            if first_row:
                first_row = False
                yield ["index","identity", "origin", "destination","job","created_dt", "contents"]
                
            else:
                try:
                    index = row[0]
                    title = row[1]
                    
                    if "wantout" in title.lower():
                        created = row[2]
                        contents = row[5]

                        identity, origin, destination,job = extract_title(title)
                        created_dt = convert_date(created)

                        yield [index,identity, origin, destination,job,created_dt,contents]

                except: 
                    pass