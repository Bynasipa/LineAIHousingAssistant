import os
import random
import logging
import traceback
import requests

from flask import Flask, request as flask_request

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
)
from linebot.v3.webhook import WebhookParser
from linebot.v3.webhooks import MessageEvent, FollowEvent

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(LINE_CHANNEL_SECRET)

# ---------------- STATE ----------------

user_state = {}


def get_user(user_id):
    if user_id not in user_state:
        user_state[user_id] = {}
    return user_state[user_id]


# ---------------- AI INSIGHT MESSAGES ----------------

friendly_messages = {
    "luxor": [
        "✨ A very cozy and modern apartment in the city center.",
        "🏡 Perfect for a comfortable and stress-free lifestyle.",
        "💙 Great option if you want convenience and modern living."
    ],
    "miracle": [
        "🌿 Peaceful atmosphere with a balanced lifestyle.",
        "🏡 Excellent for families and calm living.",
        "✨ Green surroundings make this place very relaxing."
    ],
    "victory": [
        "🏛 Unique apartment with historic charm.",
        "✨ Full of personality and strong future potential.",
        "💡 Great opportunity for creative renovation ideas."
    ]
}

guide_messages = {
    "luxor": [
        "📊 Excellent downtown location with stable property value.",
        "📍 Strong infrastructure and transport accessibility.",
        "💰 Good option for buyers seeking convenience."
    ],
    "miracle": [
        "📊 Family-oriented neighborhood with green zones.",
        "📍 Parking and recent renovation increase livability.",
        "💰 Strong balance between comfort and price."
    ],
    "victory": [
        "📊 Strong investment potential after renovation.",
        "📍 Historic district increases long-term value.",
        "💰 Attractive option for long-term investors."
    ]
}

expert_messages = {
    "luxor": [
        "🧠 Low-risk premium real estate asset.",
        "📊 Strong liquidity in central business district.",
        "🏗 Stable long-term appreciation potential."
    ],
    "miracle": [
        "🧠 Balanced growth profile with medium risk.",
        "📊 Green-zone demand improves market stability.",
        "🏗 Suitable for lifestyle-focused portfolios."
    ],
    "victory": [
        "🧠 High-risk, high-reward investment opportunity.",
        "📊 Renovation arbitrage potential is significant.",
        "🏗 Scarcity in historic areas supports future growth."
    ]
}

# ---------------- ADVICE ----------------

advice_text = {
    "friendly": (
        "😊 My personal advice for you:\n\n"
        "🏢 Luxor — if you love modern comfort and city life.\n"
        "🌿 Miracle — if you prefer peace, nature and family vibes.\n"
        "🏛 Victory — if you want something unique with future potential.\n\n"
        "What feels right to you?"
    ),
    "guide": (
        "🧭 Here is my honest guide:\n\n"
        "🏢 Luxor — best for move-in ready buyers who value location.\n"
        "🌿 Miracle — best for families who want space, parking and green area.\n"
        "🏛 Victory — best for buyers ready for renovation and long-term gains.\n\n"
        "Which fits your situation best?"
    ),
    "expert": (
        "🧠 Investment analysis:\n\n"
        "📊 Luxor — low risk, stable appreciation, strong CBD liquidity.\n"
        "📊 Miracle — medium risk, green-zone demand growth, solid rental yield.\n"
        "📊 Victory — high risk / high reward. Renovation arbitrage in historic district.\n\n"
        "Best ROI potential: Victory > Miracle > Luxor."
    )
}

# ---------------- APARTMENTS ----------------

