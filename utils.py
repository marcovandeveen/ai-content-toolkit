"""
Created on Wed Feb 14 14:24:03 2024

@author: marcovandeveen
"""


import requests
import json


def add_vtt_to_media(site_id, api_key, media_id, vtt_file_path, lang_code):
    """
    Uploads a VTT file to JWP using the provided site ID, media ID, and API v2 key.
    """
    
    url = f"https://api.jwplayer.com/v2/sites/{site_id}/media/{media_id}/text_tracks/"

    payload = {
        "upload": {
            "auto_publish": True,
            "method": "direct",
            "file_format": "vtt",
            "mime_type": "text/vtt"
        },
        "metadata": { 
            "track_kind": "captions",
            "srclang": f"{lang_code}",
            "label": f"{lang_code}"
            }
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    response = requests.post(url, json=payload, headers=headers)
    
    print(response.text)
    # Parse the JSON string into a Python dictionary
    response_json = json.loads(response.text)
    upload_link = response_json.get('upload_link', None)
    
    if upload_link:
    # Open the file in binary mode
        with open(vtt_file_path, 'rb') as file:
            # Perform the file upload
            upload_response = requests.put(upload_link, data=file, headers={'Content-Type': 'text/vtt'})
            
            # Check the upload response
            if upload_response.status_code == 200:
                print("Captions uploaded successfully")
            else:
                print(f"Failed to upload captions: {upload_response.status_code}, {upload_response.text}")
    else:
        print("No upload link available, cannot proceed with file upload.")
    

def get_vtt_url(mediaid):
    media_info_url = f"https://cdn.jwplayer.com/v2/media/{mediaid}"
    media_info = requests.get(media_info_url).json()
    vtt_url = None

    for playlist in media_info["playlist"]:
        for track in playlist.get("tracks", []):
            if track["kind"] == "captions":
                vtt_url = track["file"]
                break
        if vtt_url is not None:
            break

    return vtt_url

def get_vtt(mediaid,site_id, jw_key, lang_code=None):
    url = f"https://api.jwplayer.com/v2/sites/{site_id}/media/{mediaid}/text_tracks/"
    headers = {"Authorization": f"Bearer {jw_key}"}
    
    response = requests.get(url, headers=headers)
    data=response.json()
     # Iterate over the text tracks
    for track in data["text_tracks"]:
        # Check if the track kind is "captions" and status is "ready"
        if track["track_kind"] == "captions" and track["status"] == "ready" and track["metadata"]["srclang"] != lang_code:
            # Return the first matching track's id and delivery_url
                track_vtt = requests.get(track["delivery_url"]).text
                return track_vtt
    return None


def update_media_metadata(site_id, jw_key, media_id, title, description, keywords, lang_code=None):
    # Fetch the media item using GET request
    api_url = f"https://api.jwplayer.com/v2/sites/{site_id}/media/{media_id}"
    headers = {"Authorization": f"Bearer {jw_key}"}

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        media_data = response.json()
        custom_params = media_data.get("metadata", {}).get("custom_params", {})
        
        if lang_code is None:
            # Prepare the updated media item data for the default language
            updated_media_data = {
                "metadata": {
                    "title": title,
                    "tags": keywords,
                    "description": description,
                    "custom_params": custom_params
                }
            }
        else:
            translations = {
                f"title-{lang_code}": title,
                f"description-{lang_code}": description
            }
            # Merge the new custom_params with existing translated_metadata
            custom_params.update(translations)
            # Prepare the updated media item data for non-default language
            updated_media_data = {
                "metadata": {
                    "custom_params": custom_params
                }
            }
    
        # Send the updated media item using PATCH request
        response = requests.patch(api_url, headers=headers, json=updated_media_data)

        if response.status_code == 200:
            print("JWP Media item updated successfully \n")
        else:
            print("Error updating media item:", response.status_code, response.json())
    else:
        print("Error fetching media item:", response.status_code, response.json())
        
        
def fetch_media_item(media_id):
    """Fetch the media item from JWPlayer API."""

    api_url = f"https://cdn.jwplayer.com/v2/media/{media_id}"

    response = requests.get(api_url)

    if response.status_code != 200:
        print(f"Error fetching media item from cdn.jwplayer.com, Status code: {response.status_code}, Response: {response.json()}")
        return None

    media_info = response.json()
    playlist = media_info.get("playlist", [])

    content_type = playlist[0].get("contentType") if playlist else None
    if not content_type:
        print("No 'contentType' found in the media item.")
        return None

    return content_type


def get_media_item(media_id, site_id, api_key):
  # Fetch the media item using GET request
  api_url = f"https://api.jwplayer.com/v2/sites/{site_id}/media/{media_id}"
  headers = {"Authorization": f"Bearer {api_key}"}

  response = requests.get(api_url, headers=headers)
  if response.status_code == 200:
      return response.json()
  else: 
      print("Error retrieving media item:", response.status_code, response.json())
    
def extract_json(s):
    try:
        # Find the indices for the start and end of the JSON object
        obj_start = s.index('{')
        obj_end = s.rindex('}') + 1

        # Extract the JSON object string
        json_str = s[obj_start:obj_end]

        # Convert this string back to a JSON object/dictionary if needed
        json_obj = json.loads(json_str)
        return json_obj
    except (ValueError, json.JSONDecodeError) as e:
        print(f"Error: {e}")
        return None
    
def calculate_cost(model, input_tokens, output_tokens):
    """
    Calculate the completion price based on separate prices for input and output tokens.
    """
    input_price_per_1000=0
    output_price_per_1000=0
    
    # https://openai.com/pricing
    if model == "gpt-4-turbo-preview":
        input_price_per_1000=0.01
        output_price_per_1000=0.03
    elif model == "gpt-4-vision-preview":
        input_price_per_1000=0.01
        output_price_per_1000=0.03       
    
    # Calculate the cost for input and output tokens separately
    input_cost = (input_tokens / 1000) * input_price_per_1000
    output_cost = (output_tokens / 1000) * output_price_per_1000
    total_cost = input_cost + output_cost
    
    print(f"Input Cost: ${input_cost}")
    print(f"Output Cost: ${output_cost}")
    print(f"Total Cost: ${total_cost}")