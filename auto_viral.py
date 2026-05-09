"""
=============================================================
   FULL AUTO VIRAL VIDEO SYSTEM
   Tumhe kuch edit nahi karna - sab automatic!

   CHALANE KA TARIKA:
   python auto_viral.py                    # 1 video abhi
   python auto_viral.py --count 3          # 3 videos abhi
   python auto_viral.py --topic "funny animals"  # specific
   python auto_viral.py --schedule         # daily auto
=============================================================
"""

import os, sys, json, time, pickle, random, requests, schedule
from datetime import datetime

# ── ImageMagick (Windows) ─────────────────────────────────
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

from moviepy.editor import (
    VideoFileClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, ColorClip
)
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# =============================================================
#   SETTINGS - APNI INFO YAHAN DAALO
# =============================================================

PEXELS_API_KEY  = "APNI_PEXELS_KEY_YAHAN"   # pexels.com/api se lo

CHANNEL_NAME    = "MyChannel"                 # Tumhara channel name

TOPICS = [
    "funny animals",
    "cute babies laughing",
    "amazing nature india",
    "street food india",
    "satisfying videos",
    "cute cats dogs",
    "beautiful sunset",
    "funny fails compilation",
]

VIDEO_DURATION  = 59        # seconds (59s = Shorts/Reels best)
VIDEOS_PER_RUN  = 2         # ek run mein kitni videos
DAILY_SCHEDULE  = ["09:00", "17:00"]   # daily kab chalao

YOUTUBE_CLIENT_SECRETS = "client_secrets.json"
FACEBOOK_PAGE_ID       = "APNA_PAGE_ID_YAHAN"
FACEBOOK_PAGE_TOKEN    = "APNA_FB_TOKEN_YAHAN"

CLIPS_FOLDER  = "pexels_clips"
OUTPUT_FOLDER = "final_videos"
LOG_FILE      = "upload_log.json"
FONT          = r"C:\Windows\Fonts\arialbd.ttf"

# =============================================================
#   TITLES + HASHTAGS (auto generate)
# =============================================================

TITLES = {
    "funny animals":           ["Funny Animals That Will Make You LOL 2025!", "Hilarious Animal Moments Compilation 2025", "Try Not To Laugh - Funny Animals 2025"],
    "cute babies laughing":    ["Cute Baby Moments That Melt Your Heart 2025!", "Adorable Baby Compilation 2025", "Baby Funny Moments 2025 - So Cute!"],
    "amazing nature india":    ["Incredible India Nature 2025 - Breathtaking!", "Beautiful India Scenery 2025 - Must Watch", "India Hidden Natural Beauty 2025"],
    "street food india":       ["Amazing Indian Street Food 2025 - Delicious!", "Best Street Food India 2025 - Yummy!", "Indian Street Food 2025 - Will Make You Hungry"],
    "satisfying videos":       ["Most Satisfying Videos 2025 - So Relaxing!", "Extremely Satisfying Compilation 2025", "Oddly Satisfying Moments 2025 - Trending"],
    "cute cats dogs":          ["Cute Cats and Dogs 2025 - Adorable Moments!", "Funniest Pets Compilation 2025", "Wholesome Pet Moments 2025 - Must Watch"],
    "beautiful sunset":        ["Most Beautiful Sunsets 2025 - Relaxing Views", "Stunning Sunset Compilation 2025", "Beautiful Sky Moments 2025 - Peaceful"],
    "funny fails compilation": ["Best Funny Fails 2025 - Try Not To Laugh!", "Epic Fails Compilation 2025 - So Funny!", "Funniest Moments 2025 - Fails and Wins"],
}

