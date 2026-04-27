# ─────────────────────────────────────────────
#  META ADS AUTOMATION — MAIN RUNNER
#  One file to control everything
# ─────────────────────────────────────────────

import sys, os, json, schedule, time
from datetime import datetime

os.makedirs("reports", exist_ok=True)

def banner():
    print("""
╔══════════════════════════════════════════════╗
║   🚀 META ADS AUTOMATION — DREAM APP        ║
║   Full Campaign Manager powered by Claude   ║
╚══════════════════════════════════════════════╝
""")

def menu():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  STEP 1  →  1️⃣  Generate AI ad copies (Claude)
  STEP 2  →  2️⃣  Create campaign on Meta (first time)
  STEP 3  →  3️⃣  Upload your video/image & attach  ⬅ DO THIS WHEN CREATIVE IS READY
  STEP 4  →  4️⃣  Review in Ads Manager then GO LIVE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  DAILY   →  5️⃣  Check performance & auto-optimize
  LEADS   →  6️⃣  Process new leads + WhatsApp reply
  LEADS   →  7️⃣  View all leads summary
  AUTO    →  8️⃣  Start auto-scheduler (8 PM daily)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Q   Quit
""")

def run_generate():
    from ad_copy_generator import generate_ad_copies, print_copies
    n = int(input("How many ad variants? (recommended: 3-5): ") or "3")
    copies = generate_ad_copies(n)
    print_copies(copies)
    with open("generated_copies.json", "w") as f:
        json.dump(copies, f, indent=2, ensure_ascii=False)
    print("✅ Saved to generated_copies.json")
    return copies

def run_launch():
    if not os.path.exists("generated_copies.json"):
        print("❌ No copies found. Run option 1 first.")
        return
    with open("generated_copies.json") as f:
        copies = json.load(f)

    img = input("Image path (leave blank to skip): ").strip() or None
    live = input("Go LIVE immediately? (y/N): ").strip().lower() == "y"

    from campaign_launcher import launch_campaign
    launch_campaign(copies, image_path=img, go_live=live)

def run_activate():
    confirm = input("Are you sure you want to go LIVE? (y/N): ").strip().lower()
    if confirm == "y":
        from campaign_launcher import activate_campaign
        activate_campaign()

def run_check():
    from performance_monitor import run_daily_check
    run_daily_check()

def run_leads():
    form_id = input("Enter your Lead Form ID (from Ads Manager): ").strip()
    wati    = input("WATI API key (leave blank to use WhatsApp links): ").strip() or None
    wati_ep = None
    if wati:
        wati_ep = input("WATI endpoint URL: ").strip()
    from lead_manager import process_new_leads
    process_new_leads(form_id, wati, wati_ep)

def run_leads_summary():
    from lead_manager import print_summary
    print_summary()

def run_scheduler():
    print("\n⏰ Auto-scheduler started — runs daily at 8:00 PM")
    print("   (checks stats, optimizes ads, emails report)")
    print("   Press Ctrl+C to stop\n")

    def daily_job():
        print(f"\n🔔 Running daily check — {datetime.now().strftime('%d %b %Y %H:%M')}")
        from performance_monitor import run_daily_check
        run_daily_check()

    schedule.every().day.at("20:00").do(daily_job)

    # Also run leads check every 2 hours
    def leads_job():
        form_id = os.environ.get("META_FORM_ID")
        if form_id:
            from lead_manager import process_new_leads
            process_new_leads(form_id)

    schedule.every(2).hours.do(leads_job)

    while True:
        schedule.run_pending()
        time.sleep(60)

def run_full_pipeline():
    print("\n🚀 Running FULL PIPELINE: Generate → Launch → Schedule\n")
    copies = run_generate()
    input("\n✅ Copies generated! Press Enter to launch campaign...")
    run_launch()
    input("\n✅ Campaign created! Press Enter to start scheduler...")
    run_scheduler()


# ── MAIN ─────────────────────────────────────
if __name__ == "__main__":
    banner()
    while True:
        menu()
        choice = input("Enter choice: ").strip().upper()
        if   choice == "1": run_generate()
        elif choice == "2": run_launch()
        elif choice == "3":
            from upload_and_launch import upload_and_launch
            upload_and_launch()
        elif choice == "4": run_activate()
        elif choice == "5": run_check()
        elif choice == "6": run_leads()
        elif choice == "7": run_leads_summary()
        elif choice == "8": run_scheduler()
        elif choice == "Q": print("Bye! 👋"); sys.exit(0)
        else: print("Invalid choice.")
        input("\nPress Enter to continue...")