apartments = {
    "luxor": {
        "title": "Luxor Apartment",
        "location": "Downtown Austin",
        "price": "$300,000",
        "size": "82 m²",
        "description": (
            "Modern apartment in the business center "
            "with stylish interior design. "
            "Move-in ready, no renovation required."
        ),
        "features": [
            "✅ Free high-speed Wi-Fi included",
            "✅ Metro and transport nearby"
        ],
        "photos": [
            "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975318/Luxor_01_iyx5uc.jpg",
            "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975444/Luxor_02_x4upom.jpg",
            "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975443/Luxor_03_yglqcw.jpg"
        ]
    },
    "miracle": {
        "title": "Miracle Garden",
        "location": "Downtown Austin",
        "price": "$295,000",
        "size": "85 m²",
        "description": (
            "Quiet and green neighborhood near central park. "
            "School nearby. "
            "Renovation completed one year ago."
        ),
        "features": [
            "✅ Free resident parking",
            "✅ Modern and practical layout"
        ],
        "photos": [
            "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975445/Miracle_Garden_01_ee1iuk.jpg",
            "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975444/Miracle_Garden_02_qxghmq.jpg",
            "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975444/Miracle_Garden_03_kug6p9.jpg"
        ]
    },
    "victory": {
        "title": "Victory Mansion",
        "location": "Downtown Austin",
        "price": "$282,000",
        "size": "80 m²",
        "description": (
            "Historic city center apartment close to attractions. "
            "Requires renovation but has strong potential."
        ),
        "features": [
            "✅ Free daily bread and milk delivery",
            "✅ Nearby bakery and farmers market"
        ],
        "photos": [
            "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975445/Victory_Mansion_01_mx3sme.jpg",
            "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975445/Victory_Mansion_02_at00es.jpg",
            "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975446/Victory_Mansion_03_vu0zpn.jpg"
        ]
    }
}

APT_KEYS = ["luxor", "miracle", "victory"]

MODE_LABELS = {
    "friendly": "😊 Friendly",
    "guide": "🧭 Guide",
    "expert": "🧠 Expert"
}

# ---------------- HTTP HELPERS ----------------

def line_push(user_id, messages_payload):
    resp = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + LINE_CHANNEL_ACCESS_TOKEN
        },
        json={"to": user_id, "messages": messages_payload},
        timeout=10
    )
    logging.info("line_push status=%s body=%s", resp.status_code, resp.text)
    return resp.status_code == 200


def line_reply(reply_token, messages_payload):
    resp = requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + LINE_CHANNEL_ACCESS_TOKEN
        },
        json={"replyToken": reply_token, "messages": messages_payload},
        timeout=10
    )
    logging.info("line_reply status=%s body=%s", resp.status_code, resp.text)
    return resp.status_code == 200


# ---------------- QUICK REPLY HELPERS ----------------

def qr_items(items):
    return {
        "items": [
            {
                "type": "action",
                "action": {"type": "message", "label": label, "text": text}
            }
            for label, text in items
        ]
    }


def txt_msg(text, quick_reply=None):
    msg = {"type": "text", "text": text}
    if quick_reply:
        msg["quickReply"] = quick_reply
    return msg


# Static quick replies
# LINE label hard limit: 20 characters (including emoji which count as 1 char each)
# All labels below are verified ≤ 20 chars.

QR_AFTER_CAROUSEL = qr_items([
    ("📸 Photos", "see photos"),           # 9
    ("💬 Get Advice", "get advice"),       # 13
    ("✅ My Choice", "i made my choice")   # 12
])

QR_PHOTO_PICK = qr_items([
    ("🏢 Luxor Photos", "photos luxor"),   # 15
    ("🌿 Miracle Photos", "photos miracle"), # 17
    ("🏛 Victory Photos", "photos victory") # 17
])

QR_AFTER_PHOTOS = qr_items([
    ("💬 Get Advice", "get advice"),       # 13
    ("🔁 Cards Again", "view one again"),  # 14
    ("✅ My Choice", "i made my choice")   # 12
])

QR_VIEW_ONE = qr_items([
    ("🏢 Luxor", "view luxor"),            # 8
    ("🌿 Miracle", "view miracle"),        # 10
    ("🏛 Victory", "view victory")         # 10
])

QR_FINAL_CHOICE = qr_items([
    ("🏢 Luxor", "choose luxor"),          # 8
    ("🌿 Miracle", "choose miracle"),      # 10
    ("🏛 Victory", "choose victory")       # 10
])

QR_YES_SHOW = qr_items([
    ("👀 Yes, show me!", "yes show me")    # 17
])

QR_CONFIRM_EXIT = qr_items([
    ("✅ Yes, finish", "confirm exit"),    # 15
    ("🔄 Keep going", "keep going")        # 13
])


