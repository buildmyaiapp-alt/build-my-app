# 🚀 Meta Ads Automation — Setup Guide

## What This Does (Full Automation)
```
Meta Ad → AI generates copies → Campaign launches → 
Leads captured → WhatsApp auto-reply → 
Daily performance check → Auto-pause bad ads → Auto-scale winners → Email report
```

---

## STEP 1 — Install Python dependencies
```bash
cd meta-automation
pip install -r requirements.txt
```

---

## STEP 2 — Get Your Meta Credentials

### A. Meta Access Token (Most Important)
1. Go to → https://developers.facebook.com
2. Create an App → Business type
3. Add "Marketing API" product
4. Go to Tools → Graph API Explorer
5. Generate token with these permissions:
   - `ads_management`
   - `ads_read`
   - `leads_retrieval`
   - `pages_manage_ads`
6. Convert to Long-Lived Token (60 days) using:
   ```
   https://graph.facebook.com/v19.0/oauth/access_token?
   grant_type=fb_exchange_token&
   client_id=YOUR_APP_ID&
   client_secret=YOUR_APP_SECRET&
   fb_exchange_token=SHORT_TOKEN
   ```

### B. Ad Account ID
1. Go to → https://business.facebook.com
2. Settings → Ad Accounts
3. Copy the ID (format: act_123456789)

### C. Page ID
1. Go to your Facebook Page
2. Settings → About → Page ID

### D. Anthropic API Key
1. Go to → https://console.anthropic.com
2. API Keys → Create Key
3. Copy it

---

## STEP 3 — Fill in config.py
Open `config.py` and fill in:
- `AD_ACCOUNT_ID`
- `ACCESS_TOKEN`
- `PAGE_ID`
- `ANTHROPIC_API_KEY`
- `LANDING_PAGE_URL` (your landing page)
- `WHATSAPP_NUMBER`
- `DAILY_BUDGET` (start with Rs 300/day)

---

## STEP 4 — Run the Automation
```bash
python run.py
```

Select from menu:
1. Generate AI ad copies
2. Launch campaign (starts PAUSED)
3. Review in Ads Manager → then Activate
4. Check daily performance
5. Process leads + WhatsApp

---

## STEP 5 — WhatsApp Auto-Reply Setup

### Option A: Manual (Free)
- Script generates WhatsApp links for each lead
- You click to send

### Option B: WATI.io (Rs 999/month — Recommended)
1. Sign up at wati.io
2. Connect your WhatsApp Business number
3. Create a message template called "lead_followup"
4. Get API key
5. Enter when prompted in run.py

### Option C: Interakt / AiSensy
- Similar to WATI, just change the API endpoint

---

## STEP 6 — Daily Email Reports
Set environment variables:
```bash
export EMAIL_USER="yourgmail@gmail.com"
export EMAIL_PASS="your_app_password"   # Gmail App Password
```
You'll get daily reports at `palashrajak21@gmail.com`

---

## What Gets Automated
| Task | How Often | What it Does |
|------|-----------|--------------|
| AI Ad Copy Generation | On demand | Claude writes 3-5 variants |
| Campaign Launch | On demand | Creates campaign in Meta |
| Performance Check | Daily 8 PM | Fetches stats for all ads |
| Auto-Pause | Daily | Pauses ads with CPL > Rs 150 |
| Auto-Scale | Daily | Increases budget if CPL < Rs 50 |
| Lead Fetch | Every 2 hrs | Gets new leads from Meta |
| WhatsApp Reply | Every 2 hrs | Auto-messages new leads |
| Email Report | Daily 8 PM | Summary to your email |

---

## Recommended Starting Budget
- Start: Rs 300/day
- Scale to: Rs 500-1000/day when CPL < Rs 80
- Target CPL: Rs 50-80 for Rs 249 webinar

---

## Files Created
```
meta-automation/
├── config.py              ← Your credentials & settings
├── ad_copy_generator.py   ← Claude AI writes ad copies
├── campaign_launcher.py   ← Creates Meta campaign
├── performance_monitor.py ← Stats, auto-optimize, email
├── lead_manager.py        ← Lead capture + WhatsApp
├── run.py                 ← Main menu (run this!)
├── requirements.txt       ← Python packages
├── generated_copies.json  ← AI-generated ad copies
├── campaign_ids.json      ← Your campaign IDs
├── leads.csv              ← All captured leads
└── reports/               ← Daily reports folder
```
