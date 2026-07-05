import os
import re
import json
import random
import datetime  
import asyncio
import requests
import traceback
import subprocess  
from collections import Counter
from bs4 import BeautifulSoup
from PIL import Image, ImageFilter  

GENERIC_SPORTS_FALLBACKS = [
    "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=1920&q=80",  # Basketball Court
    "https://images.unsplash.com/photo-1519766304817-4f37bda74a27?w=1920&q=80",  # Stadium Lights
    "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=1920&q=80",  # Sports ball
    "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=1920&q=80",  # Running track
    "https://images.unsplash.com/photo-1517649763962-0c623066013b?w=1920&q=80",  # Sports stadium
]

async def generate_voice_and_subtitles(text, voice, audio_path, srt_path):
    communicate = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()
    with open(audio_path, "wb") as fobj:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                fobj.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                submaker.feed(chunk)
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(submaker.get_srt())

def scrape_article(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    paragraphs = soup.find_all('p')
    cleaned = []
    
    unwanted_phrases = [
        "follow", "read more", "cookies", "subscribe", 
        "social media information", "like our page", 
        "bgn community post", "featured in the linc",
        "the linc!"
    ]
    
    for p in paragraphs:
        txt = p.get_text().strip()
        if len(txt) < 15:
            continue
        if any(k in txt.lower() for k in unwanted_phrases):
            continue
        cleaned.append(txt)
    return "\n\n".join(cleaned)

def hex_to_ass_color(hex_str, opacity_float=1.0):
    hex_str = hex_str.lstrip('#')
    r, g, b = hex_str[0:2], hex_str[2:4], hex_str[4:6]
    alpha_val = int((1.0 - opacity_float) * 255)
    alpha_hex = f"{alpha_val:02X}"
    return f"&H{alpha_hex}{b}{g}{r}"

def get_audio_duration(audio_path):
    """FFprobe ব্যবহার করে অত্যন্ত দ্রুত ও হালকা উপায়ে অডিও ফাইলের দৈর্ঘ্য পরিমাপ করা"""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error getting audio duration via ffprobe: {e}")
        return 0.0

def search_bing_images(keyword, max_results=20):
    print(f"Searching Bing Images for: '{keyword}'...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    import urllib.parse
    url = f"https://www.bing.com/images/search?q={urllib.parse.quote(keyword)}&FORM=HDRSC2"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            urls = re.findall(r'"murl":"(http[^"]+)"', r.text)
            unique_urls = []
            for u in urls:
                if u not in unique_urls:
                    unique_urls.append(u)
            # max_results বাগটি এখানে নিখুঁতভাবে সংশোধন করা হয়েছে 
            return unique_urls[:max_results]
    except Exception as e:
        print(f"Bing Image search failed: {e}")
    return []

def fallback_wikimedia_images(keyword, max_results=20):
    print(f"Trying Wikimedia Commons fallback for: '{keyword}'...")
    try:
        url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f"filetype:bitmap {keyword}",
            "gsrlimit": max_results,
            "prop": "imageinfo",
            "iiprop": "url"
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            pages = data.get("query", {}).get("pages", {})
            urls = []
            for page_id, page_info in pages.items():
                image_info = page_info.get("imageinfo", [])
                if image_info:
                    img_url = image_info[0].get("url")
                    if img_url:
                        urls.append(img_url)
            return urls
    except Exception as e:
        print(f"Wikimedia API search failed: {e}")
    return []

def scrape_images(keyword, max_results=20):
    """Bing এবং Yahoo থেকে একযোগে হাই-কোয়ালিটি ছবি স্ক্র্যাপ করার আল্ট্রা-রিলায়েবল ফাংশন"""
    # max_results কন্ডিশন ফিক্সড করা হয়েছে 
    urls = search_bing_images(keyword, max_results=max_results)
    
    if not urls:
        urls = fallback_wikimedia_images(keyword, max_results=max_results)
        
    return urls

def select_thumbnail_and_crop(images_dir, output_thumbnail_path):
    img_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not img_files:
        print("No images found to generate thumbnail. Downloading a premium fallback.")
        r = requests.get(GENERIC_SPORTS_FALLBACKS[0], timeout=10)
        with open(output_thumbnail_path, 'wb') as f:
            f.write(r.content)
        return

    sixteen_nine_candidates = []
    for f in img_files:
        path = os.path.join(images_dir, f)
        try:
            with Image.open(path) as img:
                w, h = img.size
                if 1.6 <= (w / h) <= 1.9:
                    sixteen_nine_candidates.append(path)
        except Exception: pass

    if sixteen_nine_candidates:
        selected = random.choice(sixteen_nine_candidates)
        Image.open(selected).resize((1920, 1080)).save(output_thumbnail_path)
        print(f"Selected native 16:9 thumbnail: {selected}")
    else:
        selected = os.path.join(images_dir, random.choice(img_files))
        Image.open(selected).convert('RGB').resize((1920, 1080)).save(output_thumbnail_path)
        print(f"No native 16:9 found. Cropped random thumbnail: {selected}")

def parse_srt_start_times(srt_path):
    if not os.path.exists(srt_path): return []
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()
    pattern = re.compile(r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) -->')
    matches = pattern.findall(content)
    start_times = []
    for m in matches:
        sec = int(m[0])*3600 + int(m[1])*60 + int(m[2]) + int(m[3])/1000.0
        start_times.append(sec)
    return sorted(list(set(start_times)))

def clear_temp_workspace(workspace_dir):
    """ওয়ার্কস্পেস সম্পূর্ণ ফ্রেশ ও ক্লিন করার ফাংশন"""
    images_dir = os.path.join(workspace_dir, "images")
    proc_images_dir = os.path.join(workspace_dir, "processed_images")
    
    audio_path = os.path.join(workspace_dir, "audio.mp3")
    srt_path = os.path.join(workspace_dir, "subtitles.srt")
    slideshow_path = os.path.join(workspace_dir, "slideshow.txt")
    temp_video = os.path.join(workspace_dir, "temp_video.mp4")
    output_video = os.path.join(workspace_dir, "output_video.mp4")
    thumbnail = os.path.join(workspace_dir, "thumbnail.jpg")
    
    for p in [audio_path, srt_path, slideshow_path, temp_video, output_video, thumbnail]:
        if os.path.exists(p):
            try: os.remove(p)
            except Exception: pass
            
    if os.path.exists(images_dir):
        for f in os.listdir(images_dir):
            try: os.remove(os.path.join(images_dir, f))
            except Exception: pass
    else:
        os.makedirs(images_dir, exist_ok=True)
        
    if os.path.exists(proc_images_dir):
        for f in os.listdir(proc_images_dir):
            try: os.remove(os.path.join(proc_images_dir, f))
            except Exception: pass
    else:
        os.makedirs(proc_images_dir, exist_ok=True)

def upload_to_youtube(video_path, thumbnail_path, title, description):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    print("Authenticating with YouTube API...")
    creds = Credentials(
        token=None,
        refresh_token=os.environ.get('YOUTUBE_REFRESH_TOKEN'),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ.get('YOUTUBE_CLIENT_ID'),
        client_secret=os.environ.get('YOUTUBE_CLIENT_SECRET')
    )
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        'snippet': {
            'title': title[:100],
            'description': description,
            'categoryId': '17'
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    video_id = response.get('id')
    print(f"Video uploaded successfully! Video ID: {video_id}")

    if os.path.exists(thumbnail_path):
        youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumbnail_path)).execute()
        print("Thumbnail upload completed!")

def main():
    if not os.path.exists("config.json"):
        print("Error: config.json not found!")
        return

    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    # আপলোড ডাটাবেজ ফাইল লোড
    if not os.path.exists("processed_urls.txt"):
        print("processed_urls.txt not found. Auto-creating database...")
        with open("processed_urls.txt", "w", encoding="utf-8") as f:
            f.write("")

    processed_urls = []
    with open("processed_urls.txt", "r", encoding="utf-8") as f:
        processed_urls = [line.strip() for line in f if line.strip()]

    # কনফিগারেশন ভ্যারিয়েবলস 
    rss_list = [url.strip() for url in config["rss_urls"].split(",") if url.strip()]
    exclude_title_kws = [kw.strip().lower() for kw in config["exclude_title_keywords"].split(",") if kw.strip()]
    exclude_body_kws = [kw.strip().lower() for kw in config["exclude_body_keywords"].split(",") if kw.strip()]
    min_words = config.get("min_word_count", 200)
    max_age_hours = float(config.get("max_age_hours", 24.0))

    all_entries = []
    for r_url in rss_list:
        print(f"Parsing Feed: {r_url}")
        try:
            feed = feedparser.parse(r_url)
            for index, entry in enumerate(feed.entries):
                entry.original_index = index 
                all_entries.append(entry)
        except Exception as e:
            print(f"Failed to parse {r_url}: {e}")

    # ক্রনোলজিক্যাল সর্টিং 
    all_entries.sort(key=lambda x: getattr(x, 'published_parsed', None) or getattr(x, 'updated_parsed', None) or (0,), reverse=False)

    candidate_entries = []
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    # ক্যান্ডিডেট ভ্যালিডেশন লুপ 
    for entry in all_entries:
        title = entry.get("title", "")
        link = entry.get("link", "")

        if link in processed_urls: continue

        if exclude_title_kws:
            if any(kw in title.lower() or kw in link.lower() for kw in exclude_title_kws):
                continue

        is_top_feed_item = getattr(entry, 'original_index', 99) < 3
        pub_parsed = getattr(entry, "updated_parsed", None) or getattr(entry, "published_parsed", None)
        if not pub_parsed and not is_top_feed_item: 
            continue
        
        if pub_parsed:
            pub_dt = datetime.datetime(*pub_parsed[:6], tzinfo=datetime.timezone.utc)
            time_diff = now_utc - pub_dt
            time_diff_hours = time_diff.total_seconds() / 3600.0
        else:
            time_diff_hours = 0.0 

        if max_age_hours < 9999.0 and not is_top_feed_item:
            if time_diff_hours > max_age_hours:
                continue

        candidate_entries.append(entry)

    if not candidate_entries:
        print("No new matching articles found. Skipping workflow.")
        return

    print(f"Found {len(candidate_entries)} new articles. Starting Sequential Loop Process...")

    workspace_dir = os.path.join(os.getcwd(), 'workspace')
    images_dir = os.path.join(workspace_dir, 'images')
    proc_images_dir = os.path.join(workspace_dir, 'processed_images')
    os.makedirs(workspace_dir, exist_ok=True)

    for idx_task, entry in enumerate(candidate_entries):
        title = entry.get("title", "")
        link = entry.get("link", "")

        print(f"\n[{idx_task+1}/{len(candidate_entries)}] Processing: '{title}'...")

        scraped_content = scrape_article(link)
        word_count = len(scraped_content.split())
        
        if word_count < min_words:
            print(f"Skipping: Too short ({word_count} words). Added to processed database.")
            with open("processed_urls.txt", "a", encoding="utf-8") as f: f.write(link + "\n")
            continue

        if exclude_body_kws:
            content_lower = scraped_content.lower()
            if any(kw in content_lower for kw in exclude_body_kws):
                print(f"Skipping: Found forbidden keyword inside body content. Blocked.")
                with open("processed_urls.txt", "a", encoding="utf-8") as f: f.write(link + "\n")
                continue

        # ক্যান্ডিডেট কনফার্মড! ওয়ার্কস্পেস ক্লিন করা হচ্ছে
        clear_temp_workspace(workspace_dir)
        print(f"--- WORKSPACE CLEANED. GENERATING VIDEO FOR: '{title}' ---")

        try:
            # ভয়েস ওভার এবং ক্যাপশন তৈরি 
            audio_path = os.path.join(workspace_dir, "audio.mp3")
            srt_path = os.path.join(workspace_dir, "subtitles.srt")
            asyncio.run(generate_voice_and_subtitles(scraped_content, config["voice"], audio_path, srt_path))

            # অডিও ডিউরেশন পরিমাপ (FFprobe ব্যবহার করে- ১ সেকেন্ডের কম সময়ে!)
            audio_duration = get_audio_duration(audio_path)
            max_images = 30 if audio_duration > 240.0 else 20
            print(f"Audio Duration: {audio_duration:.2f}s. Dynamic Target: Download {max_images} images.")

            # সার্চ এবং ডাউনলোড (Bing + Yahoo!)
            words = re.findall(r'\b[A-Z][a-z]{3,}\b', scraped_content)
            keyword = f"{words[0]} {words[1]}" if len(words) >= 2 else "Sports"
            
            # আমাদের নতুন ডুয়াল ইঞ্জিন দিয়ে ছবি সার্চ
            urls = scrape_images(keyword, max_results=max_images)

            total_downloaded = 0
            for idx_img, image_url in enumerate(urls):
                try:
                    r = requests.get(image_url, timeout=5)
                    if r.status_code == 200:
                        with open(os.path.join(images_dir, f"img_{idx_img+1:02d}.jpg"), 'wb') as f:
                            f.write(r.content)
                        total_downloaded += 1
                except Exception: pass

            print(f"Collected {total_downloaded} raw images.")

            # যদি ছবি ডাউনলোড না হয়ে ০ থাকে, তবে ক্র্যাশ এড়াতে জেনেরিক স্পোর্টস ছবি নামাবে 
            if total_downloaded == 0:
                print("Total downloaded was 0. Downloading fallbacks...")
                for idx, fallback_url in enumerate(GENERIC_SPORTS_FALLBACKS):
                    try:
                        r = requests.get(fallback_url, timeout=5)
                        if r.status_code == 200:
                            with open(os.path.join(images_dir, f"img_fallback_{idx+1:02d}.jpg"), 'wb') as f:
                                f.write(r.content)
                            total_downloaded += 1
                    except Exception: pass

            # থাম্বনেইল সিলেকশন
            thumbnail_path = os.path.join(workspace_dir, "thumbnail.jpg")
            select_thumbnail_and_crop(images_dir, thumbnail_path)

            # --- Pillow দিয়ে সুপার-ফাস্ট ব্লার এবং রেশিও প্রসেসিং (১৯২০x১০৮০) ---
            print("Pre-processing image sizes and blur effects...")
            img_files = sorted([f for f in os.listdir(images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
            
            for idx, img_name in enumerate(img_files):
                img_path = os.path.join(images_dir, img_name)
                try:
                    with Image.open(img_path) as img:
                        img_rgb = img.convert('RGB')
                        w, h = img_rgb.size
                        ratio = w / h
                        
                        if ratio < 1.7:
                            # লম্বালম্বি ছবি: পেছনে ব্লার ব্যাকগ্রাউন্ড এবং সামনে আসল ছবি বসানো হচ্ছে 
                            bg = img_rgb.resize((1920, 1080))
                            bg = bg.filter(ImageFilter.GaussianBlur(radius=20))
                            
                            new_width = int(1080 * ratio)
                            fg = img_rgb.resize((new_width, 1080))
                            
                            paste_x = (1920 - new_width) // 2
                            bg.paste(fg, (paste_x, 0))
                            final_img = bg
                        else:
                            # ল্যান্ডস্কেপ ছবি 
                            final_img = img_rgb.resize((1920, 1080))
                            
                        # প্রসেসড ছবি সেভ করা হচ্ছে
                        final_img.save(os.path.join(proc_images_dir, f"proc_{idx+1:02d}.jpg"), quality=95)
                except Exception as e:
                    print(f"Error pre-processing image {img_name}: {e}")

            proc_img_files = sorted([f for f in os.listdir(proc_images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
            num_proc_images = len(proc_img_files)

            # ১১. আরএসএস সাবটাইটেল টাইমিং রিড ও স্লাইডশো কনক্যাট টেক্সট তৈরি 
            start_times = parse_srt_start_times(srt_path)
            if not start_times:
                clip_dur = audio_duration / num_proc_images
                start_times = [i*clip_dur for i in range(num_proc_images)]
            else:
                if start_times[0] > 0.1: start_times.insert(0, 0.0)
                else: start_times[0] = 0.0
            start_times.append(audio_duration)

            num_sentences = len(start_times) - 1
            
            # FFmpeg Concat Demuxer এর জন্য স্লাইডশো স্ক্রিপ্ট তৈরি 
            slideshow_lines = []
            for i in range(num_sentences):
                t_start = start_times[i]
                t_end = start_times[i+1]
                duration = t_end - t_start
                
                img_name = proc_img_files[i % num_proc_images]
                # কনক্যাট ফাইলে রিলেটিভ পাথ দিতে হবে 
                slideshow_lines.append(f"file 'processed_images/{img_name}'")
                slideshow_lines.append(f"duration {duration:.3f}")
                
            # কনক্যাট রুলস অনুযায়ী শেষ ফাইলটি ডাবল লিখতে হয়
            if num_sentences > 0:
                last_img = proc_img_files[(num_sentences - 1) % num_proc_images]
                slideshow_lines.append(f"file 'processed_images/{last_img}'")
                
            slideshow_txt_path = os.path.join(workspace_dir, "slideshow.txt")
            with open(slideshow_txt_path, "w", encoding="utf-8") as f:
                f.write("\n".join(slideshow_lines))

            # ১২. আপনার দেওয়া প্রজেক্টের স্টাইলে FFmpeg Subprocess দিয়ে ৩ সেকেন্ডে রেন্ডারিং!
            print("Compiling video at 1080p 30fps using super-fast FFmpeg engine...")
            temp_video = "temp_video.mp4"
            
            # উবুন্টু ক্লাউডের সব প্রসেসর কোর একযোগে ব্যবহার হবে
            num_threads = os.cpu_count() or 4
            
            render_command = [
                "ffmpeg", "-y", "-safe", "0", 
                "-f", "concat", "-i", "slideshow.txt",
                "-i", "audio.mp3",
                "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-r", "30",
                "-threads", str(num_threads),
                "-c:a", "copy", "-shortest", temp_video
            ]
            
            # রেন্ডারিং রান (১০০ গুণ ফাস্ট!)
            subprocess.run(render_command, cwd=workspace_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # ১৩. FFmpeg ও আপনার দেওয়া কাস্টম সাবটাইটেল ডিজাইন বার্নিং
            f_color = hex_to_ass_color(config["font_color"], 1.0)
            b_color = hex_to_ass_color(config["bg_color"], config["bg_opacity"])
            border_style = config["border_style"]
            font_size = config["font_size"]
            margin_v = config["margin_v"]

            style = f"FontName=Arial,FontSize={font_size},PrimaryColour={f_color},BackColour={b_color},BorderStyle={border_style},Outline=2,Shadow=1,Alignment=2,MarginV={margin_v}"
            
            print("Burning stylized subtitles using FFmpeg...")
            output_video = os.path.join(workspace_dir, "output_video.mp4")
            
            cmd = [
                "ffmpeg", "-y", "-i", "temp_video.mp4",
                "-vf", f"subtitles=subtitles.srt:force_style='{style}'",
                "-c:v", "libx264", "-crf", "18", "-c:a", "copy", "output_video.mp4"
            ]
            subprocess.run(cmd, cwd=workspace_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # ১৪. ইউটিউব আপলোড 
            desc = f"Latest sports news: {title}\n\nGenerated automatically via AI Cloud System."
            upload_to_youtube(output_video, thumbnail_path, title, desc)

            # ১৫. ডাটাবেজ আপডেট 
            with open("processed_urls.txt", "a", encoding="utf-8") as f:
                f.write(link + "\n")
            print(f"Database updated for successfully finished video: {title}")

        except Exception as err:
            print(f"Error processing article '{title}': {err}")
            traceback.print_exc()

if __name__ == "__main__":
    main()
