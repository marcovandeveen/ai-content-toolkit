"""
This script fetches audio from JWP media and transcribes it used OpenAI Whisper and uploads to JWP. 

"""

import requests
import tempfile
import whisper
import argparse
import sys
import os
from whisper.utils import get_writer
from utils import add_vtt_to_media


def fetch_media_m4a(media_id):
    """
    Fetches the .m4a audio URL from JWP media JSON for a given media ID,
    then downloads the audio and stores it in a temporary file.
    """
    media_url = f'https://cdn.jwplayer.com/v2/media/{media_id}'
    response = requests.get(media_url)
    response.raise_for_status()
    
    data = response.json()
    
    m4a_url = None
    # Traverse the sources list in the json to find the .m4a file URL
    for item in data.get('playlist', []):
        for source in item.get('sources', []):
            if source.get('type') == "audio/mp4" and source.get('file').endswith('.m4a'):
                m4a_url = source['file']
                break
        if m4a_url:
            break
    
    if not m4a_url:
        return None  # Return None if no .m4a URL is found
    
    # Fetch the audio data from the m4a URL
    audio_response = requests.get(m4a_url)
    audio_response.raise_for_status()
    
    # Create a temporary file to store the audio data
    with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as temp_audio_file:
        temp_audio_file.write(audio_response.content)
        return temp_audio_file.name

def generate_vtt(media_id):
    """Processes an audio file with the whisper library, writes VTT content to a temp file with the detected language in the filename, and returns VTT content as a string."""
    
    audio_file_path = fetch_media_m4a(media_id)
    
    # Load the Whisper model
    model = whisper.load_model("small")
    # Transcribe the audio file
    result = model.transcribe(audio_file_path, fp16=False)
    
    # Extract detected language code from the result
    lang_code = result["language"]
    
    # Use a temporary file to initially write the VTT content
    with tempfile.NamedTemporaryFile(delete=False, mode="w+", suffix=f"_{lang_code}.vtt", dir="./") as temp_file:
        temp_file_path = temp_file.name  # Temporary file path
        
        # Assuming 'vtt_writer' is a function that accepts the result, file path, and writes to that path
        vtt_writer = get_writer("vtt", "./")  # Assuming get_writer returns a function that writes the VTT
        vtt_writer(result, temp_file_path)  # Write the VTT to the temp file
        
        # Go back to the beginning of the file to read its content
        temp_file.seek(0)
        vtt_content = temp_file.read()
    
    # Optionally, move or rename the temp file to include the detected language in its name more explicitly if needed
    # For now, we clean up the temporary file
    print(vtt_content)
    
    # Print or return the VTT content
    return temp_file_path, lang_code

def main(media_id, site_id, jw_key):
    vtt_file_path, lang_code = generate_vtt(media_id)
    add_vtt_to_media(site_id,jw_key, media_id, vtt_file_path, lang_code)
    os.remove(vtt_file_path)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process media id and prompt.')
    parser.add_argument('--media_id', type=str,  metavar='', required=True, help='The media id for which metadata needs to be generated')
    parser.add_argument('--site_id', type=str, metavar='', required=True, help='The site ID for JWP')
    parser.add_argument('--jw_key', type=str,  metavar='', required=True, help='The JWP V2 API Key')
    
    args = parser.parse_args()
    
    main(args.media_id, args.site_id, args.jw_key)
