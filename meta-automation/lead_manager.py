# ─────────────────────────────────────────────
#  META ADS — LEAD MANAGER
#  Captures leads from Meta & sends WhatsApp auto-reply
# ─────────────────────────────────────────────

import requests, json, csv, os
from datetime import datetime
from config import ACCESS_TOKEN, LANDING_PAGE_URL, WHATSAPP_NUMBER, WHATSAPP_MSG

BASE = "https://graph.facebook.com/v19.0"

def api(endpoint, **params):
    params["access_token"] = ACCESS_TOKEN
    res = requests.get(f"{BASE}/{endpoint}", params=params)
    return res.json()


# ── FETCH LEADS FROM META ─────────────────────
def fetch_leads(form_id: str) -> list[dict]:
    """
    Fetch all leads from a Meta Lead Form.
    form_id: get from Ads Manager → Lead Forms
    """
    print(f"\n📥 Fetching leads from form {form_id}...")
    leads = []
    url = f"{form_id}/leads"
    params = {"fields": "id,created_time,field_data", "limit": 100}

    while True:
        res = api(url, **params)
        for lead in res.get("data", []):
            fields = {f["name"]: f["values"][0] for f in lead["field_data"]}
            leads.append({
                "lead_id":    lead["id"],
                "created":    lead["created_time"],
                "name":       fields.get("full_name", ""),
                "phone":      fields.get("phone_number", ""),
                "email":      fields.get("email", ""),
                "city":       fields.get("city", ""),
                "business":   fields.get("what_type_of_business", ""),
            })
        # Pagination
        next_url = res.get("paging", {}).get("next")
        if not next_url:
            break
        url = next_url  # full URL already

    print(f"✅ Fetched {len(leads)} leads")
    return leads


# ── SAVE LEADS TO CSV ─────────────────────────
def save_leads_csv(leads: list[dict], filename="leads.csv"):
    if not leads:
        print("No leads to save.")
        return
    keys = leads[0].keys()
    file_exists = os.path.exists(filename)
    existing_ids = set()
    if file_exists:
        with open(filename) as f:
            reader = csv.DictReader(f)
            existing_ids = {row["lead_id"] for row in reader}

    new_leads = [l for l in leads if l["lead_id"] not in existing_ids]
    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_leads)
    print(f"💾 {len(new_leads)} new leads saved to {filename}")
    return new_leads


# ── SEND WHATSAPP MESSAGE ─────────────────────
def send_whatsapp(phone: str, name: str):
    """
    Opens WhatsApp web link for manual sending.
    For full automation, use Interakt / WATI / AiSensy API.
    """
    msg = WHATSAPP_MSG.format(landing_page=LANDING_PAGE_URL)
    msg = f"Hi {name}! 👋\n\n" + msg
    import urllib.parse
    encoded = urllib.parse.quote(msg)
    # Clean phone number
    phone = phone.replace(" ", "").replace("-", "").replace("+", "")
    if not phone.startswith("91"):
        phone = "91" + phone
    wa_link = f"https://wa.me/{phone}?text={encoded}"
    print(f"📱 WhatsApp link for {name}: {wa_link}")
    return wa_link


# ── AUTO-REPLY VIA WATI API ───────────────────
def send_whatsapp_wati(phone: str, name: str, wati_api_key: str, wati_endpoint: str):
    """
    Auto-send WhatsApp using WATI (wati.io) API — most affordable for India.
    Sign up at wati.io, get API key.
    """
    phone = phone.replace(" ", "").replace("-", "").replace("+", "")
    if not phone.startswith("91"):
        phone = "91" + phone

    headers = {
        "Authorization": f"Bearer {wati_api_key}",
        "Content-Type": "application/json",
    }
    msg = WHATSAPP_MSG.format(landing_page=LANDING_PAGE_URL)
    payload = {
        "template_name": "lead_followup",   # create this template in WATI dashboard
        "broadcast_name": f"lead_{datetime.now().strftime('%Y%m%d%H%M')}",
        "parameters": [
            {"name": "name", "value": name},
            {"name": "landing_page", "value": LANDING_PAGE_URL},
        ],
    }
    res = requests.post(
        f"{wati_endpoint}/api/v1/sendTemplateMessage?whatsappNumber={phone}",
        headers=headers, json=payload
    )
    print(f"📱 WhatsApp sent to {name} ({phone}): {res.status_code}")
    return res.json()


# ── PROCESS NEW LEADS ─────────────────────────
def process_new_leads(form_id: str, wati_key: str = None, wati_endpoint: str = None):
    """Full pipeline: fetch → save → WhatsApp all new leads."""
    all_leads  = fetch_leads(form_id)
    new_leads  = save_leads_csv(all_leads)

    if not new_leads:
        print("No new leads to process.")
        return

    print(f"\n📤 Sending WhatsApp to {len(new_leads)} new leads...")
    for lead in new_leads:
        name  = lead["name"] or "Friend"
        phone = lead["phone"]
        if not phone:
            print(f"⚠️  No phone for lead {lead['lead_id']} — skipping")
            continue

        if wati_key and wati_endpoint:
            send_whatsapp_wati(phone, name, wati_key, wati_endpoint)
        else:
            # Fallback: generate link for manual sending
            send_whatsapp(phone, name)

    print(f"\n✅ Processed {len(new_leads)} new leads!")


# ── PRINT LEADS SUMMARY ───────────────────────
def print_summary():
    if not os.path.exists("leads.csv"):
        print("No leads file found.")
        return
    with open("leads.csv") as f:
        leads = list(csv.DictReader(f))
    print(f"\n📊 TOTAL LEADS: {len(leads)}")
    cities   = {}
    business = {}
    for l in leads:
        c = l.get("city", "Unknown")
        b = l.get("business", "Unknown")
        cities[c]   = cities.get(c, 0) + 1
        business[b] = business.get(b, 0) + 1
    print("\nTop Cities:")
    for c, n in sorted(cities.items(), key=lambda x: -x[1])[:5]:
        print(f"  {c}: {n}")
    print("\nBusiness Types:")
    for b, n in sorted(business.items(), key=lambda x: -x[1])[:5]:
        print(f"  {b}: {n}")


if __name__ == "__main__":
    # Replace with your lead form ID from Ads Manager
    FORM_ID = "YOUR_LEAD_FORM_ID"
    process_new_leads(FORM_ID)
    print_summary()
