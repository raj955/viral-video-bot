"""
=============================================================
   INDIAN MEME SHORTS BOT
   Exactly like Joshifamilymemes95!

   Bade Indian YouTubers ke funny moments cut karo
   + Caption add karo + YouTube/Facebook upload karo

   CHALANE KA TARIKA:
   python meme_bot.py                    # auto chalao
   python meme_bot.py --channel sourav   # specific creator
   python meme_bot.py --url VIDEO_URL    # specific video
   python meme_bot.py --schedule         # daily auto

   INSTALL:
   pip install yt-dlp moviepy==1.0.3 google-api-python-client
               google-auth-oauthlib requests schedule numpy
=============================================================
"""

import os, sys, json, time, pickle, random, requests, schedule
import subprocess, shutil
from datetime import datetime

# ── ImageMagick (Windows) ──────────────────────────────────
import moviepy.config as mpy_conf
for _p in [
    r"C:\Program Files\ImageMagick-7.1.2-Q8\magick.exe",
    r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe",
    r"C:\Program Files\ImageMagick-7.1.0-Q16-HDRI\magick.exe",
]:
    if os.path.exists(_p):
        mpy_conf.change_settings({"IMAGEMAGICK_BINARY": _p})
        print(f"[OK] ImageMagick: {_p}")
        break

import numpy as np
from moviepy.editor import (
    VideoFileClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, ImageClip
)
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# =============================================================
#   SETTINGS — SIRF YAHAN CHANGE KARO
# =============================================================

import os as _os
CHANNEL_NAME        = _os.environ.get("CHANNEL_NAME",     "JoshiFamilyMemes")
YOUTUBE_CLIENT_SECRETS = "client_secrets.json"


# Font
FONT = r"C:\Windows\Fonts\arialbd.ttf"
if not os.path.exists(FONT):
    FONT = None  # Auto fallback

# Folders
DOWNLOAD_FOLDER = "source_videos"
OUTPUT_FOLDER   = "shorts_output"
LOG_FILE        = "meme_log.json"

# Clip settings
MIN_CLIP_DURATION = 15    # Minimum short duration (seconds)
MAX_CLIP_DURATION = 45    # Maximum short duration (seconds)
CLIPS_PER_VIDEO   = 3     # Ek video se kitne shorts banao
VIDEOS_PER_RUN    = 2     # Ek run mein kitni videos process karo

# =============================================================
#   INDIAN CREATORS LIST
#   (Inke funny moments se Shorts banenge)
# =============================================================

CREATORS = {
    "sourav": {
        "channel": "https://www.youtube.com/channel/UCjvgGbPPn-FgYeguc5nxG4A",
        "name":    "Sourav Joshi",
        "credit":  "Sourav Joshi Vlogs",
    },
    "amit": {
        "channel": "https://www.youtube.com/channel/UC_vcKmg67vjMP7ciLnSxSHQ",
        "name":    "Amit Bhadana",
        "credit":  "Amit Bhadana",
    },
    "round2hell": {
        "channel": "https://www.youtube.com/@Round2Hell",
        "name":    "Round2Hell",
        "credit":  "Round2Hell",
    },
    "triggered": {
        "channel": "https://www.youtube.com/@triggered_insaan",
        "name":    "Triggered Insaan",
        "credit":  "Triggered Insaan",
    },
    "carry": {
        "channel": "https://www.youtube.com/@CarryMinati",
        "name":    "CarryMinati",
        "credit":  "CarryMinati",
    },
    "ashish": {
        "channel": "https://www.youtube.com/@AshishChanchlanivines",
        "name":    "Ashish Chanchlani",
        "credit":  "Ashish Chanchlani Vines",
    },
    "bhuvan": {
        "channel": "https://www.youtube.com/@BBKiVines",
        "name":    "Bhuvan Bam",
        "credit":  "BB Ki Vines",
    },
    "thugesh": {
        "channel": "https://www.youtube.com/@Thugesh",
        "name":    "Thugesh",
        "credit":  "Thugesh",
    },
}

# =============================================================
#   FUNNY CAPTIONS (auto add honge)
# =============================================================

