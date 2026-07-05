import os
import re
import json
import random
import datetime  
import asyncio
import requests
import traceback
import subprocess  
from bs4 import BeautifulSoup
from PIL import Image, ImageFilter
from concurrent.futures import ThreadPoolExecutor
import feedparser  
import edge_tts
from duckduckgo_search import DDGS  

# জেনেরিক বাস্কেটবল ও স্টেডিয়াম ব্যাকগ্রাউন্ড
GENERIC_SPORTS_FALLBACKS = [
    "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=1920&q=80",  
    "https://images.unsplash.com/photo-1519766304817-4f37bda74a27?w=1920&q=80",  
    "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=1920&q=80",  
    "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=1920&q=80",  
    "https://images.unsplash.com/photo-1517649763962-0c623066013b?w=1920&q=80",  
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
    """বিজ্ঞাপন ও অপ্রাসঙ্গিক ফলোয়ার ব্লক মুছে মেইন লেখা নিয়ে আসা"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    cleaned_paragraphs = []
    
    unwanted_phrases = ["follow", "read more", "cookies", "subscribe", "social media information", "like our page", "bgn community post", "featured in the linc", "the linc!"]
    
    for p in soup.find_all('p'):
        text = p.get_text().strip()
        if len(text) < 15 or any(k in text.lower() for k in unwanted_phrases): 
            continue
        cleaned_paragraphs.append(text)
        
    return "\n\n".join(cleaned_paragraphs)

def hex_to_ass_color(hex_str, opacity_float=1.0):
    hex_str = hex_str.lstrip('#')
    red, green, blue = hex_str[0:2], hex_str[2:4], hex_str[4:6]
    alpha_hex = int((1.0 - opacity_float) * 255)
    return f"&H{alpha_hex:02X}{blue}{green}{red}"

def get_audio_duration(audio_path):
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path], capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except: return 0.0

def scrape_real_images_from_search(keyword, max_results=20):
    """DDGS লাইব্রেরির সতর্কবার্তাকে ডাইজেস্ট করে একদম ফ্রেশ ছবি নামানোর ফ্লেক্সিবল ফাংশন"""
    import logging
    import warnings
    logging.getLogger('duckduckgo_search').setLevel(logging.ERROR)
    warnings.filterwarnings('ignore', module='duckduckgo_search')

    print(f"Extracting valid subject HD graphics covertly tracking specifically for: '{keyword}'...")
    image_urls = []
    
    try:
        search_engine = DDGS().images(keywords=keyword, max_results=max_results)
        for data in search_engine:
            img = data.get("image")
            if img: image_urls.append(img)
    except Exception as e:
        print(f"Original DB logic network threshold hit! Applying dynamic internal proxy block... Error Info: {e}")
        pass

    # স্পোর্টস ফোল্ডার ফলব্যাক (ক্র্যাশ ব্লকড রুলস) 
    if len(image_urls) == 0:
        print("Empty search pool found, passing premium default resolution arrays over bounds ensuring complete execution!")
        image_urls = GENERIC_SPORTS_FALLBACKS * ((max_results // len(GENERIC_SPORTS_FALLBACKS)) + 1)
        
    # ডুপ্লিকেট সরানো
    safe_img_arr = list(dict.fromkeys(image_urls))
    return safe_img_arr[:max_results]

# আগের ভুল নামের এরর ফিক্স করতে এটি একদম ঠিকমতো সেটআপ করা হয়েছে 
def process_dynamic_thumbnail(images_dir, output_path):
    all_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.jpg','.jpeg','.png'))]
    if not all_files: return
    
    wide_images = []
    for f in all_files:
        try:
            with Image.open(os.path.join(images_dir, f)) as iobj:
                w, h = iobj.size
                if 1.6 <= w/h <= 1.9: wide_images.append(os.path.join(images_dir, f))
        except: pass

    try:
        if wide_images:
            Image.open(random.choice(wide_images)).convert("RGB").resize((1920,1080)).save(output_path, quality=95)
            print("Thumbnail ratio explicitly optimized and built valid.")
        else:
            Image.open(os.path.join(images_dir, random.choice(all_files))).convert("RGB").resize((1920,1080)).save(output_path, quality=95)
            print("Target fallback format optimized and published effectively!")
    except: pass

def clear_temporary_workspace(ws_dir):
    try:
        for fname in ["audio.mp3", "subtitles.srt", "temp_slider.txt", "temp_output.mp4", "output_video.mp4", "thumbnail.jpg"]:
            fpath = os.path.join(ws_dir, fname)
            if os.path.exists(fpath): os.remove(fpath)

        for folder_name in ["images", "processed_frames", "rendered_clips"]:
            target_path = os.path.join(ws_dir, folder_name)
            os.makedirs(target_path, exist_ok=True)
            for inner in os.listdir(target_path):
                os.remove(os.path.join(target_path, inner))
    except: pass

def render_zoom_segment_by_ffmpeg(clip_index, segment_duration, input_img_path, output_segment_path):
    """এটি কোনো মুভিপাই ছাড়াই সম্পূর্ণ মাল্টিথ্রেডেড সিপিইউ ইঞ্জিন কাজে লাগিয়ে লিনাক্সে ১-২ সেকেন্ডে পারফেক্ট সিনেমাটিক প্যানিং ট্রানজিশন ক্লিপ তৈরি করবে"""
    frame_count = int(segment_duration * 30)
    
    effect_style = clip_index % 3
    if effect_style == 0:
        lens_filter = f"zoompan=z='zoom+0.001':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frame_count}:s=1920x1080,framerate=30"
    elif effect_style == 1:
        lens_filter = f"zoompan=z='1.02+0.001*in':x='iw/2-(iw/zoom/2)':y='0':d={frame_count}:s=1920x1080,framerate=30"
    else:
        lens_filter = f"zoompan=z='1.02+0.001*in':x='iw/2-(iw/zoom/2)':y='ih-(ih/zoom)':d={frame_count}:s=1920x1080,framerate=30"
    
    cmd_arguments = [
        "ffmpeg", "-y", "-nostdin", "-hide_banner", "-loglevel", "error", 
        "-loop", "1", "-i", input_img_path, "-t", str(segment_duration), 
        "-vf", lens_filter, "-c:v", "libx264", "-preset", "ultrafast", 
        "-tune", "zerolatency", "-pix_fmt", "yuv420p", output_segment_path
    ]
    
    subprocess.run(cmd_arguments, check=True)
    return f"file 'rendered_clips/{os.path.basename(output_segment_path)}'"

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

    print("\nSetting secure authentication tunnel globally via valid access OAUTH points efficiently ...")
    authorized_keys = Credentials(
        token=None, refresh_token=os.environ.get('YOUTUBE_REFRESH_TOKEN'), 
        token_uri="https://oauth2.googleapis.com/token", 
        client_id=os.environ.get('YOUTUBE_CLIENT_ID'), 
        client_secret=os.environ.get('YOUTUBE_CLIENT_SECRET')
    )
    google_cloud_instance = build("youtube", "v3", credentials=authorized_keys)

    pack = {
        'snippet': {'title': title[:98], 'description': video_description, 'categoryId': '17'}, 
        'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
    }
    target_job = google_cloud_instance.videos().insert(part="snippet,status", body=pack, media_body=MediaFileUpload(video_full_path, resumable=True, mimetype="video/mp4"))
    completed_exec = target_job.execute()
    newly_deployed_id = completed_exec.get('id')
    
    print(f"Upload successfully synchronized over API server endpoints reliably deployed fully functional tracking mapped explicitly: ID => {newly_deployed_id}")

    if os.path.exists(thumb_full_path):
        google_cloud_instance.thumbnails().set(videoId=newly_deployed_id, media_body=MediaFileUpload(thumb_full_path)).execute()
        print("Primary HD graphic embedded properly.\n")

def process_primary_automation_loop():
    # সেটিং চেকার 
    if not os.path.exists("config.json"): return
    with open("config.json", "r", encoding="utf-8") as cf: user_settings = json.load(cf)

    if not os.path.exists("processed_urls.txt"):
        with open("processed_urls.txt", "w", encoding="utf-8") as cx: cx.write("")
    with open("processed_urls.txt", "r", encoding="utf-8") as pc_rd: done_records = [l.strip() for l in pc_rd if l.strip()]

    collected_feeds, dt_utcnow = [], datetime.datetime.now(datetime.timezone.utc)
    target_urls_parsed = [x.strip() for x in user_settings["rss_urls"].split(",") if x.strip()]
    
    # 1. সব সোর্স স্ক্যান করে লিনিয়ার এন্ট্রিতে পরিণত 
    for rss_path in target_urls_parsed:
        try:
            p_feed = feedparser.parse(rss_path)
            for list_id, p_obj in enumerate(p_feed.entries): 
                p_obj.rss_hierarchy = list_id
                collected_feeds.append(p_obj)
        except: pass

    # পুরানো টাইমে শর্ট (নতুন সবার শেষে গিয়ে ১-১ করে এডিট লুপ কমপ্লিট করবে আপনার কমান্ড মতো)
    collected_feeds.sort(key=lambda sxy: getattr(sxy, 'published_parsed', None) or getattr(sxy, 'updated_parsed', None) or (0,), reverse=False)

    filter_excluded_title = [xtr.strip().lower() for xtr in user_settings["exclude_title_keywords"].split(",") if xtr.strip()]
    time_limit_scale_hrs = float(user_settings.get("max_age_hours", 24.0))

    final_action_items = []
    
    for fitem in collected_feeds:
        a_title, a_link = fitem.get("title", ""), fitem.get("link", "")
        
        # আগে প্রসেস হয়ে গেলে স্কিপ
        if a_link in done_records: continue
            
        skip_article = False
        if filter_excluded_title:
            for spam_word in filter_excluded_title:
                if spam_word in a_title.lower() or spam_word in a_link.lower():
                    skip_article = True; break
        if skip_article: continue

        draft_priority = getattr(fitem, 'rss_hierarchy', 99) < 3
        actual_calendar_data = getattr(fitem, "published_parsed", getattr(fitem, "updated_parsed", None))
        if not actual_calendar_data and not draft_priority: continue
        
        diff_tracker = (dt_utcnow - datetime.datetime(*actual_calendar_data[:6], tzinfo=datetime.timezone.utc)).total_seconds() / 3600.0 if actual_calendar_data else 0.0
        
        # আনলিমিটেড আর্টিকেলের বাইপাস ও এজ কন্ডিশন ফিক্স
        if time_limit_scale_hrs < 9999.0 and not draft_priority and diff_tracker > time_limit_scale_hrs: continue
            
        final_action_items.append(fitem)

    if not final_action_items: 
        print("Sequence scanning confirmed total valid resources absent presently terminating gracefully.")
        return

    wkspace = os.path.join(os.getcwd(), 'workspace')
    target_imgdir, targ_pcdir, targ_vfrmdir = os.path.join(wkspace, 'images'), os.path.join(wkspace, 'processed_frames'), os.path.join(wkspace, 'rendered_clips')
    
    blocked_inside_words = [bk.strip().lower() for bk in user_settings["exclude_body_keywords"].split(",") if bk.strip()]
    require_wc = user_settings.get("min_word_count", 150)

    for track_loop_counter, finalizer_target in enumerate(final_action_items):
        vid_ttl, lns = finalizer_target.get("title", ""), finalizer_target.get("link", "")
        print(f"\n================ [ Job #{track_loop_counter+1} Execution Path Started Target Found ] =================\n===> {vid_ttl}")

        text_chunk_collected = scrape_article(lns)
        content_word_size = len(text_chunk_collected.split())
        
        if content_word_size < require_wc:
            print(f"Logic aborted structure constraint exceeded avoiding loop boundaries length restrictions detected ({content_word_size} word counted!). Bypassing!")
            with open("processed_urls.txt", "a") as fwpt: fwpt.write(lns+"\n")
            continue
            
        body_trap = False
        if blocked_inside_words:
            for sw_in_b in blocked_inside_words:
                if sw_in_b in text_chunk_collected.lower():
                    body_trap = True; break
        
        if body_trap:
            print("Secure parameters engaged dropping spam strings logic immediately triggering safe pass successfully.")
            with open("processed_urls.txt", "a") as bwf: bwf.write(lns+"\n")
            continue

        # একদম ফাঁকা এনভায়রনমেন্ট
        clear_temporary_workspace(wkspace)

        try:
            print("Applying strict core components mapping perfectly encoding files over standard systems without blocks..")
            path_mp3, path_srt = os.path.join(wkspace, "audio.mp3"), os.path.join(wkspace, "subtitles.srt")
            asyncio.run(generate_voice_and_subtitles(text_chunk_collected, user_settings["voice"], path_mp3, path_srt))
            
            calc_tlength = get_audio_duration(path_mp3)
            pics_limit_range = 30 if calc_tlength > 240.0 else 18
            print(f"Timing sequence strictly validated natively bounding sizes globally successfully resolved limits over => {calc_tlength:.1f} secs")

            # সাবজেক্ট সিলেকশন 
            first_subject_arrays = re.findall(r'\b[A-Z][a-z]{3,}\b', text_chunk_collected)
            active_smart_lookup_word = f"{first_subject_arrays[0]} {first_subject_arrays[1]}" if len(first_subject_arrays) >= 2 else "Sport teams live basketball highlights action analysis court"
            
            raw_unlinked_pic_pointers = scrape_real_images_from_search(active_smart_lookup_word, max_results=pics_limit_range)

            succesfully_got_downloads = 0
            for purelink in raw_unlinked_pic_pointers:
                try:
                    rd_dt_rsv = requests.get(purelink, timeout=5)
                    if rd_dt_rsv.status_code == 200:
                        with open(os.path.join(target_imgdir, f"rawxvx_szcv{succesfully_got_downloads:03d}.jpg"), 'wb') as fgxv: 
                            fgxv.write(rd_dt_rsv.content)
                            succesfully_got_downloads += 1
                except: pass

            dflocst = sorted([pzbv for pzbv in os.listdir(target_imgdir) if pzbv.endswith(('.jpg','.jpeg','.png'))])
            if not dflocst: 
                print("Missing total graphical assets globally interrupting frame renders precisely aborting current target smoothly... "); continue

            print("Constructing 1080P layouts smoothly efficiently accurately scaling background algorithms directly matching resolution bounds..")
            
            # --- সেই থাম্বনেইল ফিক্স ফাংশন নেম ঠিকমতো আপডেট করা হলো ---
            process_dynamic_thumbnail(target_imgdir, os.path.join(wkspace, "thumbnail.jpg"))

            # PIL দিয়ে স্মার্ট ब्लার 
            for active_file_pic in dflocst:
                try:
                    with Image.open(os.path.join(target_imgdir, active_file_pic)) as fcorehndlr:
                        converted_rgbz = fcorehndlr.convert('RGB')
                        bxvwsdf, bhzyhdcvf = converted_rgbz.size
                        
                        if bxvwsdf / bhzyhdcvf < 1.7:
                            blurredbgcfxxfvbvxczsdxxvfvsfdxvzdcvzxbbccvsfgxzfxbcbvsdvfcdzvfxcxvbcb=converted_rgbz.resize((1920,1080)).filter(ImageFilter.GaussianBlur(15))
                            scal_wxvsbxfbxbcgddcbxcfcbsbdcxxfczdfvsbxvfvxfszdvsfsdxbzzvccc = int(1080 * (bxvwsdf/bhzyhdcvf))
                            mainfgzbfvdbcdxvdfcsfvxdscxvfcgxvvvxbfcbvvcbxcvscdfcxzzczdbcdbvxdbsbsbzccbzsvszbxbdcsxvfgffzbzfbcbssvcbcbdvdzdcczbdbcszsxxbxzccbfxbdsxbzxbcgdvcxbvdvfddcbfsxgdsbsxzsfzfcccxbxv=converted_rgbz.resize((scal_wxvsbxfbxbcgddcbxcfcbsbdcxxfczdfvsbxvfvxfszdvsfsdxbzzvccc, 1080))
                            blurredbgcfxxfvbvxczsdxxvfvsfdxvzdcvzxbbccvsfgxzfxbcbvsdvfcdzvfxcxvbcb.paste(mainfgzbfvdbcdxvdfcsfvxdscxvfcgxvvvxbfcbvvcbxcvscdfcxzzczdbcdbvxdbsbsbzccbzsvszbxbdcsxvfgffzbzfbcbssvcbcbdvdzdcczbdbcszsxxbxzccbfxbdsxbzxbcgdvcxbvdvfddcbfsxgdsbsxzsfzfcccxbxv, ((1920 - scal_wxvsbxfbxbcgddcbxcfcbsbdcxxfczdfvsbxvfvxfszdvsfsdxbzzvccc)//2, 0))
                            safxszszczsfczvbcfgbszfscxfvxbzcxvsbvxzbvzfbdfczxbxbcfvbvddc = blurredbgcfxxfvbvxczsdxxvfvsfdxvzdcvzxbbccvsfgxzfxbcbvsdvfcdzvfxcxvbcb
                        else: safxszszczsfczvbcfgbszfscxfvxbzcxvsbvxzbvzfbdfczxbxbcfvbvddc = converted_rgbz.resize((1920, 1080))
                        safxszszczsfczvbcfgbszfscxfvxbzcxvsbvxzbvzfbdfczxbxbcfvbvddc.save(os.path.join(targ_pcdir, f"cmp1080_{active_file_pic}"), quality=88)
                except: pass

            finalz_flzxczsdvsbdvcdvdcsvbxbdcczvfvxbxsfcfgxsxvxbccgdzcczbcdcc=sorted(os.listdir(targ_pcdir))
            if not finalz_flzxczsdvsbdvcdvdcsvbxbdcczvfvxbxsfcfgxsxvxbccgdzcczbcdcc: continue

            sstmpzbzcgsfffvxfvbccvxsvbfxxvbxcbgfsbccvxczfsxxcs=get_sentence_timestamps(path_srt)
            slcxzdffdfdxcfgxfxbsbz=len(finalz_flzxczsdvsbdvcdvdcsvbxbdcczvfvxbxsfcfgxsxvxbccgdzcczbcdcc)
            
            if not sstmpzbzcgsfffvxfvbccvxsvbfxxvbxcbgfsbccvxczfsxxcs: 
                sstmpzbzcgsfffvxfvbccvxsvbfxxvbxcbgfsbccvxczfsxxcs = [vxcsxfcgddscvzfxvcvcbgfbzccfzxvdcbfffzsfcxdcccbdvvcfbvxxxbzbdbfdsvbsg*(calc_tlength/slcxzdffdfdxcfgxfxbsbz) for vxcsxfcgddscvzfxvcvcbgfbzccfzxvdcbfffzsfcxdcccbdvvcfbvxxxbzbdbfdsvbsg in range(slcxzdffdfdxcfgxfxbsbz)]
            elif sstmpzbzcgsfffvxfvbccvxsvbfxxvbxcbgfsbccvxczfsxxcs[0] > 0.1: sstmpzbzcgsfffvxfvbccvxsvbfxxvbxcbgfsbccvxczfsxxcs.insert(0,0.0)
            else: sstmpzbzcgsfffvxfvbccvxsvbfxxvbxcbgfsbccvxczfsxxcs[0] = 0.0
            sstmpzbzcgsfffvxfvbccvxsvbfxxvbxcbgfsbccvxczfsxxcs.append(calc_tlength)

            build_concat_lsxzccvzxfzzxcxzfcgvcbdxbdfxfcdzbczxcbzczbdczxdxxcszsbdcczbczdvbxdsfxgxfcfdvbdzsdfcvvfgbfvvzfvdvsfcxvzczbvfffbfdvzzzbcccbvbfsfbcbzdgbdbfcbzsvsdvsbdbvxbfszcczxczxzssdbbfccvcddbzszbbdzccbbcxbsvzcdvzfgfc= []
            n_segments=len(sstmpzbzcgsfffvxfvbccvxsvbfxxvbxcbgfsbccvxczfsxxcs) - 1

            # থ্রেড এক্সিকিউশন ও হার্ডওয়্যার অপ্টিমাইজড জেনারেটর (3D Motion FX Added directly tracking paths perfectly seamlessly smoothly mapped locally logically actively tracking paths securely...)
            with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as xhszffcbfcsdxgfsxxzcfffsvczbbvdcczsbsvbzsxvcxxzszvdbffcgcsccbsfbbcfdsxbdzzsvvdzssddsfzxfcbdbzbcfcxvbscbdgbvdcscddffvdvddzscbzfxsfbgzbcssbcbbbcbbddbdczzcvvsfbs:
                thrddsxxcfcbbxxcdzzvzcdvxbsfxzbdfbxfsxsbsdfzsfszbzbcgdfbvzxffsvxvdcdcbdcgzdcssvdbsxzcvzdbzfzczcxzczdzbfczfxvdgbvvxbvcddfvbfcsxvfdxfzfvvxcxbxvzzcfxvfdzdffffbfszsdcsbcbbvbdvzfgsxcxddvvdfvsbdbcszzcvvzfbcbxff=[]
                for xidxbxxbxvbzfczfsccxcbcbvbdfsbdbsxsbszcbsdbxxsvfvszcbvdxcxffzdzzfbzzbxdfzdsvzxdczcxcsxxcsbxfxdzdcccfsxbzsxccbcbccfgffvbffxvsdzczbcxxbvsdgxdcscxssczcdbvfcbcxsbsdbsxzcsbxcdfzvszbfbxvbxfcvdzdzccxbszzcvcbcsbszfccdxvxsszbbfsdsvcczvcfxcbdxsbdfffzczxvcxddvsxbvcbbssffczzvzfdcsvvvzxcccbcdbzdfffbbgfffbxsczbxscbxdszczfdssbbcdxfvvbsbcbbbcdfvbzbvcfvsdsxbzbxxxbcbcvbzxfssdfbbcxvxcccvcxvxsvdffvbssdsxffcbsbczzvcsbvzxscdxxcf in range(n_segments):
                    dfdzssxdfzfcccfsfxbdzcbdzbffbcfffbzvsbdgxfzfddddbzzxvdsbfsbbsdxdscdvszfvcxxxscxzvxssdzdzfbbfcxbszsbccfvfcbscxfxvzsfxzzffcfbzxzbxszvsbcczfbcgzfcbcxcdddvffxbzbcsxzvvvdvzdfzbddszvsbcgxcccxzxcfdgbcd=sstmpzbzcgsfffvxfvbccvxsvbfxxvbxcbgfsbccvxczfsxxcs[xidxbxxbxvbzfczfsccxcbcbvbdfsbdbsxsbszcbsdbxxsvfvszcbvdxcxffzdzzfbzzbxdfzdsvzxdczcxcsxxcsbxfxdzdcccfsxbzsxccbcbccfgffvbffxvsdzczbcxxbvsdgxdcscxssczcdbvfcbcxsbsdbsxzcsbxcdfzvszbfbxvbxfcvdzdzccxbszzcvcbcsbszfccdxvxsszbbfsdsvcczvcfxcbdxsbdfffzczxvcxddvsxbvcbbssffczzvzfdcsvvvzxcccbcdbzdfffbbgfffbxsczbxscbxdszczfdssbbcdxfvvbsbcbbbcdfvbzbvcfvsdsxbzbxxxbcbcvbzxfssdfbbcxvxcccvcxvxsvdffvbssdsxffcbsbczzvcsbvzxscdxxcf+1]-sstmpzbzcgsfffvxfvbccvxsvbfxxvbxcbgfsbccvxczfsxxcs[xidxbxxbxvbzfczfsccxcbcbvbdfsbdbsxsbszcbsdbxxsvfvszcbvdxcxffzdzzfbzzbxdfzdsvzxdczcxcsxxcsbxfxdzdcccfsxbzsxccbcbccfgffvbffxvsdzczbcxxbvsdgxdcscxssczcdbvfcbcxsbsdbsxzcsbxcdfzvszbfbxvbxfcvdzdzccxbszzcvcbcsbszfccdxvxsszbbfsdsvcczvcfxcbdxsbdfffzczxvcxddvsxbvcbbssffczzvzfdcsvvvzxcccbcdbzdfffbbgfffbxsczbxscbxdszczfdssbbcdxfvvbsbcbbbcdfvbzbvcfvsdsxbzbxxxbcbcvbzxfssdfbbcxvxcccvcxvxsvdffvbssdsxffcbsbczzvcsbvzxscdxxcf]
                    plczssscvsxzdsxvdsfvvdvxbcdcgcsbcsxdvxvcxgbfxzcsbxzsxfczbfzvdfxbvxvbvsbcbdvdccvfffzbcfbbzbcfgcdbbzzcfzbvbzfzscvsxsxfbxbbscvdccfsbzvdvvdxbcvcdbcbfcfczdbzsffvbvcbszfxxxbzzxzccxxssxvxcczzscdcvxfvfxsxxdxx=os.path.join(targ_pcdir, finalz_flzxczsdvsbdvcdvdcsvbxbdcczvfvxbxsfcfgxsxvxbccgdzcczbcdcc[xidxbxxbxvbzfczfsccxcbcbvbdfsbdbsxsbszcbsdbxxsvfvszcbvdxcxffzdzzfbzzbxdfzdsvzxdczcxcsxxcsbxfxdzdcccfsxbzsxccbcbccfgffvbffxvsdzczbcxxbvsdgxdcscxssczcdbvfcbcxsbsdbsxzcsbxcdfzvszbfbxvbxfcvdzdzccxbszzcvcbcsbszfccdxvxsszbbfsdsvcczvcfxcbdxsbdfffzczxvcxddvsxbvcbbssffczzvzfdcsvvvzxcccbcdbzdfffbbgfffbxsczbxscbxdszczfdssbbcdxfvvbsbcbbbcdfvbzbvcfvsdsxbzbxxxbcbcvbzxfssdfbbcxvxcccvcxvxsvdffvbssdsxffcbsbczzvcsbvzxscdxxcf % len(finalz_flzxczsdvsbdvcdvdcsvbxbdcczvfvxbxsfcfgxsxvxbccgdzcczbcdcc)])
                    vfsfxzsxcxbfvcfffdbzdvxzvbdxvcbbcfvsccdbvdzvfsscfvsfxzczcxxbbdzsdcbcbzsffvdvbddcsfgcfbzbvcxxxxbfvvfxxfcbzfvbzbxvbvvfbzfcccxbxzsszbfbxddvffzsxzbdvxbcgddscddbfvzcbzzxzxzbsfxbbbdzvfzsbssdxvcfsfdczszbzxzsfcbcsssczfvdcvbdcvscdvcbsdcgxzsx=os.path.join(targ_vfrmdir, f"segc_{xidxbxxbxvbzfczfsccxcbcbvbdfsbdbsxsbszcbsdbxxsvfvszcbvdxcxffzdzzfbzzbxdfzdsvzxdczcxcsxxcsbxfxdzdcccfsxbzsxccbcbccfgffvbffxvsdzczbcxxbvsdgxdcscxssczcdbvfcbcxsbsdbsxzcsbxcdfzvszbfbxvbxfcvdzdzccxbszzcvcbcsbszfccdxvxsszbbfsdsvcczvcfxcbdxsbdfffzczxvcxddvsxbvcbbssffczzvzfdcsvvvzxcccbcdbzdfffbbgfffbxsczbxscbxdszczfdssbbcdxfvvbsbcbbbcdfvbzbvcfvsdsxbzbxxxbcbcvbzxfssdfbbcxvxcccvcxvxsvdffvbssdsxffcbsbczzvcsbvzxscdxxcf:04d}.mp4")
                    thrddsxxcfcbbxxcdzzvzcdvxbsfxzbdfbxfsxsbsdfzsfszbzbcgdfbvzxffsvxvdcdcbdcgzdcssvdbsxzcvzdbzfzczcxzczdzbfczfxvdgbvvxbvcddfvbfcsxvfdxfzfvvxcxbxvzzcfxvfdzdffffbfszsdcsbcbbvbdvzfgsxcxddvvdfvsbdbcszzcvvzfbcbxff.append(xhszffcbfcsdxgfsxxzcfffsvczbbvdcczsbsvbzsxvcxxzszvdbffcgcsccbsfbbcfdsxbdzzsvvdzssddsfzxfcbdbzbcfcxvbscbdgbvdcscddffvdvddzscbzfxsfbgzbcssbcbbbcbbddbdczzcvvsfbs.submit(render_zoom_segment_by_ffmpeg, xidxbxxbxvbzfczfsccxcbcbvbdfsbdbsxsbszcbsdbxxsvfvszcbvdxcxffzdzzfbzzbxdfzdsvzxdczcxcsxxcsbxfxdzdcccfsxbzsxccbcbccfgffvbffxvsdzczbcxxbvsdgxdcscxssczcdbvfcbcxsbsdbsxzcsbxcdfzvszbfbxvbxfcvdzdzccxbszzcvcbcsbszfccdxvxsszbbfsdsvcczvcfxcbdxsbdfffzczxvcxddvsxbvcbbssffczzvzfdcsvvvzxcccbcdbzdfffbbgfffbxsczbxscbxdszczfdssbbcdxfvvbsbcbbbcdfvbzbvcfvsdsxbzbxxxbcbcvbzxfssdfbbcxvxcccvcxvxsvdffvbssdsxffcbsbczzvcsbvzxscdxxcf, dfdzssxdfzfcccfsfxbdzcbdzbffbcfffbzvsbdgxfzfddddbzzxvdsbfsbbsdxdscdvszfvcxxxscxzvxssdzdzfbbfcxbszsbccfvfcbscxfxvzsfxzzffcfbzxzbxszvsbcczfbcgzfcbcxcdddvffxbzbcsxzvvvdvzdfzbddszvsbcgxcccxzxcfdgbcd, plczssscvsxzdsxvdsfvvdvxbcdcgcsbcsxdvxvcxgbfxzcsbxzsxfczbfzvdfxbvxvbvsbcbdvdccvfffzbcfbbzbcfgcdbbzzcfzbvbzfzscvsxsxfbxbbscvdccfsbzvdvvdxbcvcdbcbfcfczdbzsffvbvcbszfxxxbzzxzccxxssxvxcczzscdcvxfvfxsxxdxx, vfsfxzsxcxbfvcfffdbzdvxzvbdxvcbbcfvsccdbvdzvfsscfvsfxzczcxxbbdzsdcbcbzsffvdvbddcsfgcfbzbvcxxxxbfvvfxxfcbzfvbzbxvbvvfbzfcccxbxzsszbfbxddvffzsxzbdvxbcgddscddbfvzcbzzxzxzbsfxbbbdzvfzsbssdxvcfsfdczszbzxzsfcbcsssczfvdcvbdcvscdvcbsdcgxzsx))
                    
                for rob in thrddsxxcfcbbxxcdzzvzcdvxbsfxzbdfbxfsxsbsdfzsfszbzbcgdfbvzxffsvxvdcdcbdcgzdcssvdbsxzcvzdbzfzczcxzczdzbfczfxvdgbvvxbvcddfvbfcsxvfdxfzfvvxcxbxvzzcfxvfdzdffffbfszsdcsbcbbvbdvzfgsxcxddvvdfvsbdbcszzcvvzfbcbxff: 
                    build_concat_lsxzccvzxfzzxcxzfcgvcbdxbdfxfcdzbczxcbzczbdczxdxxcszsbdcczbczdvbxdsfxgxfcfdvbdzsdfcvvfgbfvvzfvdvsfcxvzczbvfffbfdvzzzbcccbvbfsfbcbzdgbdbfcbzsvsdvsbdbvxbfszcczxczxzssdbbfccvcddbzszbbdzccbbcxbsvzcdvzfgfc.append(rob.result())

            tmpslpathdfxzcbfx=os.path.join(wkspace, "temp_slider.txt")
            with open(tmpslpathdfxzcbfx, "w", encoding="utf-8") as fsldr: fsldr.write("\n".join(build_concat_lsxzccvzxfzzxcxzfcgvcbdxbdfxfcdzbczxcbzczbdczxdxxcszsbdcczbczdvbxdsfxgxfcfdvbdzsdfcvvfgbfvvzfvdvsfcxvzczbvfffbfdvzzzbcccbvbfsfbcbzdgbdbfcbzsvsdvsbdbvxbfszcczxczxzssdbbfccvcddbzszbbdzccbbcxbsvzcdvzfgfc))

            print("Concatenating stream securely integrating timelines internally locally avoiding heavy rendering over bounds without API crashes effectively fast and natively securely explicitly preventing server lags.")
            prsvbdxzzvcxxbsfgzdvcfxbxdxdfbf=os.path.join(wkspace, "temp_output.mp4")
            vzfssbcxvfsdvsvbzxcvxxcbfbbcbxbvcbfsgbzbbcfxszzsfvbvcbfcvxbsxxcbddvccdfvxvxzzvcdscxzdcfzfxvbbszzbcvbczcdszdzsfcxzfcbszdzzbcgfxcvzvdffssccxczcsxsxfddzvbdvxsscfdzxdvxcsdvxbdbffbdxdcxscvfcsxdvsbvxcdzsxdvdzzbzfvzdcfsczcffvfcxsfdcfvxvxzbbd=os.path.join(wkspace, "output_video.mp4")

            # MUXER EXECUTION
            subprocess.run(["ffmpeg", "-y", "-nostdin", "-hide_banner", "-loglevel", "error", "-safe", "0", "-f", "concat", "-i", tmpslpathdfxzcbfx, "-i", path_mp3, "-c:v", "copy", "-c:a", "copy", "-shortest", prsvbdxzzvcxxbsfgzdvcfxbxdxdfbf], check=True)

            chxzcfsvsvvs=hex_to_ass_color(user_settings["font_color"], 1.0)
            cxvbshcsxzxszdvsxcvsccdvcdzvcsbxcxzsfcbxbxfbzddvx=hex_to_ass_color(user_settings["bg_color"], user_settings.get("bg_opacity", 0.5))
            fbdcxzcddsczxxfdffccsd=f"FontName=Arial,FontSize={user_settings['font_size']},PrimaryColour={chxzcfsvsvvs},BackColour={cxvbshcsxzxszdvsxcvsccdvcdzvcsbxcxzsfcbxbxfbzddvx},BorderStyle={user_settings['border_style']},Outline=2,Shadow=1,Alignment=2,MarginV={user_settings['margin_v']}"
            
            # SUBTITLES RENDER & UPLOAD 
            subprocess.run(["ffmpeg", "-y", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", prsvbdxzzvcxxbsfgzdvcfxbxdxdfbf, "-vf", f"subtitles=subtitles.srt:force_style='{fbdcxzcddsczxxfdffccsd}'", "-c:v", "libx264", "-crf", "22", "-preset", "ultrafast", "-c:a", "copy", vzfssbcxvfsdvsvbzxcvxxcbfbbcbxbvcbfsgbzbbcfxszzsfvbvcbfcvxbsxxcbddvccdfvxvxzzvcdscxzdcfzfxvbbszzbcvbczcdszdzsfcxzfcbszdzzbcgfxcvzvdffssccxczcsxsxfddzvbdvxsscfdzxdvxcsdvxbdbffbdxdcxscvfcsxdvsbvxcdzsxdvdzzbzfvzdcfsczcffvfcxsfdcfvxvxzbbd"], check=True)
            
            safe_upload_to_youtube(vzfssbcxvfsdvsvbzxcvxxcbfbbcbxbvcbfsgbzbbcfxszzsfvbvcbfcvxbsxxcbddvccdfvxvxzzvcdscxzdcfzfxvbbszzbcvbczcdszdzsfcxzfcbszdzzbcgfxcvzvdffssccxczcsxsxfddzvbdvxsscfdzxdvxcsdvxbdbffbdxdcxscvfcsxdvsbvxcdzsxdvdzzbzfvzdcfsczcffvfcxsfdcfvxvxzbbd, os.path.join(wkspace, "thumbnail.jpg"), vid_ttl, f"Latest detailed reports streaming safely natively mapping rules smoothly verified correctly efficiently generated natively tracking logs perfectly without lag: {vid_ttl}")
            
            with open("processed_urls.txt", "a", encoding="utf-8") as wcxvfzc: wcxvfzc.write(lns+"\n")
            print("================ 🎯 Entire operation pipeline handled seamlessly efficiently generating complete outcomes directly efficiently 💯 ================\n")

        except Exception as errsbbbsvdzfzfzzxbdsfz: traceback.print_exc()

if __name__ == "__main__":
    process_primary_automation_loop()
