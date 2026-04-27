# ─────────────────────────────────────────────
#  STEP 2 — UPLOAD CREATIVE & LAUNCH AD
#  Run this when your video/image is ready
# ─────────────────────────────────────────────

import requests, json, os, time
from config import AD_ACCOUNT_ID, ACCESS_TOKEN, PAGE_ID, LANDING_PAGE_URL

BASE = "https://graph.facebook.com/v19.0"

def api(method, endpoint, **kwargs):
    url = f"{BASE}/{endpoint}"
    kwargs.setdefault("params", {})["access_token"] = ACCESS_TOKEN
    res = getattr(requests, method)(url, **kwargs)
    data = res.json()
    if "error" in data:
        raise Exception(f"❌ Meta Error: {data['error']['message']}")
    return data


# ── UPLOAD IMAGE ──────────────────────────────
def upload_image(image_path: str) -> str:
    print(f"\n🖼  Uploading image: {image_path}")
    with open(image_path, "rb") as f:
        res = requests.post(
            f"{BASE}/{AD_ACCOUNT_ID}/adimages",
            params={"access_token": ACCESS_TOKEN},
            files={"filename": f}
        )
    data = res.json()
    if "error" in data:
        raise Exception(f"❌ Image upload failed: {data['error']['message']}")
    images = data.get("images", {})
    hash_val = list(images.values())[0]["hash"]
    print(f"✅ Image uploaded! Hash: {hash_val}")
    return hash_val


# ── UPLOAD VIDEO ──────────────────────────────
def upload_video(video_path: str) -> str:
    print(f"\n🎥 Uploading video: {video_path}")
    print("   (This may take 1-2 minutes depending on file size...)")

    # Step 1: Start upload session
    file_size = os.path.getsize(video_path)
    res = requests.post(
        f"https://graph.facebook.com/v19.0/{AD_ACCOUNT_ID}/advideos",
        params={"access_token": ACCESS_TOKEN},
        data={
            "upload_phase": "start",
            "file_size": file_size,
        }
    )
    data = res.json()
    if "error" in data:
        raise Exception(f"❌ Video upload start failed: {data['error']['message']}")

    upload_session_id = data["upload_session_id"]
    video_id = data["video_id"]

    # Step 2: Upload file in chunks
    with open(video_path, "rb") as f:
        chunk_size = 1024 * 1024 * 4  # 4MB chunks
        start_offset = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            res = requests.post(
                f"https://graph.facebook.com/v19.0/{AD_ACCOUNT_ID}/advideos",
                params={"access_token": ACCESS_TOKEN},
                data={
                    "upload_phase": "transfer",
                    "upload_session_id": upload_session_id,
                    "start_offset": start_offset,
                },
                files={"video_file_chunk": chunk}
            )
            d = res.json()
            start_offset = int(d.get("start_offset", start_offset + len(chunk)))
            print(f"   Uploaded {start_offset / file_size * 100:.0f}%...", end="\r")

    # Step 3: Finish upload
    requests.post(
        f"https://graph.facebook.com/v19.0/{AD_ACCOUNT_ID}/advideos",
        params={"access_token": ACCESS_TOKEN},
        data={
            "upload_phase": "finish",
            "upload_session_id": upload_session_id,
        }
    )

    # Step 4: Wait for video to process
    print("\n   Processing video on Meta servers...")
    for _ in range(20):
        time.sleep(10)
        res = requests.get(
            f"{BASE}/{video_id}",
            params={"access_token": ACCESS_TOKEN, "fields": "status"}
        )
        status = res.json().get("status", {}).get("processing_progress", 0)
        print(f"   Processing: {status}%...", end="\r")
        if status >= 100:
            break

    print(f"\n✅ Video uploaded! Video ID: {video_id}")
    return video_id


