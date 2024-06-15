from flask import Flask, jsonify, request, render_template, send_from_directory
import instaloader
import os
import time

app = Flask(__name__, template_folder='templates', static_url_path='/static')

L = instaloader.Instaloader(sleep=True)
# L.load_session_from_file("test_shack_labs","session")

@app.route('/')
def index():
    return render_template('index.html')

def fetch_post_details(post, username):
    thumbnail_filename = f"{username}_{post.mediaid}.jpg"
    thumbnail_path = os.path.join(app.root_path, 'static', 'thumbnails', thumbnail_filename)
    if not os.path.exists(thumbnail_path):
        post.download_url = post.url
        L.download_pic(thumbnail_path, post.url, post.date)
    return {
        'caption': post.caption,
        'thumbnail': f'/static/thumbnails/{thumbnail_filename}.jpg',
        'date': post.date
    }

def fetch_reels(username, start_index, per_page):
    posts = []
    profile = instaloader.Profile.from_username(L.context, username)
    for index, post in enumerate(profile.get_posts()):
        if post.typename == "GraphVideo" and post.is_video:
            if index >= start_index:
                posts.append(post)
                if len(posts) == per_page:
                    break
    return [fetch_post_details(post, username) for post in posts]

@app.route('/api/reels', methods=['GET'])
def get_reels():
    username = request.args.get('username')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 5))  # Number of reels per page
    start_index = (page - 1) * per_page

    try:
        posts = fetch_reels(username, start_index, per_page)
    except instaloader.exceptions.ProfileNotExistsException:
        return jsonify({'error': 'Profile not found'}), 404

    return jsonify(posts)

@app.route('/static/thumbnails/<path:filename>')
def serve_thumbnail(filename):
    return send_from_directory('static/thumbnails', filename)

if __name__ == '__main__':
    if not os.path.exists(os.path.join(app.root_path, 'static', 'thumbnails')):
        os.makedirs(os.path.join(app.root_path, 'static', 'thumbnails'))
    print("Current working directory:", os.getcwd())
    app.run(debug=True)
