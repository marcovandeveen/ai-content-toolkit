# =============================================================================
# JWP Content Toolkit
# Hackweek project winter 2024 - Marco van de Veen & Michael Vernick
#
# Generate content suggestiong using subtitles and OpenAI
# python3 metadata.py --media_id=yMLK4ZlS --site_id=sbF4ehVe --jw_key=535xMmU0a8D0CZaRfWjsEmInUms1WldXRm9hbEIxT1dZNE1HaGhVMU55ZG5JM2RWUXon
#
# =============================================================================

import requests
import argparse
from utils import get_vtt_url
from utils import update_media_metadata
from utils import extract_json
from utils import calculate_cost


# API REQUEST FUNCTIONS
def get_metadata_from_captions(media_id, subtitles, ai_key, lang_code):
    """Makes an API request to the OpenAI API and returns the AI's response."""
    
    model = "gpt-4-turbo-preview"  # GPT-4-turbo can handle about 100k words of input (3-4 hours of video)


    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ai_key}"
    }
    payload = {
        "model": f"{model}",
        "messages": [
            {"role": "system", "content": "You are an assistant to video content editors. You create engaging content based on video subtitles."},
            {"role": "system", "content": subtitles},
            {"role": "user", "content": "generate a 'title' with max 35 characters, a 'description', and 5 'keywords' with language {lang_code} in json format"}
        ]
    }

    # Make the POST request to the API
    response = requests.post(url, headers=headers, json=payload)
    print(response)
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        calculate_cost(model, data['usage']['prompt_tokens'], data['usage']['completion_tokens'])
       
    # Get the message from the assistant (last message in the messages list)
        ai_output = data['choices'][0]['message']['content']
        return ai_output
    else:
        print(f"AI Request failed with status code {response.status_code}")
        return None


def get_metadata_from_image(media_id, ai_key, lang_code):
    model = "gpt-4-vision-preview"  # GPT-4-vision can handle about 100k words of input (3-4 hours of video)

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {ai_key}"
    }
    
    payload = {
      "model": "gpt-4-vision-preview",
      "messages": [
        {"role": "system", "content": "You are an assistant to video content editors. You create engaging content based on video images."},
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": f"Generate a 'title', a 'description' and 'keywords' for this video based on this image in language {lang_code} in json format"
            },
            {
              "type": "image_url",
              "image_url": {
                "url": f"https://cdn.jwplayer.com/strips/{media_id}-120.jpg"
              }
            }
          ]
        }
      ],
      "max_tokens": 1000
    }
    
    
    # Make the POST request to the API
    response = requests.post(url, headers=headers, json=payload)
    print(response)
        
    # Check if the request was successful
    if response.status_code == 200: 
        data = response.json()
        prompt_tokens = data['usage']['prompt_tokens']
        completion_tokens = data['usage']['completion_tokens']
        print(f"Prompt (input) tokens: {prompt_tokens}")
        print(f"Prompt (completion) tokens: {completion_tokens}")
        calculate_cost(model, data['usage']['prompt_tokens'], data['usage']['completion_tokens'])
        # Get the message from the assistant (last message in the messages list)
        ai_output = data['choices'][0]['message']['content']
        return ai_output
    else:
        print(f"AI Request failed with status code {response.status_code}")
        return None
    

##MAIN
def main(media_id, site_id, jw_key, ai_key, lang):
    vtt_url = get_vtt_url(media_id)
    ai_output = None
    
    if vtt_url is None:
        ai_output = get_metadata_from_image(media_id, ai_key, lang)
    else:
        vtt_content = requests.get(vtt_url).text
        ai_output = get_metadata_from_captions(media_id, vtt_content, ai_key, lang)

    response_dict = extract_json(ai_output)

    if response_dict:
        title = response_dict['title']
        description = response_dict['description']
        keywords = response_dict['keywords']
        
        print(f"Title: {title}")
        print(f"Description: {description}")
        print(f"Keywords: {keywords}")

        update_media_metadata(site_id, jw_key, media_id, title, description, keywords)
    else:
        print("No valid JSON found in AI output.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process media id and prompt.')
    parser.add_argument('--media_id', type=str,  metavar='', required=True, help='The media id for which metadata needs to be generated')
    parser.add_argument('--site_id', type=str, metavar='', required=True, help='The site ID for JWP')
    parser.add_argument('--jw_key', type=str,  metavar='', required=True, help='The JWP V2 API Key')
    parser.add_argument('--ai_key', type=str, metavar='', required=False, help='The OpenAI API Key', default='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')
    parser.add_argument('--lang', type=str,  metavar='', required=False, help='The language to use. Needs to be supported by the OpenAI completion API. Defaults to English', default='en')
    
    args = parser.parse_args()
    
    main(args.media_id, args.site_id, args.jw_key, args.ai_key, args.lang)