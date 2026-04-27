# ─────────────────────────────────────────────
#  CLAUDE AI — AD COPY GENERATOR
#  Generates high-converting Meta ad copies
# ─────────────────────────────────────────────

import anthropic
from config import ANTHROPIC_API_KEY, LANDING_PAGE_URL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

PRODUCT_BRIEF = """
Product: Dream App Workshop – Live Online Webinar
Price: Rs 249 (original Rs 999)
Target: Indian business owners (shops, coaching classes, restaurants, gyms, salons, clinics)
Key benefit: Build any mobile/web app in 30 minutes using AI — no coding, no technical knowledge
Hook: No coding needed, just type your idea in plain language and AI builds it
Guarantee: 100% money back guarantee
Urgency: Only 49 seats, early bird price
"""

def generate_ad_copies(n_variants: int = 5) -> list[dict]:
    """Generate n_variants ad copy sets using Claude."""
    print(f"\n🤖 Generating {n_variants} ad copy variants with Claude AI...\n")

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        messages=[{
            "role": "user",
            "content": f"""You are an expert Meta (Facebook/Instagram) ads copywriter for the Indian market.

Product Details:
{PRODUCT_BRIEF}

Generate {n_variants} DIFFERENT high-converting Meta ad copy variants.
Each variant must have a different HOOK / angle to test.

Angles to cover across variants:
1. Fear of missing out (competitors have apps, you don't)
2. Dream outcome (imagine having your own app)
3. Price shock (developer charges 2 lakhs, we charge 249)
4. Proof (students already built apps in 30 min)
5. Curiosity (secret method to build any app)

For EACH variant return EXACTLY this JSON format (return a JSON array):
{{
  "variant": 1,
  "angle": "Fear of missing out",
  "primary_text": "...(3-4 lines, conversational, Hindi-English mix ok, emoji ok)...",
  "headline": "...(max 8 words, punchy)...",
  "description": "...(1 line benefit + CTA)...",
  "cta_button": "LEARN_MORE" or "SIGN_UP" or "GET_QUOTE",
  "hook_line": "...(first line that stops the scroll)..."
}}

Return ONLY the JSON array, no other text.
Make copies feel natural, relatable to Indian small business owners.
Use Hindi words naturally (like "apna app", "ekdam asaan", etc.)
"""
        }]
    )

    import json
    raw = message.content[0].text.strip()
    # Clean up if wrapped in code blocks
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    variants = json.loads(raw.strip())
    print(f"✅ Generated {len(variants)} ad copy variants!\n")
    return variants


def print_copies(variants: list[dict]):
    """Pretty-print all variants to terminal."""
    for v in variants:
        print("─" * 60)
        print(f"VARIANT {v['variant']} — Angle: {v['angle']}")
        print(f"\n🎣 HOOK:  {v['hook_line']}")
        print(f"\n📝 PRIMARY TEXT:\n{v['primary_text']}")
        print(f"\n💬 HEADLINE:    {v['headline']}")
        print(f"📌 DESCRIPTION: {v['description']}")
        print(f"🔘 CTA BUTTON:  {v['cta_button']}")
        print()


if __name__ == "__main__":
    variants = generate_ad_copies(5)
    print_copies(variants)

    # Save to file
    import json
    with open("generated_copies.json", "w") as f:
        json.dump(variants, f, indent=2, ensure_ascii=False)
    print("✅ Saved to generated_copies.json")
