# ─────────────────────────────────────────────
#  META ADS — CAMPAIGN LAUNCHER
#  Creates full campaign: Campaign → Ad Set → Ads
# ─────────────────────────────────────────────

import requests
import json
from datetime import datetime
from config import (
    AD_ACCOUNT_ID, ACCESS_TOKEN, PAGE_ID, INSTAGRAM_ACTOR_ID,
    CAMPAIGN_NAME, DAILY_BUDGET, LANDING_PAGE_URL, TARGETING
)

BASE = "https://graph.facebook.com/v19.0"
HEADERS = {"Content-Type": "application/json"}

def api(method, endpoint, **kwargs):
    """Wrapper for Meta Graph API calls."""
    url = f"{BASE}/{endpoint}"
    kwargs.setdefault("params", {})["access_token"] = ACCESS_TOKEN
    res = getattr(requests, method)(url, **kwargs)
    data = res.json()
    if "error" in data:
        raise Exception(f"Meta API Error: {data['error']['message']}")
    return data


# ── STEP 1: Create Campaign ───────────────────
def create_campaign() -> str:
    print("📣 Creating campaign...")
    data = api("post", f"{AD_ACCOUNT_ID}/campaigns", json={
        "name": f"{CAMPAIGN_NAME} – {datetime.now().strftime('%d %b %Y')}",
        "objective": "OUTCOME_LEADS",          # Lead generation
        "status": "PAUSED",                    # Start paused — review before going live
        "special_ad_categories": [],
        "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
    })
    campaign_id = data["id"]
    print(f"✅ Campaign created: {campaign_id}")
    return campaign_id


# ── STEP 2: Create Ad Set ─────────────────────
def create_adset(campaign_id: str, budget_override: int = None) -> str:
    print("🎯 Creating ad set with targeting...")
    daily_budget = (budget_override or DAILY_BUDGET) * 100  # Meta uses paise

    data = api("post", f"{AD_ACCOUNT_ID}/adsets", json={
        "name": f"India – Business Owners – {datetime.now().strftime('%d%m')}",
        "campaign_id": campaign_id,
        "daily_budget": daily_budget,
        "billing_event": "IMPRESSIONS",
        "optimization_goal": "LEAD_GENERATION",
        "targeting": TARGETING,
        "status": "PAUSED",
        "start_time": datetime.now().isoformat(),
    })
    adset_id = data["id"]
    print(f"✅ Ad set created: {adset_id}")
    return adset_id


# ── STEP 3: Create Ad Creative ────────────────
def create_creative(copy: dict, image_hash: str = None) -> str:
    print(f"🎨 Creating creative for Variant {copy['variant']}...")

    link_data = {
        "message": copy["primary_text"],
        "link": LANDING_PAGE_URL,
        "name": copy["headline"],
        "description": copy["description"],
        "call_to_action": {
            "type": copy["cta_button"],
            "value": {"link": LANDING_PAGE_URL}
        },
    }
    if image_hash:
        link_data["image_hash"] = image_hash

    object_story_spec = {
        "page_id": PAGE_ID,
        "link_data": link_data,
    }
    if INSTAGRAM_ACTOR_ID:
        object_story_spec["instagram_actor_id"] = INSTAGRAM_ACTOR_ID

    data = api("post", f"{AD_ACCOUNT_ID}/adcreatives", json={
        "name": f"Creative – Variant {copy['variant']} – {copy['angle']}",
        "object_story_spec": object_story_spec,
    })
    creative_id = data["id"]
    print(f"✅ Creative created: {creative_id}")
    return creative_id


# ── STEP 4: Create Ad ─────────────────────────
def create_ad(adset_id: str, creative_id: str, variant_num: int) -> str:
    print(f"📌 Creating ad for Variant {variant_num}...")
    data = api("post", f"{AD_ACCOUNT_ID}/ads", json={
        "name": f"Ad – Variant {variant_num} – {datetime.now().strftime('%d%m%H%M')}",
        "adset_id": adset_id,
        "creative": {"creative_id": creative_id},
        "status": "PAUSED",
    })
    ad_id = data["id"]
    print(f"✅ Ad created: {ad_id}")
    return ad_id


# ── STEP 5: Upload Image ──────────────────────
def upload_image(image_path: str) -> str:
    print(f"🖼  Uploading image: {image_path}")
    with open(image_path, "rb") as f:
        data = api("post", f"{AD_ACCOUNT_ID}/adimages",
                   files={"filename": f},
                   params={"access_token": ACCESS_TOKEN})
    # Response structure: {"images": {"filename": {"hash": "..."}}}
    images = data.get("images", {})
    hash_val = list(images.values())[0]["hash"]
    print(f"✅ Image uploaded. Hash: {hash_val}")
    return hash_val


# ── LAUNCH FULL CAMPAIGN ─────────────────────
def launch_campaign(copies: list[dict], image_path: str = None, go_live: bool = False):
    """
    Create a full campaign with multiple ad variants.
    By default starts everything PAUSED so you can review before going live.
    Set go_live=True to activate immediately.
    """
    print("\n" + "═"*50)
    print("  🚀 LAUNCHING META AD CAMPAIGN")
    print("═"*50 + "\n")

    results = {"campaign_id": None, "adset_id": None, "ads": []}

    # Image (optional)
    image_hash = None
    if image_path:
        image_hash = upload_image(image_path)

    # Campaign
    campaign_id = create_campaign()
    results["campaign_id"] = campaign_id

    # Ad Set
    adset_id = create_adset(campaign_id)
    results["adset_id"] = adset_id

    # One ad per copy variant
    for copy in copies:
        creative_id = create_creative(copy, image_hash)
        ad_id = create_ad(adset_id, creative_id, copy["variant"])
        results["ads"].append({
            "variant": copy["variant"],
            "angle": copy["angle"],
            "creative_id": creative_id,
            "ad_id": ad_id,
        })

    # Save IDs
    with open("campaign_ids.json", "w") as f:
        json.dump(results, f, indent=2)

    # Optionally go live
    if go_live:
        print("\n⚡ Activating campaign...")
        api("post", f"{campaign_id}", json={"status": "ACTIVE"})
        api("post", f"{adset_id}",    json={"status": "ACTIVE"})
        for ad in results["ads"]:
            api("post", f"{ad['ad_id']}", json={"status": "ACTIVE"})
        print("✅ Campaign is LIVE!")
    else:
        print("\n⏸  Campaign created in PAUSED state.")
        print("👉 Review in Ads Manager, then call activate_campaign() to go live.\n")

    print("═"*50)
    print(f"  Campaign ID : {campaign_id}")
    print(f"  Ad Set ID   : {adset_id}")
    print(f"  Ads created : {len(results['ads'])}")
    print("═"*50)
    return results


def activate_campaign():
    """Activate a previously created (paused) campaign."""
    with open("campaign_ids.json") as f:
        ids = json.load(f)
    api("post", ids["campaign_id"], json={"status": "ACTIVE"})
    api("post", ids["adset_id"],    json={"status": "ACTIVE"})
    for ad in ids["ads"]:
        api("post", ad["ad_id"], json={"status": "ACTIVE"})
    print("✅ Campaign is now LIVE!")


if __name__ == "__main__":
    from ad_copy_generator import generate_ad_copies
    copies = generate_ad_copies(3)
    launch_campaign(copies, image_path=None, go_live=False)