def qr_after_choice(seen_modes):
    """
    Quick reply after final choice.
    Always shows Contact + Mortgage.
    Shows AI Assistant button only if not all 3 modes seen yet.
    If all 3 modes seen, shows Finish button instead.
    All labels strictly ≤ 20 chars.
    """
    items = [
        ("📞 Contact Agent", "contact agent"),  # 16
        ("🏦 Mortgage Info", "mortgage info"),  # 16
    ]
    if len(seen_modes) < 3:
        remaining = 3 - len(seen_modes)
        # "🟢 AI Mode (2 left)" = 19 chars ✓
        items.append((f"🟢 AI Mode ({remaining} left)", "choose ai assistant"))
    else:
        items.append(("🏁 Finish Session", "finish session"))  # 17
    return qr_items(items)


def qr_choose_mode(seen_modes):
    """Show only unseen modes. Labels ≤ 20 chars."""
    # "1 - 😊 Friendly" = 15 chars ✓
    # "2 - 🧭 Guide"    = 12 chars ✓
    # "3 - 🧠 Expert"   = 13 chars ✓
    all_modes = [("1", "friendly"), ("2", "guide"), ("3", "expert")]
    items = []
    for num, mode in all_modes:
        if mode not in seen_modes:
            label = f"{num} - {MODE_LABELS[mode]}"
            items.append((label, num))
    return qr_items(items) if items else None


# ---------------- CARD BUILDER ----------------

def build_info_bubble(key, mode):
    apt = apartments[key]
    if mode == "friendly":
        insight = random.choice(friendly_messages[key])
    elif mode == "guide":
        insight = random.choice(guide_messages[key])
    else:
        insight = random.choice(expert_messages[key])
    features_text = "\n".join(apt["features"])
    return {
        "type": "bubble",
        "size": "kilo",
        "hero": {
            "type": "image",
            "url": apt["photos"][0],
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "paddingAll": "16px",
            "contents": [
                {
                    "type": "text",
                    "text": apt["title"],
                    "weight": "bold",
                    "size": "lg",
                    "color": "#1a1a2e",
                    "wrap": True
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "xs",
                    "contents": [
                        {
                            "type": "text",
                            "text": "📍 " + apt["location"],
                            "size": "xs",
                            "color": "#888888",
                            "flex": 1,
                            "wrap": True
                        },
                        {
                            "type": "text",
                            "text": "📐 " + apt["size"],
                            "size": "xs",
                            "color": "#888888",
                            "align": "end"
                        }
                    ]
                },
                {
                    "type": "text",
                    "text": "💰 " + apt["price"],
                    "weight": "bold",
                    "size": "xl",
                    "color": "#e63946",
                    "margin": "sm"
                },
                {
                    "type": "separator",
                    "margin": "sm",
                    "color": "#eeeeee"
                },
                {
                    "type": "text",
                    "text": apt["description"],
                    "size": "xs",
                    "color": "#444444",
                    "wrap": True,
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": features_text,
                    "size": "xs",
                    "color": "#2d6a4f",
                    "wrap": True,
                    "margin": "sm"
                },
                {
                    "type": "separator",
                    "margin": "sm",
                    "color": "#eeeeee"
                },
                {
                    "type": "text",
                    "text": "💡 " + insight,
                    "size": "xs",
                    "color": "#555577",
                    "wrap": True,
                    "margin": "sm",
                    "style": "italic"
                }
            ]
        }
    }


def build_main_carousel(keys, mode):
    bubbles = [build_info_bubble(key, mode) for key in keys]
    return {
        "type": "flex",
        "altText": "🏠 Apartments in Downtown Austin",
        "contents": {
            "type": "carousel",
            "contents": bubbles
        }
    }


def build_image_carousel(key):
    apt = apartments[key]
    columns = []
    for i, photo_url in enumerate(apt["photos"], start=1):
        columns.append({
            "imageUrl": photo_url,
            "action": {
                "type": "message",
                "label": f"Photo {i}",
                "text": f"choose {key}"
            }
        })
    return {
        "type": "template",
        "altText": f"📸 Photos of {apt['title']}",
        "template": {
            "type": "image_carousel",
            "columns": columns
        }
    }


# ---------------- SEND HELPERS ----------------

def send_main_carousel(user_id):
    mode = get_user(user_id).get("assistant_type", "friendly")
    carousel = build_main_carousel(APT_KEYS, mode)
    ok = line_push(user_id, [
        carousel,
        txt_msg(
            "👆 Swipe through the cards to browse all apartments.\n\n"
            "What would you like to do next?",
            QR_AFTER_CAROUSEL
        )
    ])
    if not ok:
        line_push(user_id, [txt_msg("❌ Could not load cards. Please type Start to try again.")])


