import os
import re
import json
import random
import datetime  
import asyncio
import requests
import traceback
import subprocess  
import urllib.parse
import shutil
from bs4 import BeautifulSoup
from collections import Counter
from PIL import Image, ImageFilter, ImageStat
from concurrent.futures import ThreadPoolExecutor
import feedparser  
import edge_tts

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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        cleaned_paragraphs = []
        unwanted_phrases = ["follow", "read more", "cookies", "subscribe", "social media information", "like our page", "bgn community post", "featured in the linc", "the linc!"]
        
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if len(text) < 15 or any(k in text.lower() for k in unwanted_phrases): 
                continue
            cleaned_paragraphs.append(text)
            
        article_text = "\n\n".join(cleaned_paragraphs)
        
        embedded_article_photos = []
        for meta in soup.find_all('meta'):
            if meta.get('property') in ['og:image', 'twitter:image']:
                c = meta.get('content')
                if c and c.startswith('http') and not any(j in c.lower() for j in ['logo', 'icon', 'default', 'avatar', 'ad']): 
                    embedded_article_photos.append(c)
                    
        return article_text, list(dict.fromkeys(embedded_article_photos))
    except:
        return "", []

def group_paragraphs(paragraphs, min_words=80):
    if not paragraphs:
        return []
    
    groups = []
    temp = []
    
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        
        p_words = p.split()
        if not temp:
            temp.append(p)
        else:
            temp_word_count = len(" ".join(temp).split())
            if temp_word_count < min_words:
                temp.append(p)
            else:
                p_word_count = len(p_words)
                if p_word_count < min_words:
                    temp.append(p)
                else:
                    groups.append("\n\n".join(temp))
                    temp = [p]
    
    if temp:
        temp_word_count = len(" ".join(temp).split())
        if temp_word_count < min_words and groups:
            last_group = groups.pop()
            groups.append(last_group + "\n\n" + "\n\n".join(temp))
        else:
            groups.append("\n\n".join(temp))
            
    return groups

def get_primary_keyword_app_logic(text):
    words = re.findall(r'\b[A-Z][a-z]{3,}\b', text) 
    if len(words) < 2:
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text)
        
    stop_words = {'that', 'this', 'there', 'with', 'from', 'have', 'your', 'which', 'will', 
                  'about', 'like', 'just', 'when', 'what', 'know', 'feel', 'they', 'team', 'game', 'news', 'first', 'report', 'league', 'south'}
    filtered = [w for w in words if w.lower() not in stop_words]
    
    if len(filtered) < 2: 
        return "NBA Basketball match"
        
    most_common = Counter(filtered).most_common(2)
    keyword = f"{most_common[0][0]} {most_common[1][0]}"
    print(f"📊 [App Matching Logic] Primary Subject Keyword Extracted: '{keyword}'")
    return keyword

def search_vercel_cloud_bridge(keyword, engine="ddg"):
    vercel_endpoint = os.environ.get("VERCEL_BRIDGE_URL")
    if not vercel_endpoint:
        return []
    
    try:
        print(f"🌉 [Vercel Cloud Bridge Active] Fetching High-Res Photos via ({engine}) for: '{keyword}'...")
        url = f"{vercel_endpoint}?q={urllib.parse.quote(keyword)}&engine={engine}&source={engine}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            images = data.get("images", [])
            print(f"🎉 SUCCESS! Vercel Bridge ({engine}) delivered {len(images)} authentic player photos!")
            return images
    except Exception as e:
        print(f"Vercel Bridge ({engine}) Notice: {e}")
        
    return []