CAPTIONS = [
    "😂 Ye toh hona hi tha!",
    "💀 Bhai ye kya tha?!",
    "😭 Roz ka scene hai ghar mein",
    "🤣 Indian family problems",
    "😂 Relatable AF!",
    "💀 Sirf Indian samjhenge",
    "🤣 Bhai ke saath aisa hi hota hai",
    "😭 Mummy ki yaad aa gayi",
    "😂 Ghar ka drama!",
    "💀 Ye toh mera ghar hai",
    "🤣 Papa ka reaction dekho",
    "😂 Desi life be like...",
    "💀 Aisa kya hua bhai?!",
    "🤣 Indian parents 🤣",
    "😭 Bachpan ki yaadein",
]

# =============================================================
#   STEP 1: CHANNEL SE LATEST VIDEOS DHUNDO
# =============================================================

def get_latest_videos(creator_key, count=5):
    """Channel se latest videos ki list lo"""
    creator = CREATORS.get(creator_key)
    if not creator:
        print(f"  [ERROR] Creator '{creator_key}' nahi mila!")
        return []

    channel_url = creator["channel"] + "/videos"
    print(f"\n  Fetching videos from: {creator['name']}")

    ydl_opts = {
        "quiet":        True,
        "extract_flat": True,
        "playlistend":  count * 2,  # Extra fetch, filter baad mein
        "no_warnings":  True,
    }

    try:
        import yt_dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            if not info or "entries" not in info:
                print("  [ERROR] Videos nahi mile")
                return []

            videos = []
            for entry in info["entries"]:
                if entry is None:
                    continue
                dur = entry.get("duration", 0) or 0
                # Only long videos (5-30 min) — inme funny moments zyada
                if 300 <= dur <= 1800:
                    videos.append({
                        "id":       entry.get("id"),
                        "title":    entry.get("title", "Unknown"),
                        "url":      f"https://www.youtube.com/watch?v={entry.get('id')}",
                        "duration": dur,
                        "creator":  creator["name"],
                        "credit":   creator["credit"],
                    })
                if len(videos) >= count:
                    break

            print(f"  [OK] {len(videos)} videos mile")
            for v in videos:
                print(f"      - {v['title'][:55]} ({v['duration']//60}m)")
            return videos

    except Exception as e:
        print(f"  [ERROR] {e}")
        return []


# =============================================================
#   STEP 2: VIDEO DOWNLOAD KARO
# =============================================================

def download_video(video_url, creator_name):
    """Video download karo"""
    folder = os.path.join(DOWNLOAD_FOLDER, creator_name.replace(" ", "_"))
    os.makedirs(folder, exist_ok=True)

    import yt_dlp

    # Video ID extract karo
    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info     = ydl.extract_info(video_url, download=False)
        video_id = info["id"]

    filepath = os.path.join(folder, f"{video_id}.mp4")

    if os.path.exists(filepath):
        size = os.path.getsize(filepath) / (1024*1024)
        print(f"  Already downloaded: {filepath} ({size:.0f}MB)")
        return filepath

    print(f"  Downloading: {video_url}")
    ydl_opts = {
        "outtmpl":             filepath,
        "format":              "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
        "merge_output_format": "mp4",
        "quiet":               False,
        "no_warnings":         True,
    }

    # Cookies use karo agar available
    if os.path.exists("cookies.txt"):
        ydl_opts["cookiefile"] = "cookies.txt"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    if os.path.exists(filepath):
        size = os.path.getsize(filepath) / (1024*1024)
        print(f"  [OK] Downloaded: {filepath} ({size:.0f}MB)")
        return filepath

    raise FileNotFoundError(f"Download failed: {video_url}")


# =============================================================
#   STEP 3: FUNNY MOMENTS DETECT KARO (Audio Analysis)
# =============================================================

