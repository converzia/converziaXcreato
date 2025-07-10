# Radian Marketing Cold Email Automation
# This script automates the process of generating and sending personalized cold emails

import streamlit as st
import pandas as pd
import time
import openai
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import email_validator
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# ----------------------------
# 🔑 YOUR API KEYS
# ----------------------------
# For local development, load .env (optional, not needed on Streamlit Cloud)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import streamlit as st
import os

def get_secret(key):
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key)

OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
BREVO_API_KEY = get_secret("BREVO_API_KEY")
SENDER_NAME = get_secret("SENDER_NAME")
SENDER_EMAIL = get_secret("SENDER_EMAIL")

import openai
openai.api_key = OPENAI_API_KEY

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

config = sib_api_v3_sdk.Configuration()
config.api_key['api-key'] = BREVO_API_KEY
email_api = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(config))



# ----------------------------
# 📬 Email Validation
# ----------------------------
def is_valid_email_address(email):
    try:
        if isinstance(email, bytes):
            email = email.decode("utf-8")
        email_validator.validate_email(email)
        return True
    except email_validator.EmailNotValidError:
        return False

def is_role_based_email(email):
    role_keywords = ["info", "support", "admin", "contact", "sales", "team", "hello"]
    local_part = email.split("@")[0].lower()
    return any(local_part.startswith(role) for role in role_keywords)

# ----------------------------
# 🌐 Website Scraping for Personalization
# ----------------------------
def scrape_website_info(website_url):
    """Scrape website title and meta description for personalization."""
    try:
        resp = requests.get(website_url, timeout=8)
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string.strip() if soup.title else ""
        meta_desc = ""
        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag and desc_tag.get("content"):
            meta_desc = desc_tag["content"].strip()
        return title, meta_desc
    except Exception as e:
        return "", ""