def search_bing_direct_photos(keyword, max_results=20):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36'}
        url = f"https://www.bing.com/images/async?q={urllib.parse.quote(keyword + ' NBA basketball')}&first=1&count=25"
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            urls = re.findall(r'murl&quot;:&quot;(http[^&]+)&quot;', r.text) or re.findall(r'"murl":"(http[^"]+)"', r.text)
            clean_b_links = [u for u in list(dict.fromkeys(urls)) if any(ext in u.lower() for ext in ['.jpg','.jpeg','.png'])]
            print(f"✅ Unblocked Direct Search Engine fetched: {len(clean_b_links)} direct high-res images!")
            return clean_b_links[:max_results]
    except Exception as eb:
        print(f"Direct Search Exception: {eb}")
    return []

def search_wikimedia_images(keyword, max_results=15):
    try:
        url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f"filetype:bitmap {keyword} basketball",
            "gsrlimit": max_results,
            "prop": "imageinfo",
            "iiprop": "url"
        }
        r = requests.get(url, params=params, timeout=8)
        if r.status_code == 200:
            pages = r.json().get("query", {}).get("pages", {})
            urls = []
            for p in pages.values():
                imageinfo = p.get("imageinfo")
                if imageinfo and len(imageinfo) > 0:
                    img_url = imageinfo[0].get("url")
                    if img_url and any(ext in img_url.lower() for ext in ['.jpg','.png','.jpeg']):
                        urls.append(img_url)
            return urls
    except: pass
    return []

def scrape_images_strictly_web(title, body_text, embedded_photos):
    candidates = []
    
    for hero_p in embedded_photos:
        candidates.append(hero_p)
        
    subject = get_primary_keyword_app_logic(body_text)

    # ১ম প্রায়োরিটি: ডাকডাকগো (ভারসেল ক্লাউড ব্রিজের মাধ্যমে)
    ddg_pics = search_vercel_cloud_bridge(subject, engine="ddg")
    candidates.extend(ddg_pics)

    # ২য় প্রায়োরিটি: বিং ইমেজ সার্চ (ভারসেল ক্লাউড ব্রিজের মাধ্যমে)
    if len(candidates) < 15:
        bing_pics = search_vercel_cloud_bridge(subject, engine="bing")
        candidates.extend(bing_pics)

    # ৩য় প্রায়োরিটি: উইকিমিডিয়া কমন্স (ভারসেল ক্লাউড ব্রিজের মাধ্যমে)
    if len(candidates) < 8:
        wiki_pics = search_vercel_cloud_bridge(subject, engine="wiki")
        candidates.extend(wiki_pics)

    # ডিরেক্ট সোর্স ব্যাকআপ ফিল্টার (যদি এপিআই কোনো রেসপন্স না দেয়)
    if len(candidates) < 8:
        direct_pics = search_bing_direct_photos(subject, max_results=20)
        candidates.extend(direct_pics)
    if len(candidates) < 8:
        wiki_pics = search_wikimedia_images(subject, max_results=15)
        candidates.extend(wiki_pics)

    return list(dict.fromkeys(candidates))

def filter_and_clean_downloaded_images(images_dir):
    print("🧹 [Dynamic Smart Cleaner] Filtering small dimension logos and ad visuals...")
    valid_count = 0
    all_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    for fname in all_files:
        fpath = os.path.join(images_dir, fname)
        try:
            file_size = os.path.getsize(fpath)
            if file_size < 12288:
                os.remove(fpath)
                continue
                
            with Image.open(fpath) as img:
                w, h = img.size
                
                if w < 380 or h < 280:
                    img.close()
                    os.remove(fpath)
                    continue
                    
                aspect_ratio = w / float(h)
                if aspect_ratio < 0.40 or aspect_ratio > 2.7:
                    img.close()
                    os.remove(fpath)
                    continue
                    
                if img.mode == 'RGB':
                    stat = ImageStat.Stat(img)
                    if sum(stat.stddev) < 12: 
                        img.close()
                        os.remove(fpath)
                        continue
                        
            valid_count += 1
        except Exception:
            try: os.remove(fpath)
            except: pass
            
    print(f"✨ Post-Download Cleaning Complete! Retained {valid_count} verified images.")

