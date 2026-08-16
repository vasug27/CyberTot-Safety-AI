import os
import json
import random
import pandas as pd
from datetime import datetime, timedelta

CATEGORIES = [
    "safe",
    "cyberbullying",
    "grooming",
    "scam_phishing",
    "distress_selfharm",
    "inappropriate_content"
]

SHARED_WORDS = ["photo", "pic", "insta", "number", "phone", "meet", "secret", "alone", "game", "group", "school", "bhai", "link"]

SAFE_TEMPLATES = [
    "bhai {w1} bhej de homework ka fast",
    "kal school me {w1} share karenge",
    "did u see the new {w1} on youtube?",
    "roblox me {w1} match aaja server pe",
    "mummy bol rahi hai {w1} time ho gaya so jao",
    "bhai discord pe {w1} call join kar le",
    "aaj test me {w1} ka paper hard tha lol",
    "tu kitna noob hai {w1} me, kill kar dunga tera character haha",
    "bhai photo bhej de class notes ki {w1} pe please",
    "phone number bhej de tera whatsapp group me add karne ke liye",
    "aaj toh marne ka mann kar raha hai iss test ke baad haha"
]

GROOMING_TEMPLATES = [
    "how old r u? u seem mature, send {w1} privately dont tell mom",
    "hey cutie, send {w1} of u, keep this a secret ok?",
    "meet me near park after {w1}, don't tell ur parents",
    "are u alone at home? camera on karke {w1} call karein?",
    "ur parents don't understand u, send me ur {w1} fast"
]

BULLYING_TEMPLATES = [
    "tu kitna noob hai {w1}, real life me loser hai, group se nikalo",
    "sabko pata hai tu cheat kar raha tha, koi tere {w1} me nahi khelega",
    "teri {w1} photo sabko bhej ke mzaak udayenge class me",
    "terko kal school stop pe dekhenge, pitenge ruk tu {w1}"
]

SCAM_TEMPLATES = [
    "FREE ROBUX - enter parents credit card details for {w1}",
    "Claim 10000 BGMI free click link for {w1}",
    "Congratulations! You won free iPhone enter OTP for {w1}"
]

DISTRESS_TEMPLATES = [
    "kuch accha nahi lag raha {w1}, har waqt rona aata hai",
    "I feel so empty and tired of {w1}, want to disappear forever",
    "sone ka mann nahi karta {w1}, bas akele rehne ka mann karta hai"
]

INAPPROPRIATE_TEMPLATES = [
    "watch free 18+ adult movies HD online {w1}",
    "download leaked viral video link telegram {w1}",
    "how to bypass parental control pin on android {w1}"
]

def generate_random_sentence(category):
    w1 = random.choice(SHARED_WORDS)
    if category == "safe":
        return random.choice(SAFE_TEMPLATES).format(w1=w1)
    elif category == "grooming":
        return random.choice(GROOMING_TEMPLATES).format(w1=w1)
    elif category == "cyberbullying":
        return random.choice(BULLYING_TEMPLATES).format(w1=w1)
    elif category == "scam_phishing":
        return random.choice(SCAM_TEMPLATES).format(w1=w1)
    elif category == "distress_selfharm":
        return random.choice(DISTRESS_TEMPLATES).format(w1=w1)
    else:
        return random.choice(INAPPROPRIATE_TEMPLATES).format(w1=w1)

def generate_labeled_dataset(samples_per_category=400):
    data = []

    for cat in CATEGORIES:
        for _ in range(samples_per_category):
            text = generate_random_sentence(cat)
            label = cat
            # Subtle ambiguity noise (~5%)
            if random.random() < 0.05:
                label = "safe" if cat != "safe" else "cyberbullying"

            data.append({"text": text, "label": label})

    df = pd.DataFrame(data)
    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    return df

