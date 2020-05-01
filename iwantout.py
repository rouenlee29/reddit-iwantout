from csv import writer
import csv
import datetime
import re
import pycountry
from collections import Counter 
import pycountry_convert as pc
from country_alpha2_to_continent import convert_country_alpha2_to_continent

# GET DATA FROM REDDIT 

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
    
def get_data(reddit, limit, subreddit = 'IWantOut', created_cutoff=0):
    
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
            
            if post.created > created_cutoff:
                yield [post.id, post.title,post.created, post.num_comments, post.url, contents]
    except:
        pass
    
# PROCESS RAW DATA

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
            # because it means european union and we want to categorise it as a region
            pass

        elif len(s) == 1:
            # one letter words are unlikely to be countries 
            # but search_fuzzy will try to guess countries from it 
            pass

        else: 
            try:
                guesses = pycountry.countries.search_fuzzy(s)
                candidates += [g.name for g in guesses]
            except:
                pass

    # get the one most common country 
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
    dest_countries, dest_regions = get_destination(destination)

    # get whatever is before "->"
    job_and_origin_str = job_and_countries.split("->")[0].strip()
    job_and_origin_list = job_and_origin_str.split(" ") 
    origin_country = find_country_using_fuzzy(job_and_origin_list)
    origin_region = get_destination_region([origin_country], job_and_origin_str)

    job = find_job(job_and_origin_list)

    return identity, origin_country, origin_region, dest_countries, dest_regions,job

    
def load_and_transform_raw_data(raw_csv_list,encoding='utf-8'):
    """
    got through each csv file in `raw_csv_list`
    reads the csv one row at a time.
    transforms a row and returns a list containing transformed data from the row 
    """
    
    first_row = True
    
    for raw_csv in raw_csv_list:
        with open(raw_csv,encoding=encoding) as csvfile:
            readCSV = csv.reader(csvfile, delimiter=',')

            for row in readCSV:
                if first_row:
                    first_row = False
                    yield ["index","identity", "origin_country", "origin_region", "destination_countries", "destination_regions", "job","created_dt", "contents"]
                    
                else:
                    try:
                        index = row[0]
                        title = row[1]
                        
                        if "wantout" in title.lower():
                            created = row[2]
                            contents = row[5]

                            identity, origin_country, origin_region, dest_countries, dest_regions,job = extract_title(title)
                            created_dt = convert_date(created)

                            yield [index,identity, origin_country, origin_region, dest_countries, dest_regions,job,created_dt,contents]

                    except: 
                        pass

def map_country_to_continent(String):
    """
    maps country name to continent name
    returns `None` if no match is found 
    """
    try:
        # if it is a country name, map to continent 
        country_code = pc.country_name_to_country_alpha2(String, cn_name_format="lower")
        continent_name = convert_country_alpha2_to_continent(country_code)
    except:
        continent_name = None
    return continent_name
    
    

def get_destination_region(dest_countries_list, raw_dest_str):
    
    """
    `region` can mean continent (e.g Asia, Europe) or subregion (European Union, Scandinavia)
    """
    dest_region = []
    
    # see if any continents are contained in raw string 
    region = ["africa","antarctica","asia","europe","north america","south america","oceania", "scandinavia"]
    dest_region += [c if c in raw_dest_str else None for c in region]
    
    if ("eu," in raw_dest_str) or (",eu" in raw_dest_str):
        dest_region += ['european union']
    
    # map countries to continens 
    if dest_countries_list != []:
        dest_region += [map_country_to_continent(d) for d in dest_countries_list]
        
    # take unique values
    dest_region = list(set(dest_region))
    
    if None in dest_region:
        dest_region.remove(None)
    
    return dest_region

def get_destination(String):
    
    """
    Assumes countries are separated by symbols or text
    e.g. "us/uk", "australia or zimbabwe"
    """
    
    String = String.lower()
    String = re.sub(r"( or |\\|/| and |\|)", ',', String)
    
    country_list = String.split(",")
    dest = []
    region = []
    
    #print(country_list)
    for c in country_list:
        
        if ("?" in c) or ("anywhere" in c) or (" x " in c):
            dest.append("anywhere")

        else:
            fuzzy_result = find_country_using_fuzzy([c])
            if fuzzy_result is not None:
                dest.append(fuzzy_result)
    #print(String)
    dest_region = get_destination_region(dest, String)
            
    return dest, dest_region