def detect_funny_moments(video_path, num_clips=3):
    """
    Audio loudness se funny moments dhundo.
    Jab audience hassti hai ya loud action hota hai =
    audio peak hota hai = funny moment!
    """
    print(f"  Analyzing audio for funny moments...")

    try:
        clip     = VideoFileClip(video_path)
        duration = clip.duration

        if duration < MIN_CLIP_DURATION * 2:
            print(f"  Video too short ({duration:.0f}s)")
            clip.close()
            return []

        # Audio extract karo aur analyze karo
        audio    = clip.audio
        fps      = 22050
        duration = clip.duration

        # Sample audio at intervals
        window   = 2.0   # 2 second windows
        step     = 1.0   # 1 second steps
        scores   = []

        t = 10  # First 10 seconds skip (intro hota hai)
        while t < duration - MAX_CLIP_DURATION - 5:
            try:
                # Audio chunk ka RMS (loudness) nikalo
                chunk = audio.subclip(t, min(t + window, duration))
                frame = chunk.to_soundarray(fps=fps)
                if len(frame) > 0:
                    rms = float(np.sqrt(np.mean(frame**2)))
                    scores.append((t, rms))
            except:
                pass
            t += step

        clip.close()

        if not scores:
            print("  No audio analysis possible, using random timestamps")
            # Random timestamps use karo
            moments = []
            used    = set()
            while len(moments) < num_clips:
                start = random.randint(30, int(duration) - MAX_CLIP_DURATION - 10)
                if not any(abs(start - u) < 30 for u in used):
                    moments.append(start)
                    used.add(start)
            return moments

        # Top loud moments dhundo
        scores.sort(key=lambda x: x[1], reverse=True)

        # Best moments select karo (overlap avoid karo)
        moments  = []
        used_times = []
        for t, score in scores:
            # Check overlap with already selected moments
            too_close = any(abs(t - u) < 25 for u in used_times)
            if not too_close:
                moments.append(t)
                used_times.append(t)
            if len(moments) >= num_clips:
                break

        # Agar kam moments mile
        while len(moments) < num_clips:
            t = random.randint(30, int(duration) - MAX_CLIP_DURATION - 10)
            if not any(abs(t - u) < 20 for u in moments):
                moments.append(t)

        moments.sort()
        print(f"  [OK] {len(moments)} funny moments found: {[f'{m:.0f}s' for m in moments]}")
        return moments

    except Exception as e:
        print(f"  [WARN] Audio analysis failed: {e}")
        print("  Using random timestamps instead")
        try:
            clip     = VideoFileClip(video_path)
            duration = clip.duration
            clip.close()
        except:
            duration = 600

        moments = []
        used    = set()
        while len(moments) < num_clips:
            start = random.randint(30, int(duration) - MAX_CLIP_DURATION - 10)
            if not any(abs(start - u) < 30 for u in used):
                moments.append(start)
                used.add(start)
        return sorted(moments)


# =============================================================
#   STEP 4: SHORTS BANAO
# =============================================================