def process_dynamic_thumbnail(wkspace, output_path):
    all_files = []
    for root, dirs, files in os.walk(wkspace):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png')) and "images" in root:
                all_files.append(os.path.join(root, f))
                
    if not all_files: return
    
    wide_images = []
    for f in all_files:
        try:
            with Image.open(f) as iobj:
                w, h = iobj.size
                if 1.6 <= w/h <= 1.9: wide_images.append(f)
        except: pass

    try:
        if wide_images:
            Image.open(random.choice(wide_images)).convert("RGB").resize((1920,1080)).save(output_path, quality=95)
        else:
            Image.open(random.choice(all_files)).convert("RGB").resize((1920,1080)).save(output_path, quality=95)
    except: pass

def clear_temporary_workspace(ws_dir):
    try:
        for fname in ["audio.mp3", "subtitles.srt", "temp_slider.txt", "temp_output.mp4", "output_video.mp4", "thumbnail.jpg", "final_concat.txt"]:
            fpath = os.path.join(ws_dir, fname)
            if os.path.exists(fpath): os.remove(fpath)

        for name in os.listdir(ws_dir):
            path = os.path.join(ws_dir, name)
            if os.path.isdir(path):
                shutil.rmtree(path)
    except: pass

def render_segment_by_ffmpeg(clip_index, segment_duration, img_obj, output_segment_path):
    frame_count = max(int(segment_duration * 25), 10)
    
    if img_obj["type"] == "landscape":
        step_str = f"{0.15 / frame_count:.6f}"
        if clip_index % 2 == 0:
            lens_filter = f"zoompan=z='min(1.15, zoom+{step_str})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frame_count}:s=1920x1080:fps=25"
        else:
            lens_filter = f"zoompan=z='if(lte(zoom,1.0),1.15,max(1.001,zoom-{step_str}))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frame_count}:s=1920x1080:fps=25"
        
        cmd_arguments = [
            "ffmpeg", "-y", "-nostdin", "-hide_banner", "-loglevel", "error", 
            "-loop", "1", "-framerate", "25", "-i", img_obj["path"], 
            "-vf", lens_filter, "-t", f"{segment_duration:.2f}", 
            "-c:v", "libx264", "-preset", "ultrafast", 
            "-tune", "zerolatency", "-pix_fmt", "yuv420p", output_segment_path
        ]
        subprocess.run(cmd_arguments, check=True)
    else:
        bg_p = img_obj["bg_path"]
        fg_p = img_obj["fg_path"]
        
        if clip_index % 2 == 0:
            slide_filter = f"[0:v][1:v]overlay=x='(W-w)/2 - 60 + 120*(t/{segment_duration:.2f})':y=0[out]"
        else:
            slide_filter = f"[0:v][1:v]overlay=x='(W-w)/2 + 60 - 120*(t/{segment_duration:.2f})':y=0[out]"
            
        cmd_arguments = [
            "ffmpeg", "-y", "-nostdin", "-hide_banner", "-loglevel", "error", 
            "-loop", "1", "-i", bg_p, 
            "-loop", "1", "-i", fg_p, 
            "-filter_complex", slide_filter, "-map", "[out]", 
            "-t", f"{segment_duration:.2f}", "-c:v", "libx264", "-preset", "ultrafast", 
            "-tune", "zerolatency", "-pix_fmt", "yuv420p", output_segment_path
        ]
        subprocess.run(cmd_arguments, check=True)
        
    return output_segment_path

