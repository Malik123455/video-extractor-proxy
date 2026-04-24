from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import re

app = Flask(__name__)
CORS(app)

# إعدادات yt-dlp
ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
    'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',  # أفضل جودة حتى 720p
}

def extract_video_url(url):
    """استخراج رابط الفيديو باستخدام yt-dlp"""
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # إذا كان قائمة تشغيل، نأخذ أول فيديو
            if 'entries' in info:
                info = info['entries'][0]
            
            # الحصول على رابط الفيديو
            if 'url' in info:
                return info['url']
            
            # البحث عن أفضل رابط في formats
            if 'formats' in info:
                for f in info['formats']:
                    if f.get('ext') == 'mp4' and f.get('height') and f['height'] <= 720:
                        return f['url']
                return info['formats'][0]['url']
            
            return None
    except Exception as e:
        print(f"Extraction error: {e}")
        return None

@app.route('/extract', methods=['POST'])
def extract():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'}), 400
    
    video_url = extract_video_url(url)
    
    if video_url:
        return jsonify({'success': True, 'videoUrl': video_url})
    else:
        return jsonify({'success': False, 'error': 'No video found'})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