def make_short(video_path, start_time, creator_info, video_title):
    """
    Ek funny moment se ek Short banao:
    - 9:16 portrait crop
    - Caption text
    - Channel watermark
    - Credit in corner
    """
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    clip_dur = random.randint(MIN_CLIP_DURATION, MAX_CLIP_DURATION)
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTPUT_FOLDER, f"short_{ts}_{int(start_time)}.mp4")

    print(f"  Making Short: {start_time:.0f}s - {start_time+clip_dur:.0f}s ({clip_dur}s)")

    try:
        # Load aur crop
        clip   = VideoFileClip(video_path)
        cw, ch = clip.size

        # Clip nikalo
        end_time = min(start_time + clip_dur, clip.duration - 1)
        segment  = clip.subclip(start_time, end_time)

        # Portrait format (9:16)
        W, H = 1080, 1920
        sw, sh = segment.size

        if sw > sh:
            # Landscape → portrait center crop
            new_w = int(sh * W / H)
            new_w = min(new_w, sw)
            x1    = (sw - new_w) // 2
            segment = segment.crop(x1=x1, y1=0, x2=x1 + new_w, y2=sh)

        segment = segment.resize((W, H))

        layers = [segment]

        # ── Funny caption (top mein) ──────────────────────
        caption = random.choice(CAPTIONS)
        try:
            cap_kwargs = {
                "txt":          caption,
                "fontsize":     55,
                "color":        "white",
                "stroke_color": "black",
                "stroke_width": 3,
                "method":       "caption",
                "size":         (W - 40, None),
            }
            if FONT:
                cap_kwargs["font"] = FONT

            caption_clip = (
                TextClip(**cap_kwargs)
                .set_duration(segment.duration)
                .set_position(("center", 0.08), relative=True)
            )
            layers.append(caption_clip)
        except Exception as e:
            print(f"  [WARN] Caption error: {e}")

        # ── Channel watermark (bottom right) ──────────────
        try:
            wm_kwargs = {
                "txt":          f"@{CHANNEL_NAME}",
                "fontsize":     38,
                "color":        "yellow",
                "stroke_color": "black",
                "stroke_width": 2,
            }
            if FONT:
                wm_kwargs["font"] = FONT

            wm = (
                TextClip(**wm_kwargs)
                .set_duration(segment.duration)
                .set_position(("right", 0.88), relative=True)
            )
            layers.append(wm)
        except Exception as e:
            print(f"  [WARN] Watermark error: {e}")

        # ── Credit text (bottom left) ──────────────────────
        try:
            cr_kwargs = {
                "txt":      f"Credit: {creator_info['credit']}",
                "fontsize": 28,
                "color":    "white",
                "stroke_color": "black",
                "stroke_width": 1,
            }
            if FONT:
                cr_kwargs["font"] = FONT

            credit = (
                TextClip(**cr_kwargs)
                .set_duration(segment.duration)
                .set_position((20, H - 80))
            )
            layers.append(credit)
        except Exception as e:
            print(f"  [WARN] Credit error: {e}")

        # Combine all layers
        final = CompositeVideoClip(layers, size=(W, H))

        # Save
        final.write_videofile(
            out_path,
            fps         = 30,
            codec       = "libx264",
            audio_codec = "aac",
            preset      = "fast",
            verbose     = False,
            logger      = None,
            threads     = 4,
        )

        clip.close()
        size_mb = os.path.getsize(out_path) / (1024*1024)
        print(f"  [OK] Short saved: {out_path} ({size_mb:.1f}MB)")
        return out_path

    except Exception as e:
        print(f"  [ERROR] Short creation failed: {e}")
        import traceback; traceback.print_exc()
        return None


# =============================================================
#   STEP 5: TITLE + DESCRIPTION GENERATE KARO
# =============================================================

def get_title_desc(creator_name, credit, video_title):
    """Catchy title aur description banao"""

    titles = [
        f"😂 {creator_name} ka ye scene toh dekho! #shorts",
        f"💀 {creator_name} ne kya kar diya! 😂 #shorts",
        f"🤣 {creator_name} family moment! #viral #shorts",
        f"😭 Sirf Indians samjhenge! 😂 #shorts #{creator_name.replace(' ','')}",
        f"💀 Bhai ye scene! 😂 {creator_name} #shorts",
        f"🤣 {creator_name} ka best moment! #funny #shorts",
        f"😂 Indian family drama! ft. {creator_name} #shorts",
        f"💀 Ghar ka scene! 😂 #desi #shorts",
    ]

    title = random.choice(titles)

    desc = f"""{title}

😂 Watch till the end!
Like aur Subscribe karo daily funny videos ke liye! 🔔

📌 Original Video Credit: {credit}
✅ All credit goes to {credit}
⚠️ This channel is NOT affiliated with {credit}
📩 Copyright issues? Contact us for credit/removal.

#shorts #viral #funny #indian #desi #memes #comedy
#{creator_name.replace(' ', '').lower()} #indianmemes #funnyvideos
#trending #2025 #ytshorts #reels
"""

    tags = [
        "shorts", "viral", "funny", "indian", "desi", "memes",
        "comedy", creator_name.replace(" ", "").lower(),
        "indianmemes", "funnyvideos", "trending", "2025",
        "ytshorts", "reels", credit.replace(" ", "").lower(),
        "indianfamily", "relatable",
    ]

    return title[:100], desc, tags[:20]


# =============================================================
#   STEP 6: YOUTUBE UPLOAD
# =============================================================

