# ─────────────────────────────────────────────
#  META ADS — PERFORMANCE MONITOR & AUTO-OPTIMIZER
#  Runs daily: checks stats, pauses bad ads, scales winners
# ─────────────────────────────────────────────

import requests, json, smtplib, os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from config import (
    ACCESS_TOKEN, NOTIFY_EMAIL,
    PAUSE_AD_IF_CPL_ABOVE, SCALE_AD_IF_CPL_BELOW,
    SCALE_BUDGET_BY, MIN_LEADS_TO_OPTIMIZE, MAX_DAILY_SPEND
)

BASE = "https://graph.facebook.com/v19.0"

def api(method, endpoint, **kwargs):
    url = f"{BASE}/{endpoint}"
    kwargs.setdefault("params", {})["access_token"] = ACCESS_TOKEN
    res = getattr(requests, method)(url, **kwargs)
    data = res.json()
    if "error" in data:
        raise Exception(f"API Error: {data['error']['message']}")
    return data


def get_campaign_stats() -> dict:
    """Fetch today's stats for all ads in campaign_ids.json."""
    with open("campaign_ids.json") as f:
        ids = json.load(f)

    today = datetime.now().strftime("%Y-%m-%d")
    stats = {"campaign_id": ids["campaign_id"], "ads": [], "totals": {}}

    total_spend = 0
    total_leads = 0
    total_impressions = 0
    total_clicks = 0

    for ad in ids["ads"]:
        ad_id = ad["ad_id"]
        res = api("get", f"{ad_id}/insights", params={
            "fields": "spend,actions,impressions,clicks,cpm,ctr",
            "time_range": json.dumps({"since": today, "until": today}),
        })

        if not res.get("data"):
            continue

        d = res["data"][0]
        spend = float(d.get("spend", 0))
        impressions = int(d.get("impressions", 0))
        clicks = int(d.get("clicks", 0))
        leads = next(
            (int(a["value"]) for a in d.get("actions", []) if a["action_type"] == "lead"),
            0
        )
        cpl = round(spend / leads, 2) if leads > 0 else None
        ctr = round(float(d.get("ctr", 0)), 2)
        cpm = round(float(d.get("cpm", 0)), 2)

        ad_stat = {
            "ad_id": ad_id,
            "variant": ad["variant"],
            "angle": ad["angle"],
            "spend": spend,
            "impressions": impressions,
            "clicks": clicks,
            "leads": leads,
            "cpl": cpl,
            "ctr": ctr,
            "cpm": cpm,
        }
        stats["ads"].append(ad_stat)

        total_spend += spend
        total_leads += leads
        total_impressions += impressions
        total_clicks += clicks

    stats["totals"] = {
        "spend": round(total_spend, 2),
        "leads": total_leads,
        "impressions": total_impressions,
        "clicks": total_clicks,
        "cpl": round(total_spend / total_leads, 2) if total_leads > 0 else None,
        "ctr": round(total_clicks / total_impressions * 100, 2) if total_impressions > 0 else 0,
    }
    return stats


def auto_optimize(stats: dict) -> list[str]:
    """Auto-pause bad ads, scale good ads. Returns list of actions taken."""
    actions = []
    with open("campaign_ids.json") as f:
        ids = json.load(f)

    # Safety: pause everything if daily spend exceeded
    if stats["totals"]["spend"] >= MAX_DAILY_SPEND:
        api("post", ids["campaign_id"], json={"status": "PAUSED"})
        actions.append(f"🛑 PAUSED CAMPAIGN — Daily spend cap Rs {MAX_DAILY_SPEND} reached!")
        return actions

    for ad in stats["ads"]:
        cpl   = ad["cpl"]
        leads = ad["leads"]
        ad_id = ad["ad_id"]

        if leads < MIN_LEADS_TO_OPTIMIZE:
            actions.append(f"⏳ Variant {ad['variant']}: only {leads} leads — waiting for more data")
            continue

        if cpl and cpl > PAUSE_AD_IF_CPL_ABOVE:
            api("post", ad_id, json={"status": "PAUSED"})
            actions.append(f"⏸  Variant {ad['variant']} PAUSED — CPL Rs {cpl} > Rs {PAUSE_AD_IF_CPL_ABOVE}")

        elif cpl and cpl < SCALE_AD_IF_CPL_BELOW:
            # Find adset and increase budget
            adset_id = ids["adset_id"]
            adset = api("get", adset_id, params={"fields": "daily_budget"})
            current = int(adset["daily_budget"])
            new_budget = int(current * SCALE_BUDGET_BY)
            api("post", adset_id, json={"daily_budget": new_budget})
            actions.append(
                f"📈 Variant {ad['variant']} SCALED — CPL Rs {cpl} < Rs {SCALE_AD_IF_CPL_BELOW}. "
                f"Budget Rs {current//100} → Rs {new_budget//100}"
            )
        else:
            actions.append(f"✅ Variant {ad['variant']}: CPL Rs {cpl} — within range, running")

    return actions


def generate_report(stats: dict, actions: list[str]) -> str:
    """Generate a human-readable daily report."""
    t = stats["totals"]
    lines = [
        "═" * 50,
        f"  📊 META ADS DAILY REPORT — {datetime.now().strftime('%d %b %Y')}",
        "═" * 50,
        "",
        f"  💰 Total Spend    : Rs {t['spend']}",
        f"  👤 Total Leads    : {t['leads']}",
        f"  📉 Cost per Lead  : Rs {t['cpl'] or 'N/A'}",
        f"  👁  Impressions    : {t['impressions']:,}",
        f"  🖱  Clicks         : {t['clicks']:,}",
        f"  📊 CTR            : {t['ctr']}%",
        "",
        "  ── AD BREAKDOWN ──",
    ]
    for ad in stats["ads"]:
        lines.append(
            f"  Variant {ad['variant']} ({ad['angle'][:25]}): "
            f"Rs {ad['spend']} spent | {ad['leads']} leads | "
            f"CPL Rs {ad['cpl'] or 'N/A'} | CTR {ad['ctr']}%"
        )
    lines += [
        "",
        "  ── AUTO-OPTIMIZATION ACTIONS ──",
    ]
    lines += [f"  {a}" for a in actions]
    lines += ["", "═" * 50]
    return "\n".join(lines)


def send_email_report(report: str):
    """Send the daily report to your email."""
    # Uses Gmail SMTP — set EMAIL_USER and EMAIL_PASS as environment variables
    user = os.environ.get("EMAIL_USER")
    pwd  = os.environ.get("EMAIL_PASS")
    if not user or not pwd:
        print("⚠️  EMAIL_USER / EMAIL_PASS env vars not set — skipping email")
        return
    msg = MIMEText(report)
    msg["Subject"] = f"Meta Ads Daily Report — {datetime.now().strftime('%d %b')}"
    msg["From"]    = user
    msg["To"]      = NOTIFY_EMAIL
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pwd)
        s.send_message(msg)
    print(f"📧 Report emailed to {NOTIFY_EMAIL}")


def run_daily_check():
    print("\n🔍 Fetching stats...")
    stats   = get_campaign_stats()
    actions = auto_optimize(stats)
    report  = generate_report(stats, actions)
    print(report)
    send_email_report(report)

    # Save report
    with open(f"reports/report_{datetime.now().strftime('%Y%m%d')}.txt", "w") as f:
        f.write(report)
    with open(f"reports/stats_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
        json.dump(stats, f, indent=2)
    print("✅ Report saved.")


if __name__ == "__main__":
    os.makedirs("reports", exist_ok=True)
    run_daily_check()
