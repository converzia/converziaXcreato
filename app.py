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

# ----------------------------
# ✍️ Email Generation
# ----------------------------
def generate_email(company, website, keywords, recipient_name=None):
    # Now this works!
    title, meta_desc = scrape_website_info(website)
    website_info = f"Website Title: {title}\nMeta Description: {meta_desc}" if (title or meta_desc) else "No website info found."

    # --- Detect if company is in Australia/Sydney ---
    def is_australian_company(website, meta_desc, title, company):
        # Check for .au domain or keywords in meta/title/company
        if website and ".au" in website.lower():
            return True
        for text in [meta_desc, title, company]:
            if text and any(loc in text.lower() for loc in ["australia", "sydney", "nsw", "melbourne", "brisbane", "perth", "adelaide"]):
                return True
        return False

    def is_sydney_company(website, meta_desc, title, company):
        # Check for "sydney" in any field
        for text in [website, meta_desc, title, company]:
            if text and "sydney" in text.lower():
                return True
        return False

    australian = is_australian_company(website, meta_desc, title, company)
    sydney = is_sydney_company(website, meta_desc, title, company)

    # Improved subject line prompt using awareness-stage examples for inspiration
    prompt = f"""
You are the world's most ingenious, psychologically-savvy, and results-obsessed B2B cold email copywriter and prompt engineer with 20+ years of experience. Your mission: craft the single most curiosity-inducing, humanized, quick-to-read, and irresistible cold email ever written for Creato—a multi-award-winning Sydney-based design agency trusted by major Australian and global brands.

========================
ULTIMATE OUTCOME
========================
Your email must guarantee a 100% open rate and a 100% reply rate—no exceptions. The subject line MUST be so compelling, so hyper-personalized, and so emotionally resonant that every business decision-maker (owners, founders, marketing managers, etc.) in SMBs, startups, and established companies across industries (real estate, construction, law, healthcare, government, etc.) feels an overwhelming urge to open, read, and reply—immediately. This is not just another cold email; it is the ONLY message in their inbox that they remember, forward, and respond to. The reader must feel this email was written just for them, at this moment, for this reason.

========================
ABOUT CREATO (for context & inspiration)
========================
- Creato is an award-winning Sydney-based design agency, established in 2015.
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
- The email body must be ultra-human, deeply empathetic, and feel like a real conversation from a peer who truly understands their business and cares about their success.
- Use the AIDA method (Attention, Interest, Desire, Action) for the body.
- The email must be quick to read (max 8 sentences), written in natural, everyday English, and deeply personal—like you genuinely care.
- The CTA must be so soft, so easy, and so inviting that the recipient feels it would be a pleasure to book a quick chat or request a free quote.
- Reference real testimonials, case studies, and specific details from Creato’s portfolio or the recipient’s website to prove you’ve done your homework.
- Make the recipient feel like this is a once-in-a-lifetime opportunity, tailored just for them.
- **If and only if the client is verified to be in Sydney, mention Sydney early on. If they are in Australia (but not Sydney), mention Australia instead. If they are not in Australia, do not mention Sydney or Australia at all.**
- **If the client is not in Sydney, make sure to mention their competition or closest competitors if you can find a real name; if not, skip this. Never use placeholders like "XYZ".**

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
    - "What {company} could do differently (no sales pitch)"
    - "A quick fix for {company}’s website (saw this today)"
    - "What {company}’s brand could unlock next"
    - "A creative spark for {company}—from a fellow builder"
    - "What {company}’s next client will notice"
    - "A design shortcut for {company}—mind if I share?"
    - "What {company} could try before the quarter ends"
    - "A Sydney story for {company}—quick read"
    - "What {company}’s team might love to see"
    - "A micro-idea for {company}—no pitch, just value"
    - "What {company} could do to stand out this month"
    - "A quick win for {company}—saw this on your site"
    - "What {company}’s next step could look like"
    - "A creative idea for {company}—from Sydney’s best"
    - "What {company} could do to outshine the competition"
    - "A story about {company}—had to reach out"
    - "What {company}’s next big win could be"
    - "A design tip for {company}—from a Sydney creative"
    - "What {company} could try for instant impact"
    - "A quick thought for {company}—worth a look?"
    - "What {company}’s clients are saying (and why it matters)"
    - "A Sydney perspective for {company}—1-min read"
    - "What {company} could do with a fresh look"
    - "A creative shortcut for {company}—no pitch"
    - "What {company}’s next client will notice"
    - "A micro-idea for {company}—promise it’s not a pitch"
    - "What {company} could try before the quarter ends"
    - "A Sydney story for {company}—quick read"
    - "What {company}’s team might love to see"
    - "A quick win for {company}—saw this on your site"
    - "What {company}’s next step could look like"
    - "A creative idea for {company}—from Sydney’s best"
    - "What {company} could do to outshine the competition"
    - "A story about {company}—had to reach out"
    - "What {company}’s next big win could be"
    - "A design tip for {company}—from a Sydney creative"
    - "What {company} could try for instant impact"
    - "A quick thought for {company}—worth a look?"
    - "What {company}’s clients are saying (and why it matters)"
    - "A Sydney perspective for {company}—1-min read"
    - "What {company} could do with a fresh look"
    - "A creative shortcut for {company}—no pitch"
    - "What {company}’s next client will notice"
    - "A micro-idea for {company}—promise it’s not a pitch"
    - "What {company} could try before the quarter ends"
    - "A Sydney story for {company}—quick read"
    - "What {company}’s team might love to see"
    - "A quick win for {company}—saw this on your site"
    - "What {company}’s next step could look like"
    - "A creative idea for {company}—from Sydney’s best"
    - "What {company} could do to outshine the competition"
    - "A story about {company}—had to reach out"
    - "What {company}’s next big win could be"
    - "A design tip for {company}—from a Sydney creative"
    - "What {company} could try for instant impact"
    - "A quick thought for {company}—worth a look?"
    - "What {company}’s clients are saying (and why it matters)"
    - "A Sydney perspective for {company}—1-min read"
    - "What {company} could do with a fresh look"
    - "A creative shortcut for {company}—no pitch"
    - "What {company}’s next client will notice"
    - "A micro-idea for {company}—promise it’s not a pitch"
    - "What {company} could try before the quarter ends"
    - "A Sydney story for {company}—quick read"
    - "What {company}’s team might love to see"
    - "A quick win for {company}—saw this on your site"
    - "What {company}’s next step could look like"
    - "A creative idea for {company}—from Sydney’s best"
    - "What {company} could do to outshine the competition"
    - "A story about {company}—had to reach out"
    - "What {company}’s next big win could be"
    - "A design tip for {company}—from a Sydney creative"
    - "What {company} could try for instant impact"
    - "A quick thought for {company}—worth a look?"
    - "What {company}’s clients are saying (and why it matters)"
    - "A Sydney perspective for {company}—1-min read"
    - "What {company} could do with a fresh look"
    - "A creative shortcut for {company}—no pitch"
    - "What {company}’s next client will notice"
    - "A micro-idea for {company}—promise it’s not a pitch"
    - "What {company} could try before the quarter ends"
    - "A Sydney story for {company}—quick read"
    - "What {company}’s team might love to see"
    - "A quick win for {company}—saw this on your site"
    - "What {company}’s next step could look like"
    - "A creative idea for {company}—from Sydney’s best"
    - "What {company} could do to outshine the competition"
    - "A story about {company}—had to reach out"
    - "What {company}’s next big win could be"
    - "A design tip for {company}—from a Sydney creative"
    - "What {company} could try for instant impact"
    - "A quick thought for {company}—worth a look?"
    - "What {company}’s clients are saying (and why it matters)"
    - "A Sydney perspective for {company}—1-min read"
    - "What {company} could do with a fresh look"
    - "A creative shortcut for {company}—no pitch"
    - "What {company}’s next client will notice"
    - "A micro-idea for {company}—promise it’s not a pitch"
    - "What {company} could try before the quarter ends"
    - "A Sydney story for {company}—quick read"
    - "What {company}’s team might love to see"
    - "A quick win for {company}—saw this on your site"
    - "What {company}’s next step could look like"
    - "A creative idea for {company}—from Sydney’s best"
    - "What {company} could do to outshine the competition"
    - "A story about {company}—had to reach out"
    - "What {company}’s next big win could be"
    - "A design tip for {company}—from a Sydney creative"
    - "What {company} could try for instant impact"
    - "A quick thought for {company}—worth a look?"
    - "What {company}’s clients are saying (and why it matters)"
    - "A Sydney perspective for {company}—1-min read"
    - "What {company} could do with a fresh look"
    - "A creative shortcut for {company}—no pitch"
    - "What {company}’s next client will notice"
    - "A micro-idea for {company}—promise it’s not a pitch"
    - "What {company} could try before the quarter ends"
    - "A Sydney story for {company}—quick read"
    - "What {company}’s team might love to see"
    - "A quick win for {company}—saw this on your site"
    - "What {company}’s next step could look like"
    - "A creative idea for {company}—from Sydney’s best"
    - "What {company} could do to outshine the competition"
    - "A story about {company}—had to reach out"
    - "What {company}’s next big win could be"
    - "A design tip for {company}—from a Sydney creative"
    - "What {company} could try for instant impact"
    - "A quick thought for {company}—worth a look?"

========================
EMAIL BODY STRATEGY (AIDA)
========================
- **Attention (First Line):**
    - Give a very specific compliment—reference their homepage, a testimonial, a client, or a unique detail from their website.
    - Show you actually explored their site—e.g., “I saw you helped ABC Realty boost listings by 32%.”
    - Use elements like homepage header, taglines, latest blog headlines, testimonials, or recent client results.
    - **If and only if the client is verified to be in Sydney, mention Sydney early on. If they are in Australia (but not Sydney), mention Australia instead. If they are not in Australia, do not mention Sydney or Australia at all.**
    - **If the client is not in Sydney, make sure to mention their competition or closest competitors if you can find a real name; if not, skip this. Never use placeholders like "XYZ".**
- **Interest (Pain/Challenge):**
    - Identify a pain point unique to their industry (real estate, construction, law, healthcare, etc.).
    - Use micro-insights: “You’re doing amazing work, but your case study headlines don’t sell the value you delivered.”
    - Reference a recent trend, news, or shift in their industry that’s relevant to their business.
- **Desire (How Creato Helps):**
    - Tailor Creato’s value prop by niche.
    - Use vivid metaphors or analogies: “Creato is like your creative director, strategist, and design team rolled into one.”
    - Add mini case-study-style examples: “One client saw a 3.2x increase in leads after a web refresh.”
    - Emphasize the feeling (relief, clarity, connection)—not just the function.
    - Reference real testimonials or case studies for proof.
- **Action (Call-To-Action):**
    - Make it feel like a tailored offer, not a standard pitch.
    - Instead of “Would you be open to a quick chat?” try:
        → “Happy to send you some ideas for {company}—no strings attached?”
    - Use curiosity + ease: “Want to see what a fresh logo or website could do for your brand?”
    - End warm and human: “No pressure, just thought it might be fun to explore.”
    - Add rejection-safe endings: “If you’re not the right person, feel free to point me in the right direction.”

========================
DELIVERY & FORMATTING RULES
========================
- Do NOT include any opt-out language or legal disclaimers.
- Keep sentences short and snappy—no more than 2 lines per paragraph.
- Use max 6–8 sentences in total.
- Use white space generously to make the email scannable.
- Never say “agency” in a robotic way—frame Creato as a partner, creative ally, or brand builder.
- Avoid all buzzwords, jargon, or technical language.
- Make the email feel like it was written by someone who truly cares about their success.
- Reference a shared value, goal, or challenge if possible.
- The email should feel like the start of a partnership, not a transaction.
- If you use a statistic or fact, make sure it’s relevant and adds value.
- The subject line and first sentence should work together to create curiosity and relevance.
- The email should be so good that the recipient wants to forward it to a colleague.
- If you can, include a “micro-offer” (e.g., a quick tip, resource, or idea) that adds value even if they don’t reply.
- The email should feel like a breath of fresh air compared to the usual cold outreach.
- If you reference a competitor, do so respectfully and only if it adds value.
- The email should be timeless—relevant today and in the future.
- If you use a metaphor or analogy, make it vivid and memorable.
- The email should feel like a conversation starter, not a monologue.
- If you can, reference a recent achievement, milestone, or news about their company.
- The email should be so personalized that it couldn’t be sent to anyone else.
- If you use humor, make sure it’s subtle and appropriate.
- The email should feel like a handwritten note, not a mass email.
- If you reference a pain point, make it specific and empathetic.
- The email should be so good that the recipient wants to reply, even if just to say thank you.
- If you use a call-to-action, make it easy to say yes to.
- The email should feel like a favor, not a request.
- If you can, reference a mutual connection, interest, or value.
- The email should be so well-written that it stands out in their inbox.
- If you use a compliment, make it specific and genuine.
- The email should feel like the beginning of a valuable relationship.
- If you reference a challenge, make it one that only someone who understands their business would know.
- The email should be so relevant that the recipient feels compelled to respond.
- If you use a story, make it short, relevant, and memorable.
- The email should feel like it was written just for them, at this moment, for this reason.
- If you use a statistic, make it surprising and relevant.
- The email should be so good that the recipient wants to keep it for future reference.
- If you use a question, make it one that sparks curiosity and conversation.
- The email should feel like a conversation between equals.
- If you reference a goal, make it one that’s important to them.
- The email should be so helpful that the recipient feels grateful.
- If you use a resource, make it relevant and valuable.
- The email should feel like a gift, not a pitch.
- If you reference a trend, make it one that’s relevant to their business.
- The email should be so good that the recipient wants to share it with their team.
- If you use a CTA, make it feel like an invitation, not an obligation.
- The email should feel like the start of a partnership, not a transaction.
- If you can, add a “micro-offer” or insight that makes the email valuable even if they never reply.
- The email must be so good, so specific, and so relevant that the recipient feels it was written just for them, at this moment, for this reason—and they feel compelled to open, read, and reply.

========================
INPUTS
========================
Company: {company}
Website: {website}
Keywords: {keywords}
Website Info (scraped): {website_info}
Australian: {australian}
Sydney: {sydney}

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

    if "stop" not in body.lower():
        body += "\n\nIf this isn't for you, just reply STOP."

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
                subject, body = generate_email(company, website, keywords, name)
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