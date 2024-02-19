# =============================================================================
# JWP Content Toolkit
# Hackweek project winter 2024 - Marco van de Veen & Michael Vernick
#
# Generate content suggestiong using subtitles and OpenAI
#
# =============================================================================

import requests
import argparse
import tempfile
from  utils import get_vtt_url
from  utils import get_vtt
from utils import add_vtt_to_media
from utils import update_media_metadata
from utils import get_media_item
from utils import extract_json
from utils import calculate_cost


# API REQUEST FUNCTIONS
def get_vtt_translation(media_id, vtt_content, site_id, jw_key, ai_key, lang_code):
    # Define the URL and headers for the API request
    model = "gpt-4-turbo-preview"
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ai_key}"
    }
    payload = {
        "model": f"{model}", 
        "messages": [
            {"role": "system", "content": "you are a translator of subtitles in VTT format"},
            {"role": "system", "content": vtt_content},
            {"role": "user", "content": f"translate each timestamp into {lang_code} and return in VTT format"}
        ]
    }

    # Make the POST request to the API
    response = requests.post(url, headers=headers, json=payload)


    if response.status_code == 200:
        data = response.json()
        calculate_cost(model, data['usage']['prompt_tokens'], data['usage']['completion_tokens'])
        # Get the message from the assistant (last message in the messages list)
        ai_output = data['choices'][0]['message']['content']

        # Write the AI output to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=f"_{lang_code}.vtt", prefix=f"{media_id}_", dir="./", encoding="utf-8") as temp_file:
            temp_file_path = temp_file.name  # Save the temp file's path
            temp_file.write(ai_output)  # Write the AI output to the temp file
        return temp_file_path
    else:
        print(f"AI Request failed with status code {response.status_code}")
        return None


def get_metadata_translation (media_id, site_id, jw_key, ai_key, lang_code):
    media_data = get_media_item(media_id, site_id, jw_key)
    title = media_data["metadata"]["title"]
    description = media_data["metadata"]["description"],
    
    # Define the URL and headers for the API request
    model = "gpt-4-turbo-preview"
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ai_key}"
    }
    payload = {
        "model": f"{model}", 
        "messages": [
            {"role": "system", "content": "you are a translator of video metadata"},
            {"role": "user", "content": f"translate the following in language {lang_code} and return as JSON:  {title} as 'title' and {description} as 'description'"}
        ]
    }

    # Make the POST request to the API
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    # Get the message from the assistant (last message in the messages list)
    translations = extract_json(data['choices'][0]['message']['content'])
    calculate_cost(model, data['usage']['prompt_tokens'], data['usage']['completion_tokens'])
    print(translations)
    update_media_metadata(site_id, jw_key, media_id, translations["title"], translations["description"], None, lang_code)
    
    return None
    

##MAIN
def main(media_id, site_id, jw_key, ai_key, lang_code):
    vtt = get_vtt(media_id, site_id, jw_key, lang_code)
    if vtt != None: 
        vtt_content = vtt
        print(vtt)
        vtt_translation_file = get_vtt_translation(media_id, vtt_content, site_id, jw_key, ai_key, lang_code)
        add_vtt_to_media(site_id, jw_key, media_id, vtt_translation_file, lang_code)
        #TODO prevent uploading another translation
    
    get_metadata_translation(media_id, site_id, jw_key, ai_key, lang_code)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process media id and prompt.')
    parser.add_argument('--media_id', type=str,  metavar='', required=True, help='The media id for which metadata needs to be generated')
    parser.add_argument('--site_id', type=str, metavar='', required=True, help='The site ID for JWP')
    parser.add_argument('--jw_key', type=str,  metavar='', required=True, help='The JWP V2 API Key')
    parser.add_argument('--ai_key', type=str, metavar='', required=False, help='The OpenAI API Key', default='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')
    parser.add_argument('--lang', type=str,  metavar='', required=True, help='The language to use. Needs to be supported by the OpenAI completion API.')
    
    args = parser.parse_args()
    
    main(args.media_id, args.site_id, args.jw_key, args.ai_key, args.lang)