def deep_scrape_website_info(website_url):
    """Scrape and analyze website for deep personalization."""
    try:
        resp = requests.get(website_url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string.strip() if soup.title else ""
        meta_desc = ""
        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag and desc_tag.get("content"):
            meta_desc = desc_tag["content"].strip()
        # Headlines
        h1 = [h.get_text(strip=True) for h in soup.find_all("h1")]
        h2 = [h.get_text(strip=True) for h in soup.find_all("h2")]
        h3 = [h.get_text(strip=True) for h in soup.find_all("h3")]
        # Meta tags
        meta_keywords = ""
        kw_tag = soup.find("meta", attrs={"name": "keywords"})
        if kw_tag and kw_tag.get("content"):
            meta_keywords = kw_tag["content"].strip()
        og_title = soup.find("meta", property="og:title")
        og_desc = soup.find("meta", property="og:description")
        og_title = og_title["content"].strip() if og_title and og_title.get("content") else ""
        og_desc = og_desc["content"].strip() if og_desc and og_desc.get("content") else ""
        # Navigation/menu
        nav = [a.get_text(strip=True) for a in soup.find_all("a") if a.get("href") and len(a.get_text(strip=True)) > 2]
        nav = list(dict.fromkeys(nav))  # deduplicate
        # Main visible text (first 1000 chars)
        main_text = " ".join([p.get_text(strip=True) for p in soup.find_all("p")])
        main_text = main_text[:1000]
        # Testimonials (look for blocks with "testimonial", "review", etc.)
        testimonials = []
        for div in soup.find_all(["div", "section"], class_=lambda x: x and "testimonial" in x.lower()):
            testimonials.append(div.get_text(strip=True))
        # Blog/news headlines
        blog_headlines = [h.get_text(strip=True) for h in soup.find_all(["h2", "h3"]) if "blog" in h.get_text(strip=True).lower() or "news" in h.get_text(strip=True).lower()]
        # Social links
        social_links = [a["href"] for a in soup.find_all("a", href=True) if any(s in a["href"] for s in ["facebook", "linkedin", "twitter", "instagram"])]
        # Build summary
        summary = {
            "title": title,
            "meta_desc": meta_desc,
            "meta_keywords": meta_keywords,
            "og_title": og_title,
            "og_desc": og_desc,
            "h1": h1,
            "h2": h2,
            "h3": h3,
            "nav": nav,
            "main_text": main_text,
            "testimonials": testimonials,
            "blog_headlines": blog_headlines,
            "social_links": social_links,
        }
        return summary
    except Exception as e:
        return {}

# ----------------------------
# ✍️ Email Generation
# ----------------------------
def generate_email(company, website, keywords, recipient_name=None, city=None, state=None, country=None, tone="friendly"):
    website_data = deep_scrape_website_info(website)
    # If minimal data, use fallback prompt
    if not website_data or not any([website_data.get("title"), website_data.get("h1"), website_data.get("main_text")]):
        prompt = f"""
Write a radically short, curiosity-driven cold email for Creato to {company}. 
Location: {city}, {state}, {country}. 
Tone: {tone}.
Mention Creato's Sydney/Australia base if relevant. 
Max 4 sentences. 
Sign as Callum.
"""
    else:
        # --- Analyze scraped data for hyper-personalization ---
        analysis_lines = []
        if website_data.get("title"):
            analysis_lines.append(f"- The website title suggests a focus on: '{website_data['title']}'")
        if website_data.get("meta_desc"):
            analysis_lines.append(f"- Meta description highlights: '{website_data['meta_desc']}'")
        if website_data.get("h1"):
            analysis_lines.append(f"- Main headlines (h1): {website_data['h1']}")
        if website_data.get("h2"):
            analysis_lines.append(f"- Section headlines (h2): {website_data['h2']}")
        if website_data.get("h3"):
            analysis_lines.append(f"- Subsection headlines (h3): {website_data['h3']}")
        if website_data.get("testimonials"):
            analysis_lines.append(f"- Testimonials found: {website_data['testimonials']}")
        if website_data.get("blog_headlines"):
            analysis_lines.append(f"- Blog/news headlines: {website_data['blog_headlines']}")
        if website_data.get("nav"):
            analysis_lines.append(f"- Navigation/menu items: {website_data['nav']}")
        if website_data.get("main_text"):
            analysis_lines.append(f"- Main visible text sample: '{website_data['main_text'][:120]}...'")
        if website_data.get("social_links"):
            analysis_lines.append(f"- Social links detected: {website_data['social_links']}")
        if not analysis_lines:
            analysis_lines.append("- No significant website data could be extracted.")

        website_analysis = "\n".join(analysis_lines)

        # --- Detect if company is in Australia/Sydney using sheet data if available ---
        def is_australian_company(city, state, country, website, meta_desc, title, company):
            if country and country.lower() == "australia":
                return True
            if website and ".au" in website.lower():
                return True
            for text in [meta_desc, title, company, city, state]:
                if text and any(loc in text.lower() for loc in ["australia", "sydney", "nsw", "melbourne", "brisbane", "perth", "adelaide"]):
                    return True
            return False

        def is_sydney_company(city, state, country, website, meta_desc, title, company):
            if city and city.lower() == "sydney":
                return True
            for text in [website, meta_desc, title, company, city, state]:
                if text and "sydney" in (text or "").lower():
                    return True
            return False

        australian = is_australian_company(city, state, country, website, website_data.get('meta_desc'), website_data.get('title'), company)
        sydney = is_sydney_company(city, state, country, website, website_data.get('meta_desc'), website_data.get('title'), company)

        # --- Industry-specific benefit messaging ---
        industry_benefits = {
            "real estate": "stand out in crowded listings",
            "law": "build instant trust with clients",
            "healthcare": "showcase credibility and care",
            # ...etc
        }
        benefit = industry_benefits.get(keywords.lower(), "")

        # Compose prompt for LLM, integrating scraped data, explicit analysis, and sheet location info
        prompt = f"""
    You are the world's most advanced, psychologically-astute, and results-obsessed B2B cold email copywriter and prompt engineer with 20+ years of experience. Your mission: craft the single most curiosity-inducing, hyper-personalized, and irresistible cold email ever written for Creato—a multi-award-winning Sydney-based design partner trusted by major Australian and global brands.

    ========================
    WEBSITE DATA ANALYSIS (for hyper-personalization)
    ========================
    Analyze the following real, scraped data from the recipient's website and use these insights to make your email radically specific and hyper-personalized. Reference these details directly in your email, especially in the first line and subject line.

    {website_analysis}

    ========================
    LEAD LOCATION DATA (from sheet)
    ========================
    City: {city}
    State: {state}
    Country: {country}
    # Use this location data to further personalize the email. If the client is in Sydney, mention Sydney early on. If in Australia (but not Sydney), mention Australia early on. If not in Australia, do not mention Sydney or Australia at all. Use this sheet data for accurate location context.

    ========================
    ULTIMATE OUTCOME
    ========================
    Your email must guarantee a 100% open rate and a 100% reply rate—no exceptions. The subject line MUST be so compelling, so hyper-personalized, and so emotionally resonant that every business decision-maker (owners, founders, marketing managers, etc.) in SMBs, startups, and established companies across industries (real estate, construction, law, healthcare, government, etc.) feels an overwhelming urge to open, read, and reply—immediately. This is not just another cold email; it is the ONLY message in their inbox that they remember, forward, and respond to. The reader must feel this email was written just for them, at this moment, for this reason.

    ========================
    ABOUT CREATO (for context & inspiration)
    ========================
    - Creato is an award-winning Sydney-based design partner, established in 2015.
    - Trusted by University of Sydney, Dell, IGA, WHO, MSD Pharmaceuticals, Hilti, NSW Government, Menulog, Repco, Aldi, Johnson & Johnson, Ray White, Taubmans, and more.
    - 5.0 Google rating, 43+ glowing reviews, 100% customer satisfaction.
    - Owner & Creative Director: Callum Humphreys.
    - Services: Logo Design, Web Design & Development, Graphic Design, Social Media Content Creation.
    - 100% Satisfaction Guarantee: Unlimited revisions.
    - Full Copyright Ownership: No ongoing licensing or fees.
    - Fast Turnaround: 72-hour delivery on most tasks.
    - Transparent Pricing: No hidden fees.
    - Modern, clever designs that help clients outshine their competition.
    - Case studies: MBA, Wind & Vibes, Hilti, Sydney Business Park, Alpha Financials, Sevigne.
    - Testimonials highlight: “Always goes the extra mile”, “Seamless experience”, “Exceeded expectations”, “Amazing value for money”, “Highly recommended”.

    ========================
    YOUR TASK
    ========================
    - Write a cold email for Creato targeting business decision-makers (owners, founders, marketing managers, etc.) in SMBs, startups, and established companies across industries (real estate, construction, law, healthcare, government, etc.).
    - The subject line **must include the company name** and be so curiosity-driven, so hyper-personalized, and so psychologically irresistible that it achieves a 100% open rate—think like a world-class copy chief, using advanced psychological triggers, open loops, pattern interrupts, and deep personalization.
    - The email body must be radically short (max 5 sentences), ultra-personalized, and instantly relevant—no fluff, no generic intros, no filler.
    - The first line must reference a specific detail from their website (e.g., a homepage headline, a unique service, a recent achievement, or a testimonial) based on the analysis above.
    - Immediately connect that detail to a relevant value prop from Creato—make it clear you understand their business and what would move the needle for them.
    - **Mention Sydney early on if the client is in Sydney, or Australia if not. Use the sheet data (City/State/Country) to verify this.**
    - **If possible, mention their competition or closest competitors in a way that is natural, respectful, and adds value.**
    - Make the tone conversational, warm, and peer-to-peer—never salesy or robotic.
    - End with a hyper-personalized micro-offer: "I can give you a quick quote for a {{X}}-page website and list your website pages: {{list of their actual website pages, comma-separated}}. If there are more than 10 pages, just list the most relevant or unique ones."
    - The CTA must be so easy and inviting that replying feels like a favor to themselves, not to you.
    - Never use opt-out language, legal disclaimers, or generic closing lines.
    - Sign off as Callum.
    - **Make sure you use British English only in the email body.**

    ========================
    SUPER-PRO PERSONALIZATION STRATEGY
    ========================
    - Your email must feel like it could only have been written for this recipient, at this moment, for this reason.
    - Avoid all generic or templated language. Every line should reference something unique, timely, or contextually relevant to the recipient's business, website, or market.
    - Use details from the website analysis to craft a first line that is so specific and insightful that it could not possibly be used for any other company.
    - If you can identify a competitor or a recent move by a competitor (from the website or industry context), mention it in a way that demonstrates deep understanding of the recipient's market landscape.
    - If the client is in Sydney, mention Sydney in a way that feels natural and relevant to their business or market. If in Australia (but not Sydney), mention Australia early on.
    - If you use a compliment, make it so specific that it could only apply to this company.
    - If you use a statistic or insight, make it surprising and directly relevant to the recipient.
    - The email should read like a peer-to-peer note from someone who has done their homework, not a vendor or marketer.

    ========================
    SUBJECT LINE STRATEGY
    ========================
    - The subject line must include the company name ({company}) in a natural, non-spammy way.
    - Make it ultra-specific to the recipient’s website, service, or recent activity.
    - Use open loops to trigger curiosity (e.g., “Brand refresh tip for {company} you might’ve missed”).
    - Add industry-specific language (e.g., "logo impact for {company}", "web design edge for {company}").
    - Experiment with micro-story teasers (e.g., “A quick story about a Sydney brand that doubled leads”).
    - The subject line must create an irresistible open loop, spark intense curiosity, and reference something unique about their business, website, or a recent achievement, challenge, or trend.
    - Use advanced psychological triggers: open loops, pattern interrupts, micro-personalization, FOMO, social proof, and subtle urgency—but never hype or manipulation.
    - Absolutely avoid all generic, salesy, or spammy language. Make it feel like a personal note from a peer, not a vendor.
    - The subject line must be so good that the recipient feels compelled to open immediately, even if they never open cold emails.
    - **You MUST use the most advanced, creative, and proven curiosity triggers.**
    - **Below are 20+ world-class, proven, and highly creative subject line examples. Use these as inspiration, but do NOT copy—adapt the style and intent to the recipient and context. Your subject line must be even better and more irresistible than these:**
        - "Saw something on {company}’s site—can I share a wild idea?"
        - "Your brand’s secret edge? (1-min thought inside)"
        - "Noticed {{unique detail}} at {company}—is anyone else missing this?"
        - "Quick question about {company}—bet you haven’t heard this before"
        - "If I were you at {company}, I’d want to know this"
        - "A micro-idea for {company}—promise it’s not a pitch"
        - "How {company} could double enquiries this month (no sales pitch)"
        - "If you only open one email today at {company}, make it this one"
        - "What {company}’s competitors are missing (quick tip inside)"
        - "A Sydney story that could change {company}’s next quarter"
        - "What I’d do if I ran {company} (1-minute idea)"
        - "A tiny tweak for {company} with big results"
        - "Your website caught my eye—here’s why ({company})"
        - "A quick win for {company}—mind if I share?"
        - "What {company} can teach the industry (quick thought)"
        - "A design secret for {company} (from Sydney’s best)"
        - "What {company}’s next big move could be"
        - "A fresh perspective for {company}—no strings attached"
        - "Noticed something on {company}’s homepage—worth a look?"
        - "A creative shortcut for {company} (1-min read)"
        - "What {company}’s clients are really thinking"
        - "A Sydney client’s story that reminded me of {company}"
        - "A quick question about {company}’s growth"
        - "What {company} could try this month (no pitch)"
        - "A small idea for {company}—could be a game changer"
        - "What {company}’s next award could be for"
        - "A design tip for {company}—straight from the pros"
        - "What {company}’s competitors wish they knew"
        - "A story about {company} I had to share"
        - "What’s next for {company}? (quick idea inside)"
        - "A Sydney insight for {company}—worth 30 seconds?"

    ========================
    EMAIL BODY STRATEGY (ULTRA-PERSONALIZED, SHORT, ACTIONABLE)
    ========================
    - **First Line:** Reference a specific, real detail from their website or business (e.g., homepage headline, unique service, recent achievement, or testimonial) based on the above analysis.
    - **Second Line:** Connect that detail to a relevant value prop from Creato—show you understand what would move the needle for them.
    - **Third Line:** Mention Sydney early if the client is in Sydney, or Australia if not. If not in Sydney, and you can identify a real competitor, mention them briefly (never use placeholders).
    - **Fourth Line:** Offer a micro-offer: "I can give you a quick quote for a [number of]-page website and list your website pages: [list of their actual website pages, comma-separated]. If there are more than 10 pages, just list the most relevant or unique ones."
    - **Fifth Line (CTA):** Make the CTA so easy and inviting that replying feels like a favor to themselves, not to you.
    - **Sign off as Callum.**
    - **No opt-out language, no legal disclaimers, no generic closing lines.**
    - **No emojis, no bullet points, no fluff.**
    - **The email must be so specific, so relevant, and so valuable that it could only have been written for this recipient, at this moment, for this reason.**
    - **Use British English only in the email body.**

    ========================
    DELIVERY & FORMATTING RULES
    ========================
    - Max 5 sentences, each short and scannable.
    - Use white space generously.
    - Make it feel like a handwritten note from a peer, not a mass email.
    - If you reference a competitor, do so respectfully and only if it adds value.
    - If you use humor, make it subtle and appropriate.
    - If you use a compliment, make it specific and genuine.
    - If you use a statistic, make it surprising and relevant.
    - If you use a question, make it one that sparks curiosity and conversation.
    - If you use a resource or micro-offer, make it relevant and valuable.
    - The email must be so good, so specific, and so relevant that the recipient feels it was written just for them, at this moment, for this reason—and they feel compelled to open, read, and reply.

    ========================
    INPUTS
    ========================
    Company: {company}
    Website: {website}
    Keywords: {keywords}
    Australian: {australian}
    Sydney: {sydney}
    City: {city}
    State: {state}
    Country: {country}

    ========================
    EMAIL FORMAT
    ========================
    Subject: <short, ultra-personalized, curiosity-driven subject that includes the company name and is absolutely impossible to ignore or not open>
    Body:

    <the full, properly formatted email body as described above, with no outline or bullet points, and no emojis, and signed off as Callum>
    """

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=700,
    )
    result = response.choices[0].message.content.strip()

    # Extract subject and body, ensuring subject is not duplicated in the body
    subject = ""
    body = ""
    lines = result.splitlines()
    found_subject = False
    found_body = False
    body_lines = []

    for line in lines:
        if not found_subject and line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            found_subject = True
        elif line.lower().startswith("body:"):
            found_body = True
            continue  # skip the "Body:" line itself
        elif found_body:
            body_lines.append(line)

    # If subject/body not found, fallback to defaults
    if not subject:
        subject = "AI Outreach That Converts"
    if not body_lines:
        # fallback: use everything except subject line
        body_lines = [l for l in lines if not l.lower().startswith("subject:") and not l.lower().startswith("body:")]

    body = "\n".join(body_lines).strip()

    # Remove subject line if it accidentally appears at the top of the body
    if body.lower().startswith(subject.lower()):
        body = body[len(subject):].lstrip(" :\n")

    # --- Remove LLM-generated greeting at the top ---
    import re
    body = re.sub(r"^(hey|hi|hello)[^\n]*,?\s*\n+", "", body, flags=re.IGNORECASE)

    # --- Remove emojis from the body ---
    body = re.sub(r"[^\w\s,.!?@%&:;\"'()\[\]\-\/\n]", "", body)

    # --- Remove numbered/bullet formatting at the start of lines ---
    body = re.sub(r"^\s*[\-\*\d]+\s*[:.\)]\s*", "", body, flags=re.MULTILINE)

    # --- Split into short paragraphs (1–2 sentences per paragraph) ---
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    paragraphs = []
    current = ""
    for line in lines:
        if current:
            current += " " + line
        else:
            current = line
        # If the line ends with a period/question mark/exclamation, treat as paragraph end
        if current and current[-1] in ".!?":
            paragraphs.append(current.strip())
            current = ""
    if current:
        paragraphs.append(current.strip())
    body = "\n\n".join(paragraphs)

    # --- Add greeting at the top ---
    if recipient_name and recipient_name.strip().lower() not in ["", "none"]:
        greeting = f"Hey {recipient_name.strip()},"
    elif company and company.strip():
        greeting = f"Hey {company.strip()},"
    elif website and website.strip():
        domain = re.sub(r"https?://(www\.)?", "", website.strip(), flags=re.IGNORECASE)
        domain = domain.split("/")[0]
        greeting = f"Hey {domain},"
    else:
        greeting = "Hey there,"

    body = f"{greeting}\n\n{body}"

    body = body.replace("XYZ", "").replace("xyz", "")

    return subject, body