# ── CREATE AD WITH IMAGE ──────────────────────
def create_ad_with_image(adset_id, copy, image_hash):
    print(f"\n📌 Creating image ad — Variant {copy['variant']}...")

    creative = api("post", f"{AD_ACCOUNT_ID}/adcreatives", json={
        "name": f"Creative-V{copy['variant']}-{copy['angle'][:20]}",
        "object_story_spec": {
            "page_id": PAGE_ID,
            "link_data": {
                "message":     copy["primary_text"],
                "link":        LANDING_PAGE_URL,
                "name":        copy["headline"],
                "description": copy["description"],
                "image_hash":  image_hash,
                "call_to_action": {
                    "type": copy["cta_button"],
                    "value": {"link": LANDING_PAGE_URL}
                }
            }
        }
    })

    ad = api("post", f"{AD_ACCOUNT_ID}/ads", json={
        "name":    f"Ad-V{copy['variant']}-{copy['angle'][:15]}",
        "adset_id": adset_id,
        "creative": {"creative_id": creative["id"]},
        "status":  "PAUSED",
    })
    print(f"✅ Image ad created: {ad['id']}")
    return ad["id"]


# ── CREATE AD WITH VIDEO ──────────────────────
def create_ad_with_video(adset_id, copy, video_id):
    print(f"\n📌 Creating video ad — Variant {copy['variant']}...")

    creative = api("post", f"{AD_ACCOUNT_ID}/adcreatives", json={
        "name": f"Creative-V{copy['variant']}-Video",
        "object_story_spec": {
            "page_id": PAGE_ID,
            "video_data": {
                "video_id":    video_id,
                "message":     copy["primary_text"],
                "title":       copy["headline"],
                "call_to_action": {
                    "type": copy["cta_button"],
                    "value": {"link": LANDING_PAGE_URL}
                }
            }
        }
    })

    ad = api("post", f"{AD_ACCOUNT_ID}/ads", json={
        "name":     f"Ad-V{copy['variant']}-Video",
        "adset_id": adset_id,
        "creative": {"creative_id": creative["id"]},
        "status":   "PAUSED",
    })
    print(f"✅ Video ad created: {ad['id']}")
    return ad["id"]


# ── MAIN UPLOAD FLOW ──────────────────────────
def upload_and_launch():
    print("\n" + "═"*50)
    print("  🎬 UPLOAD CREATIVE & LAUNCH ADS")
    print("═"*50)

    # Load campaign IDs
    if not os.path.exists("campaign_ids.json"):
        print("❌ No campaign found. Run option 2 (Launch Campaign) first!")
        return

    with open("campaign_ids.json") as f:
        ids = json.load(f)

    with open("generated_copies.json") as f:
        copies = json.load(f)

    adset_id = ids["adset_id"]

    print("\nWhat type of creative do you have?")
    print("  1 → Image (JPG, PNG)")
    print("  2 → Video (MP4)")
    choice = input("\nEnter 1 or 2: ").strip()

    if choice == "1":
        path = input("\nDrag & drop your image file here (or type full path): ").strip().strip("'\"")
        image_hash = upload_image(path)

        print(f"\nWhich copy variant to use? (1-{len(copies)})")
        for c in copies:
            print(f"  {c['variant']} → {c['angle']}: {c['hook_line'][:60]}...")
        v = int(input("Enter variant number: ").strip()) - 1
        copy = copies[v]

        ad_id = create_ad_with_image(adset_id, copy, image_hash)

    elif choice == "2":
        path = input("\nDrag & drop your video file here (or type full path): ").strip().strip("'\"")
        video_id = upload_video(path)

        print(f"\nWhich copy variant to use? (1-{len(copies)})")
        for c in copies:
            print(f"  {c['variant']} → {c['angle']}: {c['hook_line'][:60]}...")
        v = int(input("Enter variant number: ").strip()) - 1
        copy = copies[v]

        ad_id = create_ad_with_video(adset_id, copy, video_id)

    else:
        print("Invalid choice")
        return

    # Save the new ad ID
    ids["ads"].append({
        "variant": copy["variant"],
        "angle": copy["angle"],
        "ad_id": ad_id,
        "creative_id": None,
    })
    with open("campaign_ids.json", "w") as f:
        json.dump(ids, f, indent=2)

    print("\n" + "═"*50)
    print("✅ AD CREATED SUCCESSFULLY!")
    print("═"*50)
    print(f"\n📋 Ad is currently PAUSED — review it in Ads Manager")
    print(f"👉 https://adsmanager.facebook.com")
    print(f"\nOnce reviewed → run option 3 to GO LIVE!")
    print("═"*50)


if __name__ == "__main__":
    upload_and_launch()