HASHTAGS = {
    "funny animals":           "#funnyanimals #animals #cute #viral #shorts #funny #trending #2025",
    "cute babies laughing":    "#cutebaby #baby #adorable #viral #shorts #cute #babies #2025",
    "amazing nature india":    "#india #nature #beautiful #viral #shorts #incredibleindia #2025",
    "street food india":       "#streetfood #india #food #viral #shorts #indianfood #foodie #2025",
    "satisfying videos":       "#satisfying #relaxing #viral #shorts #oddlysatisfying #2025",
    "cute cats dogs":          "#cats #dogs #pets #cute #viral #shorts #funny #animals #2025",
    "beautiful sunset":        "#sunset #nature #beautiful #viral #shorts #sky #peaceful #2025",
    "funny fails compilation": "#fails #funny #compilation #viral #shorts #lol #comedy #2025",
}

def get_title_desc_tags(topic):
    title_list = TITLES.get(topic, [f"Amazing {topic.title()} 2025 - Must Watch!"])
    title      = random.choice(title_list)
    hashtags   = HASHTAGS.get(topic, "#viral #shorts #trending #2025")
    desc = (
        f"{title}\n\n"
        f"Watch this amazing compilation! Like and Subscribe!\n\n"
        f"{hashtags}\n\n"
        f"Videos from Pexels.com (Free License)"
    )
    tags = [t.strip("#") for t in hashtags.split()] + ["viral", "shorts", "2025"]
    return title, desc, tags[:15]

# =============================================================
#   STEP 1: PEXELS SE CLIPS DOWNLOAD
# =============================================================

def download_clips(topic, target_secs=120):
    """Pexels se copyright-free clips download karo"""

    if not PEXELS_API_KEY or PEXELS_API_KEY == "APNI_PEXELS_KEY_YAHAN":
        print("\n[!] PEXELS_API_KEY set nahi hai!")
        print("    1. https://www.pexels.com/api/ jaao")
        print("    2. Free API Key lo")
        print("    3. Script mein PEXELS_API_KEY mein daalo")
        sys.exit(1)

    folder = os.path.join(CLIPS_FOLDER, topic.replace(" ", "_"))
    os.makedirs(folder, exist_ok=True)

    print(f"\n  Pexels search: '{topic}'")
    headers = {"Authorization": PEXELS_API_KEY}
    params  = {"query": topic, "per_page": 15, "orientation": "portrait", "size": "medium"}

    try:
        resp = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=15)
    except Exception as e:
        print(f"  [ERROR] Internet problem: {e}")
        return []

    if resp.status_code == 401:
        print(f"  [ERROR] Pexels API key galat hai! Dobara check karo.")
        return []
    if resp.status_code != 200:
        print(f"  [ERROR] Pexels: {resp.status_code}")
        return []

    videos = resp.json().get("videos", [])
    if not videos:
        print(f"  [WARN] '{topic}' ke liye koi video nahi mila, topic change karo")
        return []

    random.shuffle(videos)
    clips = []
    total = 0

    for v in videos:
        if total >= target_secs:
            break
        dur = v.get("duration", 0)
        if dur < 3 or dur > 30:
            continue

        files     = sorted(v.get("video_files", []), key=lambda x: x.get("height", 0), reverse=True)
        best_file = next((f for f in files if f.get("height", 0) >= 720), files[0] if files else None)
        if not best_file:
            continue

        vid_id   = v["id"]
        filepath = os.path.join(folder, f"{vid_id}.mp4")

        if not os.path.exists(filepath):
            print(f"  Downloading clip {vid_id} ({dur}s)...", end=" ", flush=True)
            try:
                r = requests.get(best_file["link"], stream=True, timeout=60)
                with open(filepath, "wb") as f:
                    for chunk in r.iter_content(512 * 1024):
                        f.write(chunk)
                print("OK")
            except Exception as e:
                print(f"FAIL ({e})")
                if os.path.exists(filepath):
                    os.remove(filepath)
                continue
        else:
            print(f"  Clip {vid_id} already downloaded")

        clips.append({"path": filepath, "duration": dur})
        total += dur

    print(f"  [OK] {len(clips)} clips ready ({total}s total)")
    return clips