def generate_followup_email(company, website, keywords, prev_subject, prev_body, recipient_name=None):
    # Simple, smart, non-personalized follow-up prompt
    prompt = f"""
You are a world-class B2B cold email copywriter. Write a follow-up email that is smart, concise, and maximizes both open and reply rates (aim for 100% each). 

========================
RULES
========================
- The subject line must be curiosity-driven and reference the previous conversation, but does NOT need to be personalized.
- The body should be short (max 6 sentences), friendly, and make it easy for the recipient to reply.
- No pressure, no hype, no salesy language.
- Make the recipient feel comfortable replying, even if it's just a quick yes/no.
- The CTA should be soft and easy to say yes to.
- Sign off as "Callum".
- No emojis, no legal disclaimers, no opt-out language.
- Output ONLY the subject line and email body (no extra commentary).

========================
INPUTS
========================
Previous Email Subject: {prev_subject}

========================
EMAIL FORMAT
========================
Subject: <short, curiosity-driven subject referencing the previous email>
Body:

<the full, well-formatted email body, signed off as Callum>
"""

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=400,
    )
    result = response.choices[0].message.content.strip()

    # Extract subject and body, ensuring subject is not duplicated in the body
    subject = ""
    body = ""
    lines = result.splitlines()
    found_subject = False
    found_body = False
    body_lines = []

    for line in lines:
        if not found_subject and line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            found_subject = True
        elif line.lower().startswith("body:"):
            found_body = True
            continue  # skip the "Body:" line itself
        elif found_body:
            body_lines.append(line)

    # If subject/body not found, fallback to defaults
    if not subject:
        subject = f"Quick follow-up on my last email"
    if not body_lines:
        body_lines = [l for l in lines if not l.lower().startswith("subject:") and not l.lower().startswith("body:")]

    body = "\n".join(body_lines).strip()

    # Remove subject line if it accidentally appears at the top of the body
    if body.lower().startswith(subject.lower()):
        body = body[len(subject):].lstrip(" :\n")

    # --- Remove LLM-generated greeting at the top ---
    import re
    body = re.sub(r"^(hey|hi|hello)[^\n]*,?\s*\n+", "", body, flags=re.IGNORECASE)

    # --- Remove emojis from the body ---
    body = re.sub(r"[^\w\s,.!?@%&:;\"'()\[\]\-\/\n]", "", body)

    # --- Remove numbered/bullet formatting at the start of lines ---
    body = re.sub(r"^\s*[\-\*\d]+\s*[:.\)]\s*", "", body, flags=re.MULTILINE)

    # --- Split into short paragraphs (1–2 sentences per paragraph) ---
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    paragraphs = []
    current = ""
    for line in lines:
        if current:
            current += " " + line
        else:
            current = line
        if current and current[-1] in ".!?":
            paragraphs.append(current.strip())
            current = ""
    if current:
        paragraphs.append(current.strip())
    body = "\n\n".join(paragraphs)

    # --- Add greeting at the top ---
    if recipient_name and recipient_name.strip().lower() not in ["", "none"]:
        greeting = f"Hey {recipient_name.strip()},"
    else:
        greeting = "Hey there,"

    body = f"{greeting}\n\n{body}"

    return subject, body

