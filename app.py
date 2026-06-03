import os
import random
import logging
import traceback

from flask import Flask, request

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer,
    QuickReply,
    QuickReplyItem,
    MessageAction
)

from linebot.v3.webhook import WebhookParser
from linebot.v3.webhooks import MessageEvent

# ---------------- LOGGING ----------------

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# ---------------- TOKENS ----------------

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(LINE_CHANNEL_SECRET)
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)

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


# ---------------- CARD BUILDER ----------------

def build_info_bubble(key, mode):
    apt = apartments[key]
    if mode == "friendly":
        insight = random.choice(friendly_messages[key])
    elif mode == "guide":
        insight = random.choice(guide_messages[key])
    else:
        insight = random.choice(expert_messages[key])

    features_text = "\n".join(f for f in apt["features"])

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


def build_photo_bubble(photo_url, label):
    return {
        "type": "bubble",
        "size": "micro",
        "hero": {
            "type": "image",
            "url": photo_url,
            "size": "full",
            "aspectRatio": "4:3",
            "aspectMode": "cover"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "8px",
            "contents": [
                {
                    "type": "text",
                    "text": "📸 " + label,
                    "size": "xxs",
                    "color": "#888888",
                    "align": "center",
                    "wrap": True
                }
            ]
        }
    }


def build_apartment_bubbles(key, mode):
    apt = apartments[key]
    bubbles = [build_info_bubble(key, mode)]
    if len(apt["photos"]) > 1:
        bubbles.append(build_photo_bubble(apt["photos"][1], "Photo 2"))
    if len(apt["photos"]) > 2:
        bubbles.append(build_photo_bubble(apt["photos"][2], "Photo 3"))
    return bubbles


def build_carousel_for_keys(keys, mode):
    bubbles = []
    for key in keys:
        bubbles.extend(build_apartment_bubbles(key, mode))
    return {"type": "carousel", "contents": bubbles}


# ---------------- QUICK REPLIES ----------------

def qr_after_carousel():
    return QuickReply(items=[
        QuickReplyItem(action=MessageAction(label="💬 Get Advice", text="get advice")),
        QuickReplyItem(action=MessageAction(label="🔁 View One Again", text="view one again")),
        QuickReplyItem(action=MessageAction(label="✅ I Made My Choice", text="i made my choice"))
    ])


def qr_view_one():
    return QuickReply(items=[
        QuickReplyItem(action=MessageAction(label="🏢 Luxor", text="view luxor")),
        QuickReplyItem(action=MessageAction(label="🌿 Miracle", text="view miracle")),
        QuickReplyItem(action=MessageAction(label="🏛 Victory", text="view victory"))
    ])


def qr_final_choice():
    return QuickReply(items=[
        QuickReplyItem(action=MessageAction(label="🏢 Luxor", text="choose luxor")),
        QuickReplyItem(action=MessageAction(label="🌿 Miracle", text="choose miracle")),
        QuickReplyItem(action=MessageAction(label="🏛 Victory", text="choose victory"))
    ])


def qr_finish():
    return QuickReply(items=[
        QuickReplyItem(action=MessageAction(label="📞 Contact Agent", text="contact agent")),
        QuickReplyItem(action=MessageAction(label="🏦 Mortgage Info", text="mortgage info"))
    ])


def qr_yes_show():
    return QuickReply(items=[
        QuickReplyItem(action=MessageAction(label="👀 Yes, show me!", text="yes show me"))
    ])


# ---------------- SEND HELPERS ----------------

def reply_msg(reply_token, messages):
    line_bot_api.reply_message(
        ReplyMessageRequest(reply_token=reply_token, messages=messages)
    )


def push_msg(user_id, messages):
    line_bot_api.push_message(
        PushMessageRequest(to=user_id, messages=messages)
    )


def txt(text, qr=None):
    return TextMessage(text=text, quick_reply=qr)


def send_carousel(user_id, keys):
    mode = get_user(user_id).get("assistant_type", "friendly")
    carousel = build_carousel_for_keys(keys, mode)
    logging.info("Sending carousel with %d bubbles", len(carousel["contents"]))
    try:
        flex = FlexMessage(
            alt_text="🏠 Apartments in Downtown Austin",
            contents=FlexContainer.from_dict(carousel)
        )
        push_msg(user_id, [
            flex,
            txt(
                "👆 Swipe through the cards to browse.\n\nWhat would you like to do next?",
                qr_after_carousel()
            )
        ])
        logging.info("Carousel sent OK")
    except Exception:
        logging.error("Carousel send failed: %s", traceback.format_exc())
        push_msg(user_id, [txt("❌ Could not load cards. Please type Start to try again.")])


# ---------------- WEBHOOK ----------------

