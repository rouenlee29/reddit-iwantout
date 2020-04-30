from csv import writer
import csv
import datetime
import re
import pycountry
from collections import Counter 

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

def most_frequent(List): 
    occurence_count = Counter(List) 
    return occurence_count.most_common(1)[0][0] 

def find_country_using_fuzzy(List):

    """
    guess country from each word in List
    e.g if List = ['new','zealand'],
    search_fuzzy will guess 'new' to be 'new zealand' or 'new caledonia'
    search_fuzzy will guess 'zealand' to be 'new zealand'
    we take the most common guess, i.e 'new zealand'
    """

    country_name = None
    candidates = []

    for s in List:
        if s == "uk":
            country_name =  "United Kingdom"
            break
        elif s == "us" :
            country_name = "United States"

        elif s == "eu" : 
            # search_fuzzy returns "reunion" for "eu", and we want to prevent this
            # because it means european union 
            country_name = "European Union"
        else: 
            try:
                guesses = pycountry.countries.search_fuzzy(s)
                candidates += [g.name for g in guesses]
            except:
                pass

    if candidates != []:
        country_name = most_frequent(candidates)

    return country_name
    
def find_job(List):
    jobs = []
    for s in List:
        try:
            _ = pycountry.countries.search_fuzzy(s)
        except: # if fails
            jobs.append(s)
    return " ".join(jobs)

def extract_title(title):
    title = title.lower()
    
    # Age&Sex: get contents that contains 2 numbers followed by an alphabet 
    identity = re.findall(r"[0-9][0-9][a-z]", title)[0].strip()
    
    # get whatever is after Age&Sex 
    job_and_countries = " ".join(title.split(identity)[1:])
    
    # get whatever is after "->"
    destination = job_and_countries.split("->")[1].strip()
    destination = re.sub('[^a-zA-Z]', " ", destination)

    
    # get whatever is before "->"
    job_and_origin = job_and_countries.split("->")[0].strip()
    job_and_origin = job_and_origin.split(" ") # convert to list
    
    origin = find_country_using_fuzzy(job_and_origin)
    job = find_job(job_and_origin)

    return identity, origin, destination,job

    
def extract_data_from_raw(raw_csv,encoding='utf-8'):
    """
    reads and transforms raw data 
    """
    
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