# Viral Video Auto Upload Bot

Pexels se free clips download, edit karke YouTube aur Facebook pe auto upload.

## Setup (ek baar karna hai)

### Step 1 — GitHub Secrets add karo
Repository mein jao: **Settings → Secrets → Actions → New secret**

| Secret Name | Value |
|---|---|
| `PEXELS_API_KEY` | pexels.com/api se free key |
| `CHANNEL_NAME` | Tumhara channel name |
| `FACEBOOK_PAGE_ID` | Facebook Page ID |
| `FACEBOOK_PAGE_TOKEN` | developers.facebook.com se token |
| `YOUTUBE_CLIENT_SECRETS` | client_secrets.json ka content |
| `YOUTUBE_TOKEN` | token.pickle ka base64 |

### Step 2 — YouTube Token banana (ek baar)
Apne PC pe run karo:
```cmd
python auto_viral.py --count 1
```
Browser mein Google login hoga. Token.pickle ban jayega.
Phir token encode karo:
```cmd
python -c "import base64; print(base64.b64encode(open('token.pickle','rb').read()).decode())"
```
Output ko `YOUTUBE_TOKEN` secret mein daalo.

### Step 3 — Enable Actions
GitHub repo mein **Actions tab** jaao → Enable karo

## Daily Schedule
- Subah 9:00 AM IST (3:30 UTC)
- Shaam 5:00 PM IST (11:30 UTC)

## Manual Run
GitHub → Actions → Daily Viral Video → Run workflow

## Local Run
```cmd
python auto_viral.py                         # 1 video
python auto_viral.py --count 3               # 3 videos
python auto_viral.py --topic "funny animals" # specific
python auto_viral.py --schedule              # daily auto
```