def mix_sfx_to_audio(audio_path, timestamps, sfx_folder, sfx_volume, output_audio_path):
    if not os.path.exists(sfx_folder):
        shutil.copyfile(audio_path, output_audio_path)
        return
        
    sfx_files = [os.path.join(sfx_folder, f) for f in os.listdir(sfx_folder) if f.lower().endswith(('.mp3', '.wav'))]
    if not sfx_files or len(timestamps) <= 1:
        shutil.copyfile(audio_path, output_audio_path)
        return
        
    cmd = ["ffmpeg", "-y", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", audio_path]
    filter_inputs = []
    
    valid_ts = [t for t in timestamps[1:-1] if t > 0.1]
    
    for idx, ts in enumerate(valid_ts):
        sfx = random.choice(sfx_files)
        cmd.extend(["-i", sfx])
        ms = int(ts * 1000)
        filter_inputs.append(f"[{idx+1}:a]volume={sfx_volume:.2f},adelay=delays={ms}:all=1[sfx{idx}]")
        
    if filter_inputs:
        mix_labels = "".join(f"[sfx{idx}]" for idx in range(len(valid_ts)))
        filter_complex = ";".join(filter_inputs) + f";[0:a]{mix_labels}amix=inputs={len(valid_ts)+1}:normalize=0[out]"
        cmd.extend(["-filter_complex", filter_complex, "-map", "[out]"])
    else:
        cmd.extend(["-c:a", "copy"])
        
    cmd.append(output_audio_path)
    subprocess.run(cmd, check=True)

def get_sentence_timestamps(srt_path):
    if not os.path.exists(srt_path): return []
    with open(srt_path, "r", encoding="utf-8") as srt_reader: content = srt_reader.read()
    regex_clock = re.compile(r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) -->')
    second_values = [int(p[0])*3600 + int(p[1])*60 + int(p[2]) + int(p[3])/1000.0 for p in regex_clock.findall(content)]
    return sorted(list(set(second_values)))

def safe_upload_to_youtube(video_full_path, thumb_full_path, title, video_description):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    print("\nProcessing backend google security auth directly with secrets variables provided in workflow ...")
    authorized_keys = Credentials(
        token=None, refresh_token=os.environ.get('YOUTUBE_REFRESH_TOKEN'), 
        token_uri="https://oauth2.googleapis.com/token", 
        client_id=os.environ.get('YOUTUBE_CLIENT_ID'), 
        client_secret=os.environ.get('YOUTUBE_CLIENT_SECRET')
    )
    google_cloud_instance = build("youtube", "v3", credentials=authorized_keys)

    body = {
        'snippet': {'title': title[:98], 'description': video_description, 'categoryId': '17'}, 
        'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
    }
    target_job = google_cloud_instance.videos().insert(
        part="snippet,status", 
        body=body, 
        media_body=MediaFileUpload(video_full_path, resumable=True, mimetype="video/mp4")
    )
    completed_exec = target_job.execute()
    newly_deployed_id = completed_exec.get('id')
    
    print(f"🚀 Mission uploaded successfully! ID: {newly_deployed_id}")

    if os.path.exists(thumb_full_path):
        try:
            google_cloud_instance.thumbnails().set(videoId=newly_deployed_id, media_body=MediaFileUpload(thumb_full_path)).execute()
            print("Associated cover photo added effectively.\n")
        except Exception as e:
            print(f"Thumbnail upload failed: {e}")

def hex_to_ass_color(hex_str, opacity_float=1.0):
    hex_str = hex_str.lstrip('#')
    red, green, blue = hex_str[0:2], hex_str[2:4], hex_str[4:6]
    alpha_hex = int((1.0 - opacity_float) * 255)
    return f"&H{alpha_hex:02X}{blue}{green}{red}"

def get_audio_duration(audio_path):
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", os.path.abspath(audio_path)], capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except: return 0.0

def escape_subtitles_path(path_str):
    escaped = os.path.abspath(path_str).replace("\\", "/")
    if ":" in escaped:
        drive, rest = escaped.split(":", 1)
        escaped = f"{drive}\\:{rest}"
    return escaped

def process_primary_automation_loop():
    if not os.path.exists("config.json"): return
    with open("config.json", "r", encoding="utf-8") as cf: user_settings = json.load(cf)

    if not os.path.exists("processed_urls.txt"):
        with open("processed_urls.txt", "w", encoding="utf-8") as cx: cx.write("")
    with open("processed_urls.txt", "r", encoding="utf-8") as pc_rd: done_records = [l.strip() for l in pc_rd if l.strip()]

    collected_feeds, dt_utcnow = [], datetime.datetime.now(datetime.timezone.utc)
    target_urls_parsed = [x.strip() for x in user_settings["rss_urls"].split(",") if x.strip()]
    
    for rss_path in target_urls_parsed:
        try:
            p_feed = feedparser.parse(rss_path)
            for list_id, p_obj in enumerate(p_feed.entries): 
                p_obj.rss_hierarchy = list_id
                collected_feeds.append(p_obj)
        except: pass

    collected_feeds.sort(key=lambda sxy: getattr(sxy, 'published_parsed', None) or getattr(sxy, 'updated_parsed', None) or (0,), reverse=False)

    filter_excluded_title = [xtr.strip().lower() for xtr in user_settings["exclude_title_keywords"].split(",") if xtr.strip()]
    time_limit_scale_hrs = float(user_settings.get("max_age_hours", 24.0))

    final_action_items = []
    for fitem in collected_feeds:
        a_title, a_link = fitem.get("title", ""), fitem.get("link", "")
        if a_link in done_records: 
            continue
            
        skip_article = False
        if filter_excluded_title:
            for spam_word in filter_excluded_title:
                if spam_word in a_title.lower() or spam_word in a_link.lower():
                    skip_article = True
                    break
        if skip_article: continue

        draft_priority = getattr(fitem, 'rss_hierarchy', 99) < 3
        actual_calendar_data = getattr(fitem, "published_parsed", getattr(fitem, "updated_parsed", None))
        
        if not actual_calendar_data and not draft_priority: continue
        diff_tracker = (dt_utcnow - datetime.datetime(*actual_calendar_data[:6], tzinfo=datetime.timezone.utc)).total_seconds() / 3600.0 if actual_calendar_data else 0.0
        if time_limit_scale_hrs < 9999.0 and not draft_priority and diff_tracker > time_limit_scale_hrs: 
            continue
            
        final_action_items.append(fitem)

    if not final_action_items: 
        print("Completed database scraping securely. Scheduled task waiting.")
        return

    print(f"📊 Target Items Found: Processing ALL {len(final_action_items)} matching news articles sequentially for [{time_limit_scale_hrs}h]...")

    wkspace = os.path.abspath(os.path.join(os.getcwd(), 'workspace'))
    blocked_inside_words = [bk.strip().lower() for bk in user_settings["exclude_body_keywords"].split(",") if bk.strip()]
    require_wc = user_settings.get("min_word_count", 150)
    sfx_volume = user_settings.get("sfx_volume", 0.3)

    for track_loop_counter, finalizer_target in enumerate(final_action_items):
        vid_ttl, lns = finalizer_target.get("title", ""), finalizer_target.get("link", "")
        print(f"\n=========================================================================")
        print(f"[{track_loop_counter+1}/{len(final_action_items)}] Processing Target Article: >> {vid_ttl}")
        print(f"=========================================================================")

        text_chunk_collected, embedded_page_photos = scrape_article(lns)
        content_word_size = len(text_chunk_collected.split())
        
        if content_word_size < require_wc:
            with open("processed_urls.txt", "a") as fwpt: fwpt.write(lns+"\n"); continue
            
        body_trap = False
        if blocked_inside_words:
            for sw_in_b in blocked_inside_words:
                if sw_in_b in text_chunk_collected.lower():
                    body_trap = True; break
        if body_trap:
            with open("processed_urls.txt", "a") as bwf: bwf.write(lns+"\n"); continue

        clear_temporary_workspace(wkspace)

        raw_paras = text_chunk_collected.split("\n\n")
        paragraph_groups =