# =============================================================
#   STEP 2: VIDEO BANAO - SHORTS FORMAT 9:16
# =============================================================

def make_video(clips, topic, duration=VIDEO_DURATION):
    """Clips ko jodke ek Shorts-ready video banao"""
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    ts     = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = os.path.join(OUTPUT_FOLDER, f"{topic.replace(' ', '_')}_{ts}.mp4")

    print(f"\n  Video compile kar raha hun...")

    W, H      = 1080, 1920   # Shorts/Reels standard
    loaded    = []
    total_dur = 0

    for info in clips:
        if total_dur >= duration:
            break
        try:
            clip   = VideoFileClip(info["path"])
            cw, ch = clip.size

            # Landscape to portrait crop (center)
            if cw > ch:
                new_w = int(ch * W / H)
                new_w = min(new_w, cw)
                x1    = (cw - new_w) // 2
                clip  = clip.crop(x1=x1, y1=0, x2=x1 + new_w, y2=ch)

            # Resize to exact 1080x1920
            clip = clip.resize((W, H))

            # Clip duration limit karo
            need = min(12, duration - total_dur)
            if clip.duration > need:
                start = random.uniform(0, max(0, clip.duration - need - 0.5))
                clip  = clip.subclip(start, start + need)

            # Thodi speed variation (copyright se alag dikhne ke liye)
            clip = clip.speedx(random.uniform(1.0, 1.05))

            # Brightness thodi badha do
            clip = clip.fl_image(lambda f: (f * 1.06).clip(0, 255).astype("uint8"))

            # Audio hatao (tumhari choice ka music baad mein add hoga)
            clip = clip.without_audio()

            loaded.append(clip)
            total_dur += clip.duration
            print(f"    + {os.path.basename(info['path'])} ({clip.duration:.1f}s)")

        except Exception as e:
            print(f"    [SKIP] {os.path.basename(info['path'])}: {e}")

    if not loaded:
        print("  [ERROR] Koi clip process nahi hua!")
        return None

    # Sab clips jodo
    print(f"\n  {len(loaded)} clips jod raha hun...")
    final = concatenate_videoclips(loaded, method="compose")

    # Exactly duration tak trim karo
    if final.duration > duration:
        final = final.subclip(0, duration)

    # Background music add karo
    # music/ folder mein koi bhi royalty-free mp3 rakh do - auto use hoga
    music_folder = "music"
    if os.path.exists(music_folder):
        mp3_files = [f for f in os.listdir(music_folder) if f.lower().endswith('.mp3')]
        if mp3_files:
            music_path = os.path.join(music_folder, random.choice(mp3_files))
            try:
                from moviepy.editor import AudioFileClip
                from moviepy.audio.fx.all import audio_loop, volumex
                from moviepy.audio.AudioClip import CompositeAudioClip
                music = AudioFileClip(music_path)
                if music.duration < final.duration:
                    music = audio_loop(music, duration=final.duration)
                else:
                    music = music.subclip(0, final.duration)
                music = volumex(music, 0.35)
                if final.audio is not None:
                    orig = volumex(final.audio, 0.65)
                    final = final.set_audio(CompositeAudioClip([orig, music]))
                else:
                    final = final.set_audio(music)
                print(f"  [OK] Background music: {os.path.basename(music_path)}")
            except Exception as e:
                print(f"  [WARN] Music error: {e}")
    else:
        print(f"  [TIP] Royalty-free music ke liye 'music' folder banao")
        print(f"        pixabay.com/music se free mp3 download karo")
        print(f"        Original Pexels audio video mein hai")

    # Channel watermark
    try:
        wm_kwargs = {
            "txt":          f"@{CHANNEL_NAME}",
            "fontsize":     42,
            "color":        "white",
            "stroke_color": "black",
            "stroke_width": 2,
        }
        if os.path.exists(FONT):
            wm_kwargs["font"] = FONT

        watermark = (
            TextClip(**wm_kwargs)
            .set_duration(final.duration)
            .set_position(("right", 0.05), relative=True)
        )
        final = CompositeVideoClip([final, watermark])
        print(f"  [OK] Watermark @{CHANNEL_NAME} added")
    except Exception as e:
        print(f"  [WARN] Watermark skip: {e}")

    # Save karo
    print(f"  Saving... (2-5 minute lagenge, wait karo)")
    final.write_videofile(
        output,
        fps         = 30,
        codec       = "libx264",
        audio_codec = "aac",
        preset      = "fast",
        verbose     = False,
        logger      = None,
        threads     = 4,
    )

    size_mb = os.path.getsize(output) / (1024 * 1024)
    print(f"  [OK] Video ready: {output} ({size_mb:.1f} MB)")
    return output

