from flask import Flask, jsonify, request, render_template, g, send_from_directory
import sqlite3
import os
import requests
from config import API_V1_URL, API_V1_URL_2, ACCESS_TOKEN, API_V2_URL, BALANCE_API_URL, USERNAME_API_URL
from urllib.parse import urlparse, unquote
from urllib.parse import urlparse
import hashlib
from pydub import AudioSegment
import whisper
import time
import threading


app = Flask(__name__, template_folder='templates', static_url_path='/static')
DATABASE = 'database.db'
model = whisper.load_model('tiny')

IMAGE_FOLDER = os.path.join(app.root_path, 'static', 'thumbnails')
AUDIO_FOLDER = os.path.join(app.root_path, 'static', 'audio')

headers = {
    'accept': 'application/json',
    'x-access-key': ACCESS_TOKEN
}

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usernamesandids (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                unique_id TEXT UNIQUE NOT NULL
            )
        ''')
        db.commit()


@app.route('/')
def index():
    return render_template('index.html')

def get_filename_from_url(url):
    """Extract the filename from the URL."""
    parsed_url = urlparse(url)
    return os.path.basename(unquote(parsed_url.path))

def convert_to_wav(audio_path):
    """Convert audio file to WAV format if not already."""
    audio = AudioSegment.from_file(audio_path)
    wav_path = os.path.splitext(audio_path)[0] + ".wav"
    audio.export(wav_path, format="wav")
    return wav_path

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    data = request.get_json()
    audio_url = data.get('audio_url')
    if not audio_url:
        return jsonify({'error': 'audio_url is required'}), 400

    try:
        # Download the audio file
        audio_response = requests.get(audio_url)
        audio_response.raise_for_status()

        # Extract the file name from the URL
        file_name = get_filename_from_url(audio_url)
        audio_path = os.path.join(app.root_path, 'static', 'audio', file_name)

        # Ensure the directory exists
        if not os.path.exists(os.path.dirname(audio_path)):
            os.makedirs(os.path.dirname(audio_path))

        # Save the audio file locally
        with open(audio_path, 'wb') as audio_file:
            audio_file.write(audio_response.content)

        # Convert audio to WAV format
        wav_path = convert_to_wav(audio_path)
        result = model.transcribe(wav_path)

        return jsonify({'transcription': result["text"]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def by_v1_media(user_id, play_count_filter, end_cursor=None):
    api_v1_url = API_V1_URL.format(user_id)
    if end_cursor:
        api_v1_url = API_V1_URL_2.format(user_id, end_cursor)
    
    try:
        r = requests.get(url=api_v1_url, headers=headers)
    except requests.RequestException as e:
        print("Request failed:", e)
        return None

    if r.status_code == 200:
        try:
            res_json = r.json()
        except ValueError as e:
            print("Failed to parse JSON:", e)
            return None

        next_page_id = res_json[1]
        num_results = len(res_json[0])
        
        media_data = []
        for item in res_json[0]:
            if item is None:
                continue
            try:
                play_count = item.get('play_count', None)
                if play_count is not None and play_count >= play_count_filter:
                    media_info = {
                        'timestamp': item.get('taken_at', None),
                        'media_type': item.get('media_type', None),
                        'caption': item.get('caption_text', None),
                        'play_count': play_count,
                        'product_type': item.get('product_type', None),
                        'comment_count': item.get('comment_count', None),
                        'like_count': item.get('like_count', None),
                        'video_duration': item.get('video_duration', None),
                        'original_sound_url': item.get('clips_metadata', {}).get('original_sound_info', {}).get('progressive_download_url', None) if item.get('clips_metadata') else None,
                        'video_url': item.get('video_url', None),
                        'thumbnail_url': download_image(item.get('thumbnail_url', None))
                    }
                    media_data.append(media_info)
            except Exception as e:
                print("Error processing item:", e)
                continue
        
        response = {
            'next_page_id': next_page_id,
            'num_results': num_results,
            'items': media_data
        }
        
        return response
    else:
        return None



def by_v2_media(user_id, page_id, play_count_filter):
    api_v2_url = API_V2_URL.format(user_id, page_id)
    try:
        print("Calling URL:- ", api_v2_url)
        t7 = time.time()
        r = requests.get(url=api_v2_url, headers=headers)
        t8 = time.time()
        print("API CALL TIME:- ",t8-t7)
    except requests.RequestException as e:
        print("Request failed:", e)
        return None

    print("by_v2_media:- ", r.status_code)
    if r.status_code == 200:
        try:
            res_json = r.json()
        except ValueError as e:
            print("Failed to parse JSON:", e)
            return None

        next_page_id = res_json.get('next_page_id')
        num_results = res_json.get('response', {}).get('num_results')
        items = res_json.get('response', {}).get('items', [])

        media_data = []
        download_threads = []

        def process_item(item):
            if item is None:
                return
            try:
                play_count = item.get('play_count', None)
                if play_count is not None and play_count >= play_count_filter:
                    media_info = {
                        'timestamp': item.get('taken_at', None),
                        'media_type': item.get('media_type', None),
                        'caption': item.get('caption', {}).get('text', None) if item.get('caption') else None,
                        'play_count': play_count,
                        'product_type': item.get('product_type', None),
                        'comment_count': item.get('comment_count', None),
                        'like_count': item.get('like_count', None),
                        'video_subtitles_uri': item.get('video_subtitles_uri', None),
                        'video_subtitles_locale': item.get('video_subtitles_locale', None),
                        'video_duration': item.get('video_duration', None),
                        'has_audio': item.get('has_audio', None),
                        'original_sound_url': item.get('clips_metadata', {}).get('original_sound_info', {}).get('progressive_download_url', None) if item.get('clips_metadata') else None,
                        'reshare_count': item.get('reshare_count', None),
                        'video_url': item.get('video_url', None),
                        'thumbnail_url': download_image(item.get('thumbnail_url', None))
                    }
                    media_data.append(media_info)
            except Exception as e:
                print("Error processing item:", e)

        t5 = time.time()
        for item in items:
            thread = threading.Thread(target=process_item, args=(item,))
            download_threads.append(thread)
            thread.start()

        for thread in download_threads:
            thread.join()
        t6 = time.time()
        print("For Loop Time:- ", t6 - t5)

        response = {
            'next_page_id': next_page_id,
            'num_results': num_results,
            'items': media_data
        }

        return response
    else:
        return None 

def fetch_reels(pk_id, page, play_count_filter):
    t3 = time.time()
    api_v2_response = by_v2_media(pk_id,page,play_count_filter)
    t4 = time.time()
    print("by_v2_media:- ",t4-t3)
    # print("api_v2_response", api_v2_response)
    if not api_v2_response:
        print("V2 Failed using V1 Now")
        if page == 1:
            end_cursor = None
        else:
            end_cursor = page
        res = by_v1_media(pk_id, play_count_filter, end_cursor)
        # print("by_v1_media", res)
        return res
    return api_v2_response

def get_id_by_username(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM usernamesandids WHERE username = ?', (username,))
    pk_id = cursor.fetchone()
    # print("pk_id:- ", pk_id)
    if pk_id:
        # print(True)
        return pk_id[2]
    url = USERNAME_API_URL.format(username)
    r = requests.get(url=url, headers=headers)
    print("API CONSUMED get_id_by_username")
    # print("STEP")
    # print(r.status_code, r.text)
    if r.status_code == 200:
        if 'UserNotFound' in r.text:
            return None
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO usernamesandids (username, unique_id) VALUES (?, ?)', (username, r.json()['pk']))
        db.commit()
        print(r.json()['pk'])
        return r.json()['pk']
    return False

def check_balance():
    r = requests.get(url=BALANCE_API_URL, headers=headers)
    if r.json['requests'] > 0:
        return True

def download_image(url):
    if url is None:
        return None
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        url_path = urlparse(url).path
        filename = hashlib.md5(url_path.encode()).hexdigest() + os.path.splitext(url_path)[1]
        image_path = os.path.join(IMAGE_FOLDER, filename)
        with open(image_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return f'/static/thumbnails/{filename}'
    except requests.RequestException as e:
        print("Failed to download image:", e)
        return None

@app.route('/api/reels', methods=['GET'])
def get_reels():
    username = request.args.get('username')
    page = request.args.get('page', 1)
    pk_id = get_id_by_username(username)
    print('PK:-', pk_id)
    if pk_id is None:
        return jsonify({'error': 'Profile not found'}), 404
    elif pk_id is False:
        return jsonify({'error': 'Something went Wrong'}), 400
    
    play_count_filter = int(request.args.get('play_count', 10000))

    try:
        t1 = time.time()
        response = fetch_reels(pk_id, page, play_count_filter)
        t2 = time.time()
        print("fetch_reels:- ",t2-t1)
    except Exception as e:
        print("Error fetching reels:", e)
        return jsonify({'error': 'Something went Wrong'}), 400
    if response is None:
        return jsonify({'error': 'Something went Wrong'}), 400
    return jsonify(response)

if __name__ == '__main__':
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)
    if not os.path.exists(AUDIO_FOLDER):
        os.makedirs(AUDIO_FOLDER)
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)