def get_youtube_service():
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    creds  = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(YOUTUBE_CLIENT_SECRETS):
                print(f"  [SKIP] {YOUTUBE_CLIENT_SECRETS} nahi mila")
                return None
            flow  = InstalledAppFlow.from_client_secrets_file(
                YOUTUBE_CLIENT_SECRETS, SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as f:
            pickle.dump(creds, f)
    return build("youtube", "v3", credentials=creds)


def upload_youtube(path, title, desc, tags):
    print(f"\n  [YouTube] Uploading: {title[:55]}")
    if not os.path.exists(YOUTUBE_CLIENT_SECRETS):
        print("  [SKIP] client_secrets.json nahi mila")
        return None
    try:
        yt   = get_youtube_service()
        if not yt:
            return None
        body = {
            "snippet": {
                "title":       title,
                "description": desc,
                "tags":        tags,
                "categoryId":  "23",   # 23 = Comedy
            },
            "status": {
                "privacyStatus":           "public",
                "selfDeclaredMadeForKids": False,
            },
        }
        media   = MediaFileUpload(path, chunksize=-1, resumable=True)
        request = yt.videos().insert(
            part=",".join(body.keys()), body=body, media_body=media)
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"\r  Upload: {int(status.progress()*100)}%  ",
                      end="", flush=True)
        url = f"https://www.youtube.com/watch?v={response['id']}"
        print(f"\n  [OK] YouTube LIVE: {url}")
        return url
    except Exception as e:
        print(f"\n  [ERROR] YouTube: {e}")
        return None


    try:
        with open(path, "rb") as f:
            resp = requests.post(
                f"https://graph.facebook.com/v18.0/{FACEBOOK_PAGE_ID}/videos",
                timeout=600,
                data={
                    "title":        title[:255],
                    "description":  desc,
                    "access_token": FACEBOOK_PAGE_TOKEN,
                },
                files={"source": f},
            )
        if resp.status_code == 200:
            url = f"https://www.facebook.com/video/{resp.json().get('id')}"
            print(f"  [OK] Facebook LIVE: {url}")
            return url
        print(f"  [ERROR] Facebook {resp.status_code}: {resp.text[:100]}")
        return None
    except Exception as e:
        print(f"  [ERROR] Facebook: {e}")
        return None



# =============================================================
#   FACEBOOK UPLOAD
# =============================================================

def upload_facebook(path, title, desc):
    print(f"\n  [Facebook] Uploading: {title[:55]}")
    if not FACEBOOK_PAGE_TOKEN or FACEBOOK_PAGE_TOKEN == "YOUR_FB_TOKEN":
        print("  [SKIP] Facebook token nahi hai")
        return None
    try:
        with open(path, "rb") as f:
            resp = requests.post(
                f"https://graph.facebook.com/v18.0/{FACEBOOK_PAGE_ID}/videos",
                timeout=600,
                data={
                    "title":        title[:255],
                    "description":  desc,
                    "access_token": FACEBOOK_PAGE_TOKEN,
                },
                files={"source": f},
            )
        if resp.status_code == 200:
            url = f"https://www.facebook.com/video/{resp.json().get('id')}"
            print(f"  [OK] Facebook LIVE: {url}")
            return url
        print(f"  [ERROR] Facebook {resp.status_code}: {resp.text[:100]}")
        return None
    except Exception as e:
        print(f"  [ERROR] Facebook: {e}")
        return None

# =============================================================
#   MAIN PIPELINE
# =============================================================

