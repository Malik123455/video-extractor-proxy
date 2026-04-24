from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

@app.route('/extract', methods=['POST'])
def extract_video():
    data = request.get_json()
    page_url = data.get('url')
    
    if not page_url:
        return jsonify({'error': 'No URL provided'}), 400
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(page_url, headers=headers, timeout=30)
        html = response.text
        
        # البحث عن روابط الفيديو
        video_urls = re.findall(r'https?://[^\s"\']+\.(?:mp4|m3u8|mkv|avi|mov)[^\s"\']*', html)
        
        if video_urls:
            return jsonify({'success': True, 'videoUrl': video_urls[0]})
        
        soup = BeautifulSoup(html, 'html.parser')
        video_tag = soup.find('video')
        if video_tag and video_tag.get('src'):
            return jsonify({'success': True, 'videoUrl': video_tag['src']})
        
        return jsonify({'success': False, 'error': 'No video found'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)