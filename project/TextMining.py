import requests
import numpy

api_url = 'https://api.twitter.com/2/tweets/search/recent'
bearer_token = 'AAAAAAAAAAAAAAAAAAAAAIyUagEAAAAAwJxB%2BsJcNlgKNgKMKifUDwQXng4%3DXRKHHBl5MeXoeYlDra1KYstSRKM3D3WjTsaBt2cgktFOJYplTe'

def search_twitter(query, bearer_token, results: int = 10):
    payload = {
        'query': 'lang:en '+str(query),
        'max_results': results,
        'sort_order': 'relevancy',
        'tweet.fields': 'id,text,public_metrics'
    }

    auth = {
        'Authorization': 'Bearer '+str(bearer_token)
    }

    response = requests.get(api_url, params=payload, headers=auth)
    if response.status_code != 200:
        print('Error: Status Code '+str(response.status_code))
        return
    if not 'data' in response.json().keys():
        print('Error: No tweets found')
        return
    return response.json()

def get_replies(id, bearer_token, results: int = 10):
    """
    match = re.match(r'(?:https?:\/\/)?(?:www.)?twitter.com/[^/]*/status/([0-9]*)', url)
    if not match:
        print('Error: Not a valid tweet URL')
        return
    conversation_id = match.group(1)
    """

    payload = {
        'query': 'lang:en conversation_id:'+str(id),
        'max_results': results,
        'sort_order': 'relevancy',
        'tweet.fields': 'text,public_metrics'
    }

    auth = {
        'Authorization': 'Bearer '+str(bearer_token)
    }

    response = requests.get(api_url, params=payload, headers=auth)
    if response.status_code != 200:
        print('Error: Status Code '+str(response.status_code)+': '+response.text)
        return
    if not 'data' in response.json().keys():
        print('Error: No replies found')
        return
    return response.json()

def sentiment(text):
    #TODO
    return 0.5

def analyze_topic(
    query, 
    bearer_token, 
    num_parents: int = 10, 
    num_replies: int = 10,
    parent_weight = 1,
    reply_weight = 1
):
    tweets = search_twitter(query, bearer_token, num_parents)
    if tweets:
        sentiments = []
        for tweet in tweets['data']:
            sentiments.append(
                    {
                        'sentiment': sentiment(tweet['text']),
                        'weight': parent_weight*(1 + tweet['public_metrics']['retweet_count'] + tweet['public_metrics']['quote_count'] + tweet['public_metrics']['like_count'])
                    }
                )
            if num_replies:
                replies = get_replies(tweet['id'], bearer_token, num_replies)
                if replies:
                    for reply in replies['data']:
                        metrics = reply['public_metrics']
                        sentiments.append(
                            {
                                'sentiment': sentiment(reply['text']),
                                'weight': reply_weight*(1 + metrics['retweet_count'] + metrics['quote_count'] + metrics['like_count'])
                            }
                        )
        weighted_average = numpy.average(
            [item['sentiment'] for item in sentiments],
            weights = [item['weight'] for item in sentiments]
        )
        return weighted_average

# Only parent tweets for now - replies works, I'm just worried abt duplicates
print(analyze_topic('"Mac Pro"', bearer_token, num_replies=0))