def generate_daily_stream_scenario(scenario_type="grooming_attempt"):
    base_date = datetime(2026, 8, 11, 8, 0, 0)
    events = []
    
    events.append({
        "ts": (base_date + timedelta(hours=6, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S+05:30"),
        "type": "app_session",
        "app": "com.whatsapp",
        "duration_s": 300
    })
    events.append({
        "ts": (base_date + timedelta(hours=6, minutes=32)).strftime("%Y-%m-%dT%H:%M:%S+05:30"),
        "type": "chat_message",
        "app": "com.whatsapp",
        "direction": "received",
        "text": "bhai aaj bus 10 min late aayegi",
        "counterparty": "classmate_arav"
    })
    events.append({
        "ts": (base_date + timedelta(hours=8, minutes=15)).strftime("%Y-%m-%dT%H:%M:%S+05:30"),
        "type": "app_session",
        "app": "com.google.android.youtube",
        "duration_s": 2400
    })
    events.append({
        "ts": (base_date + timedelta(hours=8, minutes=20)).strftime("%Y-%m-%dT%H:%M:%S+05:30"),
        "type": "web_visit",
        "domain": "youtube.com",
        "title": "Minecraft survival guide for beginners in Hindi"
    })
    events.append({
        "ts": (base_date + timedelta(hours=10, minutes=10)).strftime("%Y-%m-%dT%H:%M:%S+05:30"),
        "type": "app_session",
        "app": "com.roblox.client",
        "duration_s": 4820
    })
    
    if scenario_type == "safe_day":
        events.append({
            "ts": (base_date + timedelta(hours=10, minutes=40)).strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "type": "chat_message",
            "app": "com.roblox.client",
            "direction": "received",
            "text": "tu kitna noob hai game me, kill kar dunga tera character haha",
            "counterparty": "best_friend"
        })
        events.append({
            "ts": (base_date + timedelta(hours=13, minutes=15)).strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "type": "chat_message",
            "app": "com.whatsapp",
            "direction": "sent",
            "text": "aaj test ke baad toh dimag kharab ho gaya lol",
            "counterparty": "best_friend"
        })
        
    elif scenario_type == "grooming_attempt":
        events.append({
            "ts": (base_date + timedelta(hours=11, minutes=20)).strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "type": "web_visit",
            "domain": "freerobuxgenerator.xyz",
            "title": "FREE ROBUX - just enter your parents card"
        })
        events.append({
            "ts": (base_date + timedelta(hours=13, minutes=47)).strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "type": "chat_message",
            "app": "com.roblox.client",
            "direction": "received",
            "text": "how old r u? u seem mature, send photo privately dont tell mom",
            "counterparty": "unknown_user_8812"
        })
        events.append({
            "ts": (base_date + timedelta(hours=14, minutes=58)).strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "type": "chat_message",
            "app": "com.whatsapp",
            "direction": "sent",
            "text": "kuch accha nahi lag raha photo, har waqt rona aata hai",
            "counterparty": "best_friend"
        })

    elif scenario_type == "cyberbullying":
        events.append({
            "ts": (base_date + timedelta(hours=11, minutes=5)).strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "type": "chat_message",
            "app": "com.whatsapp",
            "direction": "received",
            "text": "tu kitna noob hai, real life me bhi loser hai, group se nikalo",
            "counterparty": "class_group"
        })
        events.append({
            "ts": (base_date + timedelta(hours=12, minutes=10)).strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "type": "chat_message",
            "app": "com.whatsapp",
            "direction": "received",
            "text": "teri photo sabko bhej ke mzaak udayenge class me",
            "counterparty": "unknown_user_992"
        })
        
    elif scenario_type == "scam_trap":
        events.append({
            "ts": (base_date + timedelta(hours=11, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "type": "web_visit",
            "domain": "free-bgmi-uc-claim.net",
            "title": "Claim 10,000 BGMI for FREE! Click link below to unlock"
        })
        events.append({
            "ts": (base_date + timedelta(hours=11, minutes=32)).strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "type": "chat_message",
            "app": "com.whatsapp",
            "direction": "received",
            "text": "FREE ROBUX - enter parents credit card details here",
            "counterparty": "bot_promo_spammer"
        })
        
    return events

if __name__ == "__main__":
    os.makedirs("c:/Development/CyberTot/data", exist_ok=True)
    df = generate_labeled_dataset()
    train_size = int(0.8 * len(df))
    train_df = df.iloc[:train_size]
    test_df = df.iloc[train_size:]
    
    train_df.to_csv("c:/Development/CyberTot/data/train.csv", index=False)
    test_df.to_csv("c:/Development/CyberTot/data/test.csv", index=False)
    print(f"Generated synthetic training set ({len(train_df)} samples) and test set ({len(test_df)} samples).")