def process_creator(creator_key, video_url=None):
    """Ek creator ke videos se Shorts banao"""
    creator = CREATORS.get(creator_key)
    if not creator:
        print(f"[ERROR] Creator '{creator_key}' nahi mila!")
        print(f"Available: {list(CREATORS.keys())}")
        return []

    print(f"\n{'='*55}")
    print(f"  CREATOR : {creator['name']}")
    print(f"  TIME    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}")

    results = []

    # Videos ki list lo
    if video_url:
        videos = [{"url": video_url, "title": "Custom Video",
                   "creator": creator["name"], "credit": creator["credit"],
                   "duration": 600}]
    else:
        videos = get_latest_videos(creator_key, count=VIDEOS_PER_RUN + 2)

    if not videos:
        print("  [ERROR] Koi video nahi mila!")
        return []

    processed = 0
    for video in videos:
        if processed >= VIDEOS_PER_RUN:
            break

        print(f"\n  >> Video: {video['title'][:50]}")

        try:
            # Download
            print(f"\n  [Step 1] Downloading...")
            vid_path = download_video(video["url"], creator["name"])

            # Funny moments detect karo
            print(f"\n  [Step 2] Finding funny moments...")
            moments = detect_funny_moments(vid_path, num_clips=CLIPS_PER_VIDEO)

            # Har moment se ek Short banao
            for i, start_time in enumerate(moments):
                print(f"\n  [Step 3] Making Short {i+1}/{len(moments)}...")
                short_path = make_short(
                    vid_path, start_time, creator, video["title"])

                if not short_path:
                    continue

                # Title/desc generate karo
                title, desc, tags = get_title_desc(
                    creator["name"], creator["credit"], video["title"])

                # Upload
                yt_url = upload_youtube(short_path, title, desc, tags)
                fb_url = upload_facebook(short_path, title, desc)

                log = {
                    "time":         datetime.now().isoformat(),
                    "creator":      creator["name"],
                    "source_video": video["title"],
                    "short_file":   short_path,
                    "title":        title,
                    "youtube_url":  yt_url  or "Not configured",
                    "facebook_url": fb_url  or "Not configured",
                    "status":       "SUCCESS",
                }
                results.append(log)
                save_log(log)

                print(f"\n  ✅ Short complete!")
                print(f"     YouTube : {yt_url or 'Not configured'}")
                print(f"     Facebook: {fb_url or 'Not configured'}")

                # Rate limiting — YouTube quota protect karo
                time.sleep(5)

            processed += 1

        except Exception as e:
            print(f"\n  [ERROR] {e}")
            import traceback; traceback.print_exc()
            log = {
                "time":    datetime.now().isoformat(),
                "creator": creator["name"],
                "status":  f"ERROR: {str(e)[:100]}",
            }
            results.append(log)
            save_log(log)

    return results


def save_log(entry):
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except:
            pass
    logs.append(entry)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)


def daily_run():
    """Daily auto run — random creator choose karo"""
    print(f"\n{'='*55}")
    print(f"  DAILY AUTO RUN - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}")

    # Random creator choose karo
    creator_key = random.choice(list(CREATORS.keys()))
    print(f"  Today's creator: {CREATORS[creator_key]['name']}")
    results = process_creator(creator_key)

    print(f"\n  Done! {len(results)} shorts created today.")


def start_scheduler():
    """Daily 12 PM aur 6 PM IST pe chalao"""
    schedule.every().day.at("12:00").do(daily_run)
    schedule.every().day.at("18:00").do(daily_run)
    schedule.every().tuesday.at("15:30").do(daily_run)
    schedule.every().wednesday.at("15:30").do(daily_run)

    print(f"\n[SCHEDULER] Active! Times: 12:00, 15:30(Tue/Wed), 18:00 IST")
    print(f"Ctrl+C se band karo\n")
    while True:
        schedule.run_pending()
        time.sleep(30)


# =============================================================
#   ENTRY POINT
# =============================================================

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  INDIAN MEME SHORTS BOT")
    print(f"  Creators: {', '.join(CREATORS.keys())}")
    print("="*55)
    print()
    print("  python meme_bot.py                         # auto")
    print("  python meme_bot.py --channel sourav        # specific")
    print("  python meme_bot.py --url VIDEO_URL         # specific video")
    print("  python meme_bot.py --schedule              # daily auto")
    print()

    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--channel",  type=str, help="Creator key (sourav/thugesh/amit...)")
    p.add_argument("--url",      type=str, help="Specific YouTube video URL")
    p.add_argument("--schedule", action="store_true")
    args = p.parse_args()

    if args.schedule:
        start_scheduler()
    elif args.channel:
        results = process_creator(args.channel, args.url)
        print(f"\n  Done! {len(results)} shorts created.")
    elif args.url:
        # URL given but no channel — sourav default
        results = process_creator("sourav", args.url)
        print(f"\n  Done! {len(results)} shorts created.")
    else:
        # Default: random creator
        creator_key = random.choice(list(CREATORS.keys()))
        print(f"  Random creator: {CREATORS[creator_key]['name']}\n")
        results = process_creator(creator_key)
        print(f"\n  Done! {len(results)} shorts created.")
        print(f"  Log: {LOG_FILE}")