# =============================================================
#   STEP 3A: YOUTUBE UPLOAD
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
            flow  = InstalledAppFlow.from_client_secrets_file(YOUTUBE_CLIENT_SECRETS, SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as f:
            pickle.dump(creds, f)
    return build("youtube", "v3", credentials=creds)


def upload_youtube(path, title, desc, tags):
    print(f"\n  [YouTube] Upload: {title[:55]}")

    if not os.path.exists(YOUTUBE_CLIENT_SECRETS):
        print(f"  [SKIP] client_secrets.json nahi mila")
        print(f"  Setup: https://console.cloud.google.com")
        return None

    try:
        yt   = get_youtube_service()
        body = {
            "snippet": {
                "title":       title[:100],
                "description": desc,
                "tags":        tags,
                "categoryId":  "22",
            },
            "status": {
                "privacyStatus":          "public",
                "selfDeclaredMadeForKids": False,
            },
        }
        media   = MediaFileUpload(path, chunksize=-1, resumable=True)
        request = yt.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"\r  Uploading: {pct}%  ", end="", flush=True)
        url = f"https://www.youtube.com/watch?v={response['id']}"
        print(f"\n  [OK] YouTube LIVE: {url}")
        return url
    except Exception as e:
        print(f"\n  [ERROR] YouTube upload fail: {e}")
        return None

# =============================================================
#   STEP 3B: FACEBOOK UPLOAD
# =============================================================

def upload_facebook(path, title, desc):
    print(f"\n  [Facebook] Upload: {title[:55]}")

    if not FACEBOOK_PAGE_TOKEN or FACEBOOK_PAGE_TOKEN == "APNA_FB_TOKEN_YAHAN":
        print("  [SKIP] Facebook token set nahi hai")
        print("  Setup: https://developers.facebook.com/tools/explorer")
        return None

    try:
        with open(path, "rb") as f:
            resp = requests.post(
                f"https://graph.facebook.com/v18.0/{FACEBOOK_PAGE_ID}/videos",
                timeout = 600,
                data    = {
                    "title":        title[:255],
                    "description":  desc,
                    "access_token": FACEBOOK_PAGE_TOKEN,
                },
                files = {"source": f},
            )

        if resp.status_code == 200:
            vid_id = resp.json().get("id")
            url    = f"https://www.facebook.com/video/{vid_id}"
            print(f"  [OK] Facebook LIVE: {url}")
            return url
        else:
            print(f"  [ERROR] Facebook {resp.status_code}: {resp.text[:150]}")
            return None

    except Exception as e:
        print(f"  [ERROR] Facebook upload fail: {e}")
        return None

# =============================================================
#   MAIN PIPELINE
# =============================================================

