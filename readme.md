## TODO: add goal

## Run notebooks to scrape, transform and analyse data 

Create a `config.py` file containing `my_client_id` , `my_client_secret` and `my_user_agent`. These are required to scrape data from reddit using `PRAW` (The Python Reddit API Wrapper). For more info, see [here](https://praw.readthedocs.io/en/latest/getting_started/quick_start.html).

To run in the following order:
- `01. reddit-scrape.ipynb` : Use `PRAW` to scrape data
- `02. data-cleaning.ipynb` : Clean and transform raw data
- `03. analysis.ipynb` : Analyse transformed data. 

### Other notebook(s):
- `generate-test-csv.ipynb` : Take a sample of data created in `01. reddit-scrape.ipynb`, for testing and debugging. 

### Python files 

- `iwantout.py` : Functions to load, transform and analyse data 
- `contractions.py` : Function to expand contractions in words (I'm -> I am)
- `country_alpha2_to_continent.py` : Map country code to continent name  
- `process_text.py` : Functions to clean text 
- `sankey.py` : Code to generate sankey diagram.

### Other files 
- `iwantout-sankey.html` : Sankey diagram. Output from `03. analysis.ipynb`.

## ... Or just access the data in `output` folder 

The following are compressed outputs from `01. reddit-scrape.ipynb`, created from three different occasions.
- `iwantout.tar.gz` (API call on 26th April 2020)
- `iwantout_v2.tar.gz` (API call on 1st May 2020)
- `iwantout_v3.tar.gz` (API call on 7th May 2020)

Using the above files as inputs for `02. data-cleaning.ipynb` produces the transformed data `transformed.tar.gz`. 

Tip: to unzip file `iwantout.tar.gz`, type in your linux terminal:
```bash
tar -xvzf iwantout.tar.gz
```
## An overview of the data scraping and transformation processes

### Scraping raw data from reddit 
I have decided to honor reddit's scraping guidelines and use `PRAW`, the official Reddit scraping tool. 

However, one of its limitations is that the data we get in one API call is limited. I could only scrape a maximum of 500ish posts in a single call. To overcome this, I have invoked the API in three separate occasions overs three weeks. Hence, there are three output files from `01. reddit-scrape.ipynb` in the `output` folder.

Each row in data scraped by `PRAW` corresponds to one reddit post. 

### Transforming data 

The following processes happen at this stage:
- Map origin and destination country names to standardised country names. For example, mentions of "US" and "USA" will map to "the United States of America"

- Find the regions of origin and destination countries. My definition of _region_ is an area more than a country, but less or equal to a continent. For example: Scandinavia, European Union, South America etc. 

- Explode data. Say, a post lists both the United States and the United Kingdom as destinations. In the transformed dataset, the post will have two rows, one of the destinations for each row. 