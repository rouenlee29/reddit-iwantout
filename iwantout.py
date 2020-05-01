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

def check_continent_words(String):
        is_continent_word = False
        continent_words = ["south", "north", "east", "west", "central"]

        for c in continent_words:
            if c in String:
                is_continent_word = True
                break
        return is_continent_word

def find_country_using_fuzzy(List):

    """
    guess country from each word in List
    e.g if List = ['new','zealand'],
    search_fuzzy will guess 'new' to be 'new zealand' or 'new caledonia'
    search_fuzzy will guess 'zealand' to be 'new zealand'
    we take the most common guess, i.e 'new zealand'
    """
    # words that will belong to a continent and not a country
    

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

        # check if `s` contains any words in continent_words
        elif check_continent_words(s) == True:
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
    origin_region = map_country_to_continent(origin_country)

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
    
def capitalise_every_word(String):
    """
    "south america" becomes "South America"
    """

    List = String.split(" ")
    capitalised_list = []

    for L in List:
        capitalised_list.append(L.capitalize())

    capitalised_str = " ".join(capitalised_list)

    return capitalised_str

def get_destination_region(raw_string, country_list):
    
    """
    `region` can mean continent (e.g Asia, Europe) or subregion (European Union, Scandinavia)
    String contains ONLY name of a country 
    """    
    dest_region = []
    
    if country_list == []: # no countries found 
        # find manually from raw string
        region = ["africa","antarctica","asia","europe","north america","south america","oceania", "scandinavia"]
        dest_region += [capitalise_every_word(c) if c in raw_string else None for c in region]

        if ("eu," in raw_string) or (",eu" in raw_string):
            dest_region += ['European Union']

        dest_region = list(set(dest_region)) # remove duplicates
        
        if dest_region != [None]:
            dest_region.remove(None)
    else:
        for c in country_list:
            dest_region.append(map_country_to_continent(c))
    
    return dest_region

def get_destination(String):
    
    """
    Assumes countries are separated by symbols or text
    e.g. "us/uk", "australia or zimbabwe"

    returns a list of countries identified from fuzzy search 
    """
    
    String = String.lower()
    String = re.sub(r"( or |\\|/| and |\|)", ',', String)
    List = String.split(",")

    dest_country_list = []
    region = []
    
    #print(country_list)
    for c in List:
        
        if ("?" in c) or ("anywhere" in c) or (" x " in c):
            dest_country_list.append("anywhere")

        else:
            fuzzy_result = find_country_using_fuzzy([c.strip()])
            if fuzzy_result is not None:
                dest_country_list.append(fuzzy_result)
    
    dest_region_list = get_destination_region(String, dest_country_list)

    if dest_country_list == []:
        dest_country_list = [None] * len(dest_region_list)
            
    return dest_country_list, dest_region_list


# expldoe function below is...
# taken from https://stackoverflow.com/questions/45846765/efficient-way-to-unnest-explode-multiple-list-columns-in-a-pandas-dataframe
def explode(df, lst_cols, fill_value=''):
    # make sure `lst_cols` is a list
    if lst_cols and not isinstance(lst_cols, list):
        lst_cols = [lst_cols]
    # all columns except `lst_cols`
    idx_cols = df.columns.difference(lst_cols)

    # calculate lengths of lists
    lens = df[lst_cols[0]].str.len()

    if (lens > 0).all():
        # ALL lists in cells aren't empty
        return pd.DataFrame({
            col:np.repeat(df[col].values, df[lst_cols[0]].str.len())
            for col in idx_cols
        }).assign(**{col:np.concatenate(df[col].values) for col in lst_cols}) \
          .loc[:, df.columns]
    else:
        # at least one list in cells is empty
        return pd.DataFrame({
            col:np.repeat(df[col].values, df[lst_cols[0]].str.len())
            for col in idx_cols
        }).assign(**{col:np.concatenate(df[col].values) for col in lst_cols}) \
          .append(df.loc[lens==0, idx_cols]).fillna(fill_value) \
          .loc[:, df.columns]

# example of `explode` function usage:
# df
# 	A	        B           C
# 0	[1, 2, 3]	[2, 3, 4]   1
# 1	[3,4]	    [4, 5]      2
# 2	[5]	        [6]         3

# explode(df,['A','B'])
# 	A	B	C
# 0	1	2	1
# 1	2	3	1
# 2	3	4	1
# 3	3	4	2
# 4	4	5	2
# 5	5	6	3