def process_one_topic(topic):
    """Ek topic ke liye poora pipeline chalao"""
    print(f"\n{'='*55}")
    print(f"  TOPIC : {topic.upper()}")
    print(f"  TIME  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}")

    log = {
        "topic":  topic,
        "time":   datetime.now().isoformat(),
        "status": "STARTED",
    }

    try:
        # Step 1: Clips download
        clips = download_clips(topic, target_secs=VIDEO_DURATION + 60)
        if not clips:
            log["status"] = "ERROR: No clips downloaded"
            return log

        # Step 2: Video banao
        video = make_video(clips, topic, VIDEO_DURATION)
        if not video:
            log["status"] = "ERROR: Video creation failed"
            return log
        log["video_path"] = video

        # Step 3: Title/desc/tags
        title, desc, tags = get_title_desc_tags(topic)
        log["title"] = title

        # Step 4: Upload karo
        yt_url = upload_youtube(video, title, desc, tags)
        fb_url = upload_facebook(video, title, desc)

        log["youtube_url"]  = yt_url  or "Not configured"
        log["facebook_url"] = fb_url  or "Not configured"
        log["status"]       = "SUCCESS"

    except Exception as e:
        print(f"\n  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        log["status"] = f"ERROR: {e}"

    return log


def save_log(entry):
    """Upload log JSON mein save karo"""
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
    print(f"  Log saved: {LOG_FILE}")


def print_result(log):
    print(f"\n  {'='*45}")
    print(f"  STATUS  : {log['status']}")
    print(f"  TOPIC   : {log['topic']}")
    if log.get("title"):
        print(f"  TITLE   : {log['title'][:55]}")
    if log.get("video_path"):
        print(f"  FILE    : {log['video_path']}")
    if log.get("youtube_url"):
        print(f"  YOUTUBE : {log['youtube_url']}")
    if log.get("facebook_url"):
        print(f"  FACEBOOK: {log['facebook_url']}")
    print(f"  {'='*45}")


def daily_run():
    """Daily scheduled run"""
    print(f"\n{'='*55}")
    print(f"  DAILY AUTO RUN")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}")

    chosen = random.sample(TOPICS, min(VIDEOS_PER_RUN, len(TOPICS)))
    print(f"  Topics: {chosen}")

    for topic in chosen:
        log = process_one_topic(topic)
        save_log(log)
        print_result(log)


def start_scheduler():
    """Daily scheduler start karo"""
    print(f"\n[SCHEDULER] Scheduled times: {DAILY_SCHEDULE}")
    for t in DAILY_SCHEDULE:
        schedule.every().day.at(t).do(daily_run)
        print(f"  Scheduled: Every day at {t}")

    print(f"\n[OK] Scheduler chal raha hai...")
    print(f"  Abhi time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"  Ctrl+C se band karo\n")

    while True:
        schedule.run_pending()
        time.sleep(30)

# =============================================================
#   ENTRY POINT
# =============================================================

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  FULL AUTO VIRAL VIDEO SYSTEM")
    print("  Source: Pexels.com (100% Copyright Free)")
    print("="*55)
    print()
    print("  COMMANDS:")
    print("  python auto_viral.py                         # 1 video abhi")
    print("  python auto_viral.py --count 3               # 3 videos abhi")
    print("  python auto_viral.py --topic 'funny animals' # specific topic")
    print("  python auto_viral.py --schedule              # daily auto run")
    print()

    import argparse
    parser = argparse.ArgumentParser(description="Auto Viral Video System")
    parser.add_argument("--topic",    type=str,            help="Topic name")
    parser.add_argument("--count",    type=int, default=1, help="Kitni videos (default: 1)")
    parser.add_argument("--schedule", action="store_true", help="Daily scheduler chalao")
    args = parser.parse_args()

    if args.schedule:
        # Daily auto run
        start_scheduler()

    elif args.topic:
        # Ek specific topic
        log = process_one_topic(args.topic)
        save_log(log)
        print_result(log)

    else:
        # Default: random topics se videos banao
        chosen = random.sample(TOPICS, min(args.count, len(TOPICS)))
        print(f"  Topics chosen: {chosen}\n")

        for topic in chosen:
            log = process_one_topic(topic)
            save_log(log)
            print_result(log)

        print("\n  Sab complete! Check karo:")
        print(f"  - Videos : {OUTPUT_FOLDER}\\")
        print(f"  - Log    : {LOG_FILE}")