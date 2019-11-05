# Finance Duck
 A Duck. That Knows Finance. 
 
Finance Duck a is a python-based Twitter bot ([@financeduck](https://twitter.com/FinanceDuck)) that runs on AWS's serverless Lambda service. 

### Key Features of the Project
* Serverless Twitter bot;
* Built in python;
* Uses Amazon's Comprehend API for sentiment analysis and syntactic parsing;
* Grabs the closing price of the S&P 500 and "explains" the price change with a cute animal story;
* Scrapes animal stories using the `requests` and `bs4` libraries.

### Project Files and Content Explained

**lambda directory**: A zipped version of this folder is loaded into the AWS Lambda console. It contains the core `duck.py` script file and all of the dependencies that the function uses to tweet. The Lambda SDK has python 3.7 and the boto3 (Amazon web service API) built in, so neither of those has to be included in the dependencies list. 

**config.py**: This is the file that contains the Twitter environment variables used to login and tweet. Lambda allows you to set your own environment variables and encrypt them. I used this method to avoid more AWS configuration changes. The config file is loaded as a library in `duck.py` and the variables are referenced early in the code sequence. 

**amazon_api_version.ipynb**: This is a Jupyter notebook that I used to test all of the individual elements of the function. For example, the web-scraping and sentiment analysis tasks. It contains a consolidated version of the `duck.py` code that culminates in a `print(tweet)` command so you can see the fruits of your labor before tweeting. The remaining cells contain tests for the Tweepy API, and a small chunk of code you can use to scrape stories from Google News based on a unique search. 
 
 `git clone "https://github.com/timraiswell/financeduck/"`
