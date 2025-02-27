import requests
import re
import os
import numpy
import spacy
nlp = spacy.load('en_core_web_sm')

def load_vader():
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    return SentimentIntensityAnalyzer()

try:
    vader_model = load_vader()
except LookupError as e:
    print(e)
    print('Attempting to download automatically...')
    import nltk 
    nltk.download('vader_lexicon')
    vader_model = load_vader()
    print('Success')


api_url = 'https://api.twitter.com/2/tweets/search/recent'
bearer_token = 'AAAAAAAAAAAAAAAAAAAAAIyUagEAAAAAwJxB%2BsJcNlgKNgKMKifUDwQXng4%3DXRKHHBl5MeXoeYlDra1KYstSRKM3D3WjTsaBt2cgktFOJYplTe'

def search_twitter(payload, bearer_token):
    auth = {
        'Authorization': 'Bearer '+str(bearer_token)
    }

    response = requests.get(api_url, params=payload, headers=auth)

    if response.status_code != 200:
        print('Error: Status Code '+str(response.status_code))
        return
    return response.json()


def get_tweets(query, bearer_token, results: int = 10):
    payload = {
        'query': 'lang:en '+str(query),
        'max_results': results,
        'sort_order': 'relevancy',
        'tweet.fields': 'id,text,public_metrics'
    }

    return search_twitter(payload, bearer_token)

def get_replies(id, bearer_token, results: int = 10):
    payload = {
        'query': 'lang:en conversation_id:'+str(id),
        'max_results': results,
        'sort_order': 'relevancy',
        'tweet.fields': 'text,public_metrics'
    }

    return search_twitter(payload, bearer_token)

def analyze_tweets(
    tweets, 
    num_replies: int = 10,
    parent_minimum_likes = 5,
    reply_minimum_likes = 1,
    parent_weight = 1,
    reply_weight = 1
):
    if tweets and 'data' in tweets:
        sentiments = []
        for tweet in tweets['data']:
            metrics = tweet['public_metrics']
            if metrics['like_count'] >= parent_minimum_likes:
                s = sentiment(tweet['text'])
                if s:
                    sentiments.append(
                            {
                                'sentiment': s,
                                'weight': parent_weight*(1 + metrics['retweet_count'] + metrics['like_count'])
                            }
                        )

            if num_replies:
                replies = get_replies(tweet['id'], bearer_token, num_replies)
                if replies and 'data' in replies:
                    for reply in replies['data']:
                        metrics = reply['public_metrics']
                        if metrics['like_count'] >= reply_minimum_likes:
                            s = sentiment(reply['text'])
                            if s:
                                sentiments.append(
                                    {
                                        'sentiment': s,
                                        'weight': reply_weight*(1 + metrics['retweet_count'] + metrics['like_count'])
                                    }
                                )

        weighted_average = numpy.average(
            [item['sentiment'] for item in sentiments],
            weights = [item['weight'] for item in sentiments]
        )
        return weighted_average
    else:
        print('Error: No tweets to analyze')

def sentiment_to_sentence(value, min=-1, max=1):
    if value < min+(max-min)*(1/6):
        return "strongly negative"
    elif value < min+(max-min)*(2/6):
        return "moderately negative"
    elif value < min+(max-min)*(3/6):
        return "slightly negative"
    elif value < min+(max-min)*(4/6):
        return "slightly positive"
    elif value < min+(max-min)*(5/6):
        return "moderately positive"
    else:
        return "strongly positive"

def sentiment_to_line(value, min=-1, max=1):
    line = '----------|----------'
    pos = (value-min) / (max-min)
    pos = int(numpy.round(pos*len(line)))
    line = line[:pos]+'*'+(line[(pos+1):] if pos<len(line) else '')
    return '(-) ['+line+'] (+)'
    
def sentiment(text):
    scores = vader_model.polarity_scores(text)
    return scores['compound']

print("""Welcome to
    ____             __  __       _    __          __         
   / __ \____ ______/ /_/ /_     | |  / /___ _____/ /__  _____
  / / / / __ `/ ___/ __/ __ \    | | / / __ `/ __  / _ \/ ___/
 / /_/ / /_/ / /  / /_/ / / /    | |/ / /_/ / /_/ /  __/ /    
/_____/\__,_/_/   \__/_/ /_/     |___/\__,_/\__,_/\___/_/     """)
while True:
    query = str(input('\nEnter a topic, URL, or filename to analyze: '))
    match = re.match(r'(?:https?:\/\/)?(?:www.)?twitter.com/[^/]*/status/([0-9]*)', query)
    if match:
        num_r = input('How many reply tweets to get? (10-100, default=25) ')
        num_r = num_r if num_r else 25

        print('Analyzing replies...')
        tweets = get_replies(match.group(1), bearer_token, num_r)
        snt = analyze_tweets(tweets, num_replies=0)
    elif os.path.isfile(query):
        with open(query) as file:
            text = file.read()
        doc = nlp(text)
        snt = numpy.average([sentiment(str(s)) for s in doc.sents])
    else:
        if not query[0] == '%':
            query = '"'+query+'"'
        else:
            query = query[1:]

        num_p = input('How many parent tweets to get? (10-100, default=100) ')
        num_p = num_p if num_p else 100
        num_r = input('How many reply tweets to get? (10-100, default=0) ')
        num_r = num_r if num_r else 0

        print('Analyzing topic...')
        tweets = get_tweets(query, bearer_token, num_p)
        snt = analyze_tweets(tweets, num_replies=num_r)

    if snt:
        print('Done! Found overall ' + sentiment_to_sentence(snt) + ' sentiment (' + str(numpy.round(snt, 4))+')')
        print(sentiment_to_line(snt))