def send_single_carousel(user_id, key):
    mode = get_user(user_id).get("assistant_type", "friendly")
    bubble = build_info_bubble(key, mode)
    apt = apartments[key]
    ok = line_push(user_id, [
        {
            "type": "flex",
            "altText": f"🏠 {apt['title']}",
            "contents": bubble
        },
        txt_msg(
            f"📋 Here is {apt['title']} again!\n\nWhat would you like to do next?",
            QR_AFTER_CAROUSEL
        )
    ])
    if not ok:
        line_push(user_id, [txt_msg("❌ Could not load card. Please type Start to try again.")])


def send_photos(user_id, key):
    apt = apartments[key]
    image_carousel = build_image_carousel(key)
    ok = line_push(user_id, [
        txt_msg(f"📸 Photos of {apt['title']} — swipe to see all 3 👇"),
        image_carousel,
        txt_msg(
            f"💰 {apt['price']}  |  📐 {apt['size']}  |  📍 {apt['location']}\n\n"
            "Tap a photo to select this apartment, or choose what to do next:",
            QR_AFTER_PHOTOS
        )
    ])
    if not ok:
        line_push(user_id, [txt_msg("❌ Could not load photos. Please type Start to try again.")])


def send_ai_insights(user_id, mode):
    """
    Send fresh AI insights for all 3 apartments in the chosen mode.
    Does NOT re-send the full carousel — just text insights.
    """
    lines = [f"🤖 {MODE_LABELS[mode]} mode — fresh insights for each apartment:\n"]
    for key in APT_KEYS:
        apt = apartments[key]
        if mode == "friendly":
            insight = random.choice(friendly_messages[key])
        elif mode == "guide":
            insight = random.choice(guide_messages[key])
        else:
            insight = random.choice(expert_messages[key])
        lines.append(f"🏠 {apt['title']} ({apt['price']})\n💡 {insight}")
    lines.append("\nYou can still view photos or get advice below.")
    line_push(user_id, [
        txt_msg("\n\n".join(lines), QR_AFTER_CAROUSEL)
    ])


# ---------------- SUMMARIES ----------------

CHOICE_SUMMARIES = {
    "luxor": (
        "✨ Excellent choice!\n"
        "Modern living in the heart of Austin.\n"
        "📡 Free Wi-Fi, metro nearby, move-in ready."
    ),
    "miracle": (
        "🌿 Great pick!\n"
        "Peaceful and green neighborhood.\n"
        "🌳 School nearby, free parking, renovated."
    ),
    "victory": (
        "🏛 Bold choice!\n"
        "Historic gem with strong potential.\n"
        "🍞 Free bread and milk delivery every day."
    )
}


# ---------------- WEBHOOK ----------------

