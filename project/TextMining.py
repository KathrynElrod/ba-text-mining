import re
import requests
import json

api_url = 'https://api.twitter.com/2/tweets/search/recent'
bearer_token = 'AAAAAAAAAAAAAAAAAAAAAIyUagEAAAAAwJxB%2BsJcNlgKNgKMKifUDwQXng4%3DXRKHHBl5MeXoeYlDra1KYstSRKM3D3WjTsaBt2cgktFOJYplTe'

conversation_id = None
while not conversation_id:
    url = input('URL of parent tweet: ')
    match = re.match(r'(?:https?:\/\/)?(?:www.)?twitter.com/[^/]*/status/([0-9]*)', url)
    if match:
        conversation_id = match.group(1)
    else:
        print("Sorry, that's not a valid URL. Please try again.")

payload = {
    'query': 'lang:en conversation_id:'+str(conversation_id),
    'max_results': 10,
    'sort_order': 'relevancy',
    'tweet.fields': 'text,public_metrics'
}

auth = {
    'Authorization': 'Bearer '+str(bearer_token)
}

response = requests.get(api_url, params=payload, headers=auth)
print(json.dumps(response.json(), indent=2))