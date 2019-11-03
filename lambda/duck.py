from bs4 import BeautifulSoup
import boto3, json, random, re, requests, datetime, holidays, tweepy, config, time

# Authenticate to Twitter
auth = tweepy.OAuthHandler(config.CONSUMER_TOKEN, config.CONSUMER_SECRET)
auth.set_access_token(config.ACCESS_TOKEN, config.ACCESS_SECRET)
# Set up API access
api = tweepy.API(auth)


def financeduck(event=None, context=None):
    # Set the headless browser header
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36"
    headers = {"User-Agent": user_agent}
    # Create title and link lists for manipulation
    link_list = []
    title_list = []

    # Scraping from The Dodo
    try:
        dodo_url = "https://www.thedodo.com/close-to-home"

        response = requests.get(dodo_url, headers=headers)
        dodo_soup = BeautifulSoup(response.content, "html.parser")

        dodo_list = dodo_soup.findAll(
            "a", attrs={"class": "double-column-listing__link u-block-link ga-trigger"}
        )

        [link_list.append(i["href"]) for i in dodo_list]

        for i in dodo_list:
            title_list.append(i.find("h2").text.strip())
    except:
        pass

    # Google News Scrape
    time.sleep(0.5)

    try:
        goog_url = "https://news.google.com/rss/search?q={funny+animals}"
        response = requests.get(goog_url, headers=headers)

        goog_soup = BeautifulSoup(response.content, "html.parser")

        goog_list = goog_soup.findAll("item")

        for title in goog_list:
            title_list.append(title.find("title").text.strip())

        for link in goog_list:
            link_list.append(re.findall("<link/>(.*?)<guid", str(link))[0])
    except:
        pass

    # Buzzpaws Scrape
    time.sleep(0.5)

    try:
        url = "http://www.buzzpaws.com/"
        response = requests.get(url, headers=headers)
        buzz_soup = BeautifulSoup(response.content, "html.parser")

        buzz_list = buzz_soup.findAll(
            "div", attrs={"class": "content-thumb content-list-thumb"}
        )

        for link in buzz_list:
            link_list.append(link.find("a")["href"])

        for title in buzz_list:
            title_list.append(title.find("a")["title"])
    except:
        pass

    # Analyze sentiment

    client = boto3.client("comprehend")
    sentiment = []

    for sentence in title_list:
        sentiment.append(
            client.detect_sentiment(Text=sentence, LanguageCode="en")["Sentiment"]
        )

    # Render titles into lower case for later publishing
    title_list = [x.lower() for x in title_list]

    # So now we have link_list, sentiment, and title_list in memory

    # Discover Whether the Market Closed Up or Down on the Day

    # Reset the user agent and headers
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36"
    headers = {"User-Agent": user_agent}

    # We can grab a closing price from Yahoo Finance
    url = "https://finance.yahoo.com/quote/^GSPC"

    response = requests.get(url, headers=headers)
    price_soup = BeautifulSoup(response.content, "html.parser")

    # Extract the string we want with price information
    price_text = price_soup.findAll("div", attrs={"class": "D(ib) Mend(20px)"})[0].text
    price_string = price_text[price_text.find("(") + 1 : price_text.find(")")]

    """
    Remove the four-digit delta in price, either positive or negative, from the Yahoo Finance
    string.
    """

    def price_format(price_string, price_text):
        price_1 = re.sub(
            r"\+[0-9]{1,2}[^(]*", " ", price_text, count=1
        )  # + change; count=1 means remove only first instance
        price_2 = re.sub(r"\-[0-9]{1,2}[^(]*", " ", price_text, count=1)  # - change

        if price_string[0] == "+":  # positive delta
            return price_1
        else:
            return price_2

    price_text = price_format(price_string, price_text)

    def price_clean(price_text):
        # Remove remaining text
        price_text = re.sub("[A-z]", "", price_text)
        # Remove remaining artifacts
        price_text = re.sub("[ :]", "", price_text)
        price_text = re.sub("\)[0-9]{3}", ")", price_text)
        # Format the text for Twitter printing
        price_text = price_text.replace("(", "\n(").replace(")", ")\n\n")
        # for some reason the chained replace was not working so it required a second pass, such...
        price_text = price_text.replace("..", "")
        return price_text

    price_text = price_clean(price_text)

    market_up = [
        "Hooray, you guys! The market finished up today. ",
        "Finance Duck is jazzed. Markets r up.",
        "Capitalism won today. Markets finished higher.",
        "Damn, son. Markets up.",
        """
                Adorable 4pm
                A happy market high-fives
                because of the ducks
                """,
        "Tell your friends. Market is up. All is well.",
        "If the markets aren't up, I'm a swan.",
        """
                gusting proudly, bulls
                savor passionate nectars,
                bears crying""",
        "yessir, markets are up.",
        "I'm pumped. Markets are too.",
    ]

    market_down = [
        "Dang it. Markets wet the bed.",
        "Release the QUACKEN! Market down.",
        "Whatever. I don't even care that the markets finished down.",
        "Well I'll be a lune's uncle; the markets finished down.",
        "Pfffft. Stupid markets. They finished (eider)down. Ohhhhhhhhh...",
        "Quack. Not even once.",
        "Nnnnggg, bahhhhh.",
        "Snap. Markets down a bit.",
        """
                Dire evening
                A dark, failing market descends
                forget the duck.""",
        "Flapping heck. Market down.",
        "My net worth is down. So is the market.",
    ]

    # Generate a Message Related to Where the Market Finished

    # First, we want to generate two options for contextual link sentences based on whether the first word of our article title is a verb or not.

    noun = "My analysis concludes that it's because this "
    verb = "My analysis concludes that you should "
    num = "My analysis concludes that the root cause is numeric. Here are "
    neither = "My analysis concludes that it's because "

    # Now we want to randomly select a duck message based on whether the market finished up or down.
    def duck_message(market_up, market_down, price_string):
        up_message = random.choice(market_up)
        down_message = random.choice(market_down)
        if price_string[0] == "+":
            return up_message
        else:
            return down_message

    duck_talk = duck_message(market_up, market_down, price_string)

    # Now we want to select a good article title and link to behave as the causal force in the market as identified by Finance Duck.

    def title_message(sentiment, title_list, price_string):
        # grab the index numbers of the respective sentiments
        pos_index = [i for i, x in enumerate(sentiment) if x == "POSITIVE"]
        neg_index = [i for i, x in enumerate(sentiment) if x == "NEGATIVE"]
        neut_index = [i for i, x in enumerate(sentiment) if x == "NEUTRAL"]
        # if the market finished up select our random positive message; if there is no pos message, go with a neutral
        if price_string[0] == "+":
            if len(pos_index) > 0:
                choice = random.choice(pos_index)
                return choice, title_list[choice]
            else:
                choice = random.choice(neut_index)
                return choice, title_list[choice]
        # if it finished down but there are no negative sentiment stories today, use the neutral messages...
        elif len(neg_index) == 0:
            choice = random.choice(neut_index)
            return choice, title_list[choice]
        else:
            choice = random.choice(neg_index)
            return choice, title_list[choice]

    # otherwise stay on plan and use the negative sentiment title

    choice, title_result = title_message(sentiment, title_list, price_string)

    # Parse the title to see if the first word is a verb or noun
    first_word = client.detect_syntax(Text=title_result, LanguageCode="en")[
        "SyntaxTokens"
    ][0]["PartOfSpeech"]["Tag"]

    def link_phrase(first_word, verb, noun, neither):
        if first_word == "VERB":
            return verb
        elif first_word == "NOUN":
            return noun
        elif first_word == "NUM":
            return num
        else:
            return neither

    anchor = link_phrase(first_word, verb, noun, neither)

    """
    Link extraction from data frame. 
    """
    link = link_list[choice]

    # Compile the final message

    tweet = (
        duck_talk
        + "\n\n"
        + "The S&P500 closed at: \n"
        + price_text
        + anchor
        + title_result
        + ":\n"
        + link
    )
    # Check the tweet will pass length criteria (280 max);
    # The auto URL shorterner scales back max potential tweet.
    if len(tweet) > 320:
        financeduck()
    else:
        return tweet


us_holidays = holidays.CountryHoliday("US")
today = datetime.date.today()

if today in us_holidays:
    message = "It's a holiday! No market shenanigans today. Have a good one."
else:
    try:
        message = financeduck()
    except:
        message = "uh oh, Duck 404. Back to the quacking board."


# Tweet message
api.update_status(message)