# ----------------------------
# 📤 Send Email
# ----------------------------
def send_email(to_email, to_name, subject, body):
    email_data = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": to_email, "name": to_name}],
        sender={"email": SENDER_EMAIL, "name": SENDER_NAME},
        subject=subject,
        html_content=body.replace("\n", "<br>")
    )
    return email_api.send_transac_email(email_data)

# ----------------------------
# 🖥️ Streamlit UI
# ----------------------------
st.set_page_config(page_title="Converzia", layout="wide")
st.title("📬 Converzia X Creato : Cold Email Automation")
st.markdown("Upload your lead CSV and let AI generate and send personalized cold emails.")

# --- Remove CRM button from UI ---
col1, col2 = st.columns(2)
with col1:
    st.markdown(
        '<a href="https://app-smtp.brevo.com/statistics" target="_blank">'
        '<button style="background-color:#2563eb;color:white;padding:8px 18px;border:none;border-radius:5px;font-size:16px;cursor:pointer;">📊 Statistics</button>'
        '</a>',
        unsafe_allow_html=True
    )
# with col2: ... (CRM button removed)

file = st.file_uploader("📁 Upload CSV (with columns: co_name, website, email, keywords, Name)", type="csv")

if file:
    df = pd.read_csv(file)
    st.success(f"Loaded {len(df)} leads from file.")

    start = st.number_input("Start index", 0, len(df)-1, value=0)
    end = st.number_input("End index", start+1, len(df), value=min(len(df), start+10))

    tone = st.selectbox("Email Tone", ["friendly", "witty", "bold", "formal"], index=0)

    if st.button("🚀 Start Sending Emails"):
        skipped = []
        total = end - start
        sent_count = 0
        progress = st.progress(0)
        status_text = st.empty()
        time_per_email = 1.5  # seconds per email (adjust if needed)
        start_time = time.time()

        for idx, i in enumerate(range(start, end), 1):
            row = df.iloc[i]
            company = str(row.get("co_name", "")).strip()
            website = str(row.get("website", "")).strip()
            email = str(row.get("email", "")).strip()
            keywords = str(row.get("keywords", "")).strip()
            name = str(row.get("Name", company)).strip()

            if not email or not is_valid_email_address(email):
                skipped.append((i, email, "Invalid email"))
                continue

            st.markdown(f"#### ✉️ Sending to {name} ({email})")

            try:
                city = str(row.get("city", "")).strip()
                state = str(row.get("state", "")).strip()
                country = str(row.get("country", "")).strip()
                subject, body = generate_email(company, website, keywords, name, city, state, country, tone)
                st.code(f"Subject: {subject}", language="text")
                st.code(body, language="markdown")

                send_email(email, name, subject, body)

                sent_count += 1
                elapsed = time.time() - start_time
                emails_left = total - sent_count
                est_time_left = emails_left * time_per_email
                status_text.info(
                    f"Sent: {sent_count}/{total} | Left: {emails_left} | "
                    f"Estimated time left: {int(est_time_left)}s"
                )
                progress.progress(sent_count / total)
                st.success(f"✅ Sent to {email}")
            except ApiException as e:
                st.error(f"❌ Brevo API Error: {e}")
                skipped.append((i, email, "Brevo error"))
            except Exception as e:
                st.error(f"❌ AI/General Error: {e}")
                skipped.append((i, email, "General error"))

            time.sleep(time_per_email)  # avoid rate limits

        st.balloons()
        st.success("✅ All emails processed!")

        if skipped:
            st.warning(f"⚠️ Skipped {len(skipped)} emails.")
            st.dataframe(pd.DataFrame(skipped, columns=["Row", "Email", "Reason"]))
    if st.button("🔁 Send Follow-up Emails"):
        skipped = []
        for i in range(start, end):
            row = df.iloc[i]
            company = str(row.get("co_name", "")).strip()
            website = str(row.get("website", "")).strip()
            email = str(row.get("email", "")).strip()
            keywords = str(row.get("keywords", "")).strip()
            name = str(row.get("Name", company)).strip()

            if not email or not is_valid_email_address(email):
                skipped.append((i, email, "Invalid email"))
                continue

            st.markdown(f"#### 🔁 Sending follow-up to {name} ({email})")

            try:
                # Generate the original email to use as context for the follow-up
                prev_subject, prev_body = generate_email(company, website, keywords)
                subject, body = generate_followup_email(company, website, keywords, prev_subject, prev_body)
                st.code(f"Subject: {subject}", language="text")
                st.code(body, language="markdown")

                send_email(email, name, subject, body)
                st.success(f"✅ Follow-up sent to {email}")
            except ApiException as e:
                st.error(f"❌ Brevo API Error: {e}")
                skipped.append((i, email, "Brevo error"))
            except Exception as e:
                st.error(f"❌ AI/General Error: {e}")
                skipped.append((i, email, "General error"))

            time.sleep(1.5)  # avoid rate limits

        st.balloons()
        st.success("✅ All follow-up emails processed!")

        if skipped:
            st.warning(f"⚠️ Skipped {len(skipped)} emails.")
            st.dataframe(pd.DataFrame(skipped, columns=["Row", "Email", "Reason"]))
