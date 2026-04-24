from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import json
import requests
from bs4 import BeautifulSoup
import yt_dlp as youtube_dl

app = Flask(__name__)
CORS(app)

# إعدادات yt-dlp لاستخراج روابط الفيديو
ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
    'force_generic_extractor': False,
}

def extract_youtube_url(url):
    """استخراج رابط الفيديو من يوتيوب باستخدام yt-dlp"""
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                # قائمة تشغيل - نأخذ أول فيديو
                info = info['entries'][0]
            
            # الحصول على أفضل رابط فيديو متاح
            if 'formats' in info:
                # نفضل mp4 مع أعلى جودة
                for f in info['formats']:
                    if f.get('ext') == 'mp4' and f.get('height') and f['height'] <= 720:
                        return f['url']
                # لو ما لقينا، نرجع أول رابط mp4
                for f in info['formats']:
                    if f.get('ext') == 'mp4':
                        return f['url']
            
            # لو ما لقينا رابط mp4، نرجع رابط m3u8
            if 'url' in info:
                return info['url']
        
        return None
    except Exception as e:
        print(f"YouTube extraction error: {e}")
        return None

def extract_tiktok_url(url):
    """استخراج رابط الفيديو من تيك توك"""
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'url' in info:
                return info['url']
            if 'formats' in info and len(info['formats']) > 0:
                return info['formats'][0]['url']
        return None
    except Exception as e:
        print(f"TikTok extraction error: {e}")
        return None

def extract_generic_url(url):
    """محاولة استخراج الفيديو من مواقع عامة"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        html = response.text
        
        # البحث عن روابط الفيديو في الصفحة
        patterns = [
            r'https?://[^\s"\']+\.(?:mp4|m3u8|mkv|avi|mov)[^\s"\']*',
            r'"videoUrl":"([^"]+)"',
            r"'videoUrl':'([^']+)'",
            r'src="([^"]+\.mp4)"',
            r'content="([^"]+\.mp4)"',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html)
            if matches:
                return matches[0]
        
        # استخدام BeautifulSoup للبحث
        soup = BeautifulSoup(html, 'html.parser')
        video_tags = soup.find_all('video')
        for video in video_tags:
            src = video.get('src')
            if src and src.startswith('http'):
                return src
        
        return None
    except Exception as e:
        print(f"Generic extraction error: {e}")
        return None

def get_platform(url):
    """تحديد نوع الموقع من الرابط"""
    url_lower = url.lower()
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    elif 'tiktok.com' in url_lower:
        return 'tiktok'
    elif 'facebook.com' in url_lower or 'fb.watch' in url_lower:
        return 'facebook'
    elif 'instagram.com' in url_lower:
        return 'instagram'
    elif 'twitter.com' in url_lower or 'x.com' in url_lower:
        return 'twitter'
    else:
        return 'generic'

@app.route('/extract', methods=['POST'])
def extract_video():
    data = request.get_json()
    page_url = data.get('url')
    
    if not page_url:
        return jsonify({'success': False, 'error': 'No URL provided'}), 400
    
    platform = get_platform(page_url)
    video_url = None
    
    try:
        if platform == 'youtube':
            video_url = extract_youtube_url(page_url)
        elif platform == 'tiktok':
            video_url = extract_tiktok_url(page_url)
        else:
            video_url = extract_generic_url(page_url)
        
        if video_url:
            return jsonify({
                'success': True, 
                'videoUrl': video_url,
                'platform': platform
            })
        else:
            return jsonify({
                'success': False, 
                'error': f'No video found on {platform}',
                'platform': platform
            })
    
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e),
            'platform': platform
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Proxy server is running'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