@app.route("/callback", methods=["POST"])
def callback():
    try:
        body = request.get_data(as_text=True)
        signature = request.headers.get("X-Line-Signature")
        events = parser.parse(body, signature)

        for event in events:
            user_id = getattr(event.source, "user_id", None)
            if not user_id:
                continue

            user = get_user(user_id)

            if not isinstance(event, MessageEvent):
                continue
            if not hasattr(event.message, "text"):
                continue

            text = event.message.text.strip().lower()
            step = user.get("step", "")
            logging.info("TEXT=[%s]  STEP=[%s]", text, step)

            # ---- START ----
            if text == "start":
                user_state[user_id] = {"step": "choose_assistant"}
                reply_msg(event.reply_token, [txt(
                    "🏡 Welcome to AI Housing Assistant!\n\n"
                    "I will help you find the perfect apartment in Austin.\n\n"
                    "Please choose your assistant type:\n\n"
                    "1 - 😊 Friendly\n"
                    "2 - 🧭 Guide\n"
                    "3 - 🧠 Expert"
                )])

            # ---- CHOOSE ASSISTANT ----
            elif step == "choose_assistant" and text in ["1", "2", "3"]:
                modes = {"1": "friendly", "2": "guide", "3": "expert"}
                labels = {"1": "😊 Friendly", "2": "🧭 Guide", "3": "🧠 Expert"}
                user["assistant_type"] = modes[text]
                user["step"] = "choose_city"
                reply_msg(event.reply_token, [txt(
                    "✅ " + labels[text] + " mode selected!\n\n"
                    "🏙 Step 1: Choose city\n\n"
                    "1 - Austin"
                )])

            # ---- STEP 1: CITY ----
            elif step == "choose_city" and text == "1":
                user["step"] = "choose_area"
                reply_msg(event.reply_token, [txt(
                    "📍 Step 2: Choose area\n\n"
                    "1 - Downtown"
                )])

            # ---- STEP 2: AREA ----
            elif step == "choose_area" and text == "1":
                user["step"] = "choose_payment"
                reply_msg(event.reply_token, [txt(
                    "💳 Step 3: Payment method\n\n"
                    "1 - Mortgage"
                )])

            # ---- STEP 3: PAYMENT ----
            elif step == "choose_payment" and text == "1":
                user["step"] = "choose_price"
                reply_msg(event.reply_token, [txt(
                    "💰 Step 4: Choose price range\n\n"
                    "1 - $280k – $300k"
                )])

            # ---- STEP 4: PRICE ----
            elif step == "choose_price" and text == "1":
                user["step"] = "confirm_show"
                reply_msg(event.reply_token, [txt(
                    "🔍 Searching for apartments..."
                )])
                push_msg(user_id, [txt(
                    "🏠 I found 3 apartments that match your request!\n"
                    "📍 Downtown Austin  |  💰 $282k – $300k\n\n"
                    "Would you like to see them?",
                    qr_yes_show()
                )])

            # ---- CONFIRM SHOW ----
            elif step == "confirm_show" and text == "yes show me":
                user["step"] = "browsing"
                reply_msg(event.reply_token, [txt(
                    "🏙 Here are your apartments! Swipe to browse 👇"
                )])
                send_carousel(user_id, APT_KEYS)

            # ---- BROWSING: GET ADVICE ----
            elif step == "browsing" and text == "get advice":
                mode = user.get("assistant_type", "friendly")
                reply_msg(event.reply_token, [txt(
                    advice_text[mode],
                    qr_after_carousel()
                )])

            # ---- BROWSING: VIEW ONE AGAIN ----
            elif step == "browsing" and text == "view one again":
                user["step"] = "view_one"
                reply_msg(event.reply_token, [txt(
                    "👀 Which apartment would you like to see again?",
                    qr_view_one()
                )])

            # ---- VIEW ONE: PICK ----
            elif step == "view_one" and text in ["view luxor", "view miracle", "view victory"]:
                key = text.split()[1]
                user["step"] = "browsing"
                reply_msg(event.reply_token, [txt(
                    "📋 Here is " + apartments[key]["title"] + " again:"
                )])
                send_carousel(user_id, [key])

            # ---- BROWSING: I MADE MY CHOICE ----
            elif step == "browsing" and text == "i made my choice":
                user["step"] = "final_choice"
                reply_msg(event.reply_token, [txt(
                    "🏠 Which apartment are you choosing?",
                    qr_final_choice()
                )])

            # ---- FINAL CHOICE ----
            elif step == "final_choice" and text in ["choose luxor", "choose miracle", "choose victory"]:
                key = text.split()[1]
                user["chosen"] = key
                user["step"] = "finish"
                summaries = {
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
                reply_msg(event.reply_token, [txt(
                    "🎉 You selected: " + apartments[key]["title"] + "\n\n"
                    + summaries[key] + "\n\n"
                    "What would you like to do next?",
                    qr_finish()
                )])

            # ---- FINISH: CONTACT AGENT ----
            elif step == "finish" and text == "contact agent":
                reply_msg(event.reply_token, [txt(
                    "📞 You can contact our agent.\n"
                    "We will get back to you shortly!"
                )])

            # ---- FINISH: MORTGAGE ----
            elif step == "finish" and text == "mortgage info":
                reply_msg(event.reply_token, [txt(
                    "🏦 You can contact a mortgage specialist.\n"
                    "We will help you find the best rates!"
                )])

            # ---- UNKNOWN ----
            else:
                reply_msg(event.reply_token, [txt(
                    "🏡 Please type Start to begin."
                )])

        return "OK", 200

    except Exception as e:
        logging.error("FULL ERROR: %s", traceback.format_exc())
        return "error", 500


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))