else:
    st.info("Please upload a CSV to begin.")

# --- ADVANCED FOLLOW-UP: TRACKING CSV ONLY ---
st.markdown("---")
st.header("📊 Advanced Follow-up: Upload Open/Click Tracking CSV (No Leads CSV Needed)")
tracking_file = st.file_uploader(
    "📊 Upload Open/Click Tracking CSV (columns: st_text, ts, sub, frm, email, tag, mid, link)",
    type="csv",
    key="tracking_csv_only"
)

if tracking_file is not None:
    tracking_df = pd.read_csv(tracking_file)
    st.success(f"Loaded {len(tracking_df)} rows from tracking CSV.")

    st.subheader("Select Range for Advanced Follow-up")
    start_adv = st.number_input(
        "Start index (Advanced Follow-up)", 0, len(tracking_df)-1, value=0, key="start_adv_tracking"
    )
    end_adv = st.number_input(
        "End index (Advanced Follow-up)", start_adv+1, len(tracking_df), value=min(len(tracking_df), start_adv+10), key="end_adv_tracking"
    )

    if st.button("📈 Send Follow-ups Based on Tracking CSV Only"):
        skipped = []
        sent_count = 0
        progress = st.progress(0)
        status_text = st.empty()
        total = end_adv - start_adv
        for idx, i in enumerate(range(start_adv, end_adv), 1):
            row = tracking_df.iloc[i]
            email = str(row.get("email", "")).strip()
            subject_base = str(row.get("sub", "")).strip()
            name = str(row.get("Name", "")).strip()
            if not name:
                name = "there"  # <-- fallback name for Brevo

            if not email or not is_valid_email_address(email):
                skipped.append((i, email, "Invalid email"))
                continue

            prev_subject = subject_base
            prev_body = ""

            subject, body = generate_followup_email("", "", "", prev_subject, prev_body, name)

            st.markdown(f"#### 📧 Sending follow-up to {email}")
            st.code(f"Subject: {subject}", language="text")
            st.code(body, language="markdown")

            try:
                send_email(email, name, subject, body)
                sent_count += 1
                status_text.info(f"Sent: {sent_count}/{total}")
                progress.progress(sent_count / total)
                st.success(f"✅ Sent to {email}")
            except Exception as e:
                st.error(f"❌ Error sending to {email}: {e}")
                skipped.append((i, email, str(e)))
            time.sleep(1.5)  # avoid rate limits

        st.balloons()
        st.success("✅ All advanced follow-up emails processed!")
        if skipped:
            st.warning(f"⚠️ Skipped {len(skipped)} emails.")
            st.dataframe(pd.DataFrame(skipped, columns=["Row", "Email", "Reason"]))