@app.route("/callback", methods=["POST"])
def callback():
    try:
        body = flask_request.get_data(as_text=True)
        signature = flask_request.headers.get("X-Line-Signature")
        events = parser.parse(body, signature)

        for event in events:
            user_id = getattr(event.source, "user_id", None)
            if not user_id:
                continue
            user = get_user(user_id)

            # ---- FOLLOW ----
            if isinstance(event, FollowEvent):
                line_push(user_id, [txt_msg(
                    "👋 Welcome to AI Housing Assistant!\n\n"
                    "I will help you find your perfect apartment in Austin.\n\n"
                    "🏡 Type Start to begin!"
                )])
                continue

            if not isinstance(event, MessageEvent):
                continue
            if not hasattr(event.message, 'text'):
                continue

            text = event.message.text.strip().lower()
            step = user.get("step", "")
            logging.info("TEXT=[%s]  STEP=[%s]  STATE=%s", text, step, str(user))

            # ---- START ----
            if text == "start":
                user_state[user_id] = {
                    "step": "choose_assistant",
                    "seen_modes": []          # track which AI modes user has tried
                }
                line_reply(event.reply_token, [txt_msg(
                    "🏡 Welcome to AI Housing Assistant!\n\n"
                    "I will help you find the perfect apartment in Austin.\n\n"
                    "Please choose your assistant type:\n\n"
                    "1 - 😊 Friendly\n"
                    "2 - 🧭 Guide\n"
                    "3 - 🧠 Expert"
                )])

            # ---- CHOOSE ASSISTANT (initial + loop) ----
            elif step == "choose_assistant" and text in ["1", "2", "3"]:
                modes = {"1": "friendly", "2": "guide", "3": "expert"}
                mode = modes[text]
                user["assistant_type"] = mode

                # Mark this mode as seen
                if mode not in user.get("seen_modes", []):
                    user.setdefault("seen_modes", []).append(mode)

                prev_step = user.get("prev_step", "")

                # If returning from choice screen — send insights, not full carousel
                if prev_step == "finish":
                    user["step"] = "browsing"
                    user["prev_step"] = ""
                    line_reply(event.reply_token, [txt_msg(
                        f"✅ Switched to {MODE_LABELS[mode]} mode!\n\n"
                        "Here are updated AI insights — your apartment cards are still above. 👆"
                    )])
                    send_ai_insights(user_id, mode)
                else:
                    # First time: ask city
                    user["step"] = "choose_city"
                    line_reply(event.reply_token, [txt_msg(
                        f"✅ {MODE_LABELS[mode]} mode selected!\n\n"
                        "🏙 Step 1: Choose city\n\n"
                        "1 - Austin"
                    )])

            # ---- CHOOSE CITY ----
            elif step == "choose_city" and text == "1":
                user["step"] = "choose_area"
                line_reply(event.reply_token, [txt_msg(
                    "📍 Step 2: Choose area\n\n"
                    "1 - Downtown"
                )])

            # ---- CHOOSE AREA ----
            elif step == "choose_area" and text == "1":
                user["step"] = "choose_payment"
                line_reply(event.reply_token, [txt_msg(
                    "💳 Step 3: Payment method\n\n"
                    "1 - Mortgage"
                )])

            # ---- CHOOSE PAYMENT ----
            elif step == "choose_payment" and text == "1":
                user["step"] = "choose_price"
                line_reply(event.reply_token, [txt_msg(
                    "💰 Step 4: Choose price range\n\n"
                    "1 - $280k – $300k"
                )])

            # ---- CHOOSE PRICE ----
            elif step == "choose_price" and text == "1":
                user["step"] = "confirm_show"
                line_reply(event.reply_token, [txt_msg("🔍 Searching for apartments...")])
                line_push(user_id, [txt_msg(
                    "🏠 I found 3 apartments that match your request!\n"
                    "📍 Downtown Austin  |  💰 $282k – $300k\n\n"
                    "Would you like to see them?",
                    QR_YES_SHOW
                )])

            # ---- CONFIRM SHOW ----
            elif step == "confirm_show" and text == "yes show me":
                user["step"] = "browsing"
                line_reply(event.reply_token, [txt_msg(
                    "🏙 Here are your apartments! Swipe to browse 👇"
                )])
                send_main_carousel(user_id)

            # ---- SEE PHOTOS ----
            elif step == "browsing" and text == "see photos":
                user["step"] = "pick_photos"
                line_reply(event.reply_token, [txt_msg(
                    "📸 Which apartment photos would you like to see?",
                    QR_PHOTO_PICK
                )])

            # ---- PICK PHOTOS ----
            elif step == "pick_photos" and text in ["photos luxor", "photos miracle", "photos victory"]:
                key = text.split()[1]
                user["step"] = "browsing"
                line_reply(event.reply_token, [txt_msg(
                    f"📸 Loading photos of {apartments[key]['title']}..."
                )])
                send_photos(user_id, key)

            # ---- GET ADVICE ----
            elif step == "browsing" and text == "get advice":
                mode = user.get("assistant_type", "friendly")
                line_reply(event.reply_token, [txt_msg(
                    advice_text[mode],
                    QR_AFTER_CAROUSEL
                )])

            # ---- VIEW ONE AGAIN ----
            elif step == "browsing" and text == "view one again":
                user["step"] = "view_one"
                line_reply(event.reply_token, [txt_msg(
                    "👀 Which apartment would you like to see again?",
                    QR_VIEW_ONE
                )])

            elif step == "view_one" and text in ["view luxor", "view miracle", "view victory"]:
                key = text.split()[1]
                user["step"] = "browsing"
                line_reply(event.reply_token, [txt_msg(
                    f"📋 Loading {apartments[key]['title']} for you..."
                )])
                send_single_carousel(user_id, key)

            # ---- I MADE MY CHOICE ----
            elif step == "browsing" and text == "i made my choice":
                user["step"] = "final_choice"
                line_reply(event.reply_token, [txt_msg(
                    "🏠 Which apartment are you choosing?",
                    QR_FINAL_CHOICE
                )])

            # ---- FINAL CHOICE (from browsing OR from photo tap) ----
            elif (step in ["final_choice", "browsing"]) and text in ["choose luxor", "choose miracle", "choose victory"]:
                key = text.split()[1]
                user["chosen"] = key
                user["step"] = "finish"
                user["prev_step"] = "finish"
                seen = user.get("seen_modes", [])
                line_reply(event.reply_token, [txt_msg(
                    f"🎉 You selected: {apartments[key]['title']}\n\n"
                    + CHOICE_SUMMARIES[key] + "\n\n"
                    "What would you like to do next?",
                    qr_after_choice(seen)
                )])

            # ---- CHOOSE AI ASSISTANT (from finish screen) ----
            elif step == "finish" and text == "choose ai assistant":
                seen = user.get("seen_modes", [])
                current = user.get("assistant_type", "friendly")
                unseen = [m for m in ["friendly", "guide", "expert"] if m not in seen]

                # Build message listing remaining modes
                mode_lines = []
                num_map = {"friendly": "1", "guide": "2", "expert": "3"}
                for mode_key in ["friendly", "guide", "expert"]:
                    if mode_key not in seen:
                        mode_lines.append(f"{num_map[mode_key]} - {MODE_LABELS[mode_key]}")

                user["step"] = "choose_assistant"
                qr = qr_choose_mode(seen)
                line_reply(event.reply_token, [txt_msg(
                    "🤖 Please choose your assistant type:\n\n"
                    + "\n".join(mode_lines) +
                    "\n\nYou will see fresh AI insights without reloading the cards.",
                    qr
                )])

            # ---- FINISH SESSION (after all 3 modes seen) ----
            elif text == "finish session":
                chosen_key = user.get("chosen", "")
                chosen_title = apartments[chosen_key]["title"] if chosen_key else "an apartment"
                user["step"] = "done"
                line_reply(event.reply_token, [txt_msg(
                    f"🏁 Thank you for using AI Housing Assistant!\n\n"
                    f"Your choice: {chosen_title}\n\n"
                    "You have explored all 3 AI perspectives.\n\n"
                    "Would you like to finish?",
                    QR_CONFIRM_EXIT
                )])

            # ---- CONFIRM EXIT ----
            elif text == "confirm exit":
                chosen_key = user.get("chosen", "")
                chosen_title = apartments[chosen_key]["title"] if chosen_key else "an apartment"
                user_state[user_id] = {}  # clear state
                line_reply(event.reply_token, [txt_msg(
                    f"✅ Session complete!\n\n"
                    f"Your selected apartment: {chosen_title}\n\n"
                    "Our agent will contact you shortly. 🙌\n\n"
                    "Type Start anytime to explore again."
                )])

            # ---- KEEP GOING ----
            elif text == "keep going":
                user["step"] = "finish"
                seen = user.get("seen_modes", [])
                line_reply(event.reply_token, [txt_msg(
                    "👍 No problem! What would you like to do?",
                    qr_after_choice(seen)
                )])

            # ---- CONTACT / MORTGAGE ----
            elif text == "contact agent":
                line_reply(event.reply_token, [txt_msg(
                    "📞 You can contact our agent.\n"
                    "We will get back to you shortly!\n\n"
                    "🏡 To view apartments again — type Start"
                )])

            elif text == "mortgage info":
                line_reply(event.reply_token, [txt_msg(
                    "🏦 You can contact a mortgage specialist.\n"
                    "We will help you find the best rates!\n\n"
                    "🏡 To view apartments again — type Start"
                )])

            # ---- FALLBACK ----
            else:
                line_reply(event.reply_token, [txt_msg(
                    "🏡 Please type Start to begin."
                )])

        return 'OK', 200

    except Exception:
        logging.error("FULL ERROR: %s", traceback.format_exc())
        return 'error', 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
