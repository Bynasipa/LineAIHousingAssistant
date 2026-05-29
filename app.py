import os
import random
import logging
import traceback

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, abort

from linebot.v3 import WebhookHandler

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    ImageMessage,
    FlexMessage,
    FlexContainer
)

from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    PostbackEvent,
    FollowEvent
)


# ---------------- LOGGING ----------------

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ---------------- TOKEN (FIXED FOR RAILWAY) ----------------

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise ValueError("Missing LINE_CHANNEL_ACCESS_TOKEN or LINE_CHANNEL_SECRET")

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ---------------- FLASK APP ----------------

app = Flask(__name__)

# ---------------- AI MESSAGES ----------------

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

# ---------------- APARTMENTS ----------------

apartments = {
    "luxor": {
        "title": "Luxor Apartment",
        "location": "Downtown Austin",
        "price": "$300,000",
        "size": "82 m²",
        "description": (
            "Modern apartment in the business center with modern interior design.\n"
            "Move-in ready, no renovation required.\n\n"
            "✅ Free high-speed Wi-Fi included\n"
            "✅ Metro and transport nearby"
        ),
        "photos": [
            "https://res.cloudinary.com/dekw8i9b8/image/upload/Luxor_01_iyx5uc",
            "https://res.cloudinary.com/dekw8i9b8/image/upload/Luxor_02_lf47j3",
            "https://res.cloudinary.com/dekw8i9b8/image/upload/Luxor_03_yglqcw"
        ]
    },

    "miracle": {
        "title": "Miracle Garden Apartment",
        "location": "Downtown Austin",
        "price": "$295,000",
        "size": "85 m²",
        "description": (
            "Apartment near central park in a quiet and green neighborhood.\n"
            "School nearby. Renovation completed one year ago.\n\n"
            "✅ Free resident parking\n"
            "✅ Modern and practical layout"
        ),
        "photos": [
            "https://res.cloudinary.com/dekw8i9b8/image/upload/Miracle_Garden_01_m9psqg",
            "https://res.cloudinary.com/dekw8i9b8/image/upload/Miracle_Garden_02_taju6n",
            "https://res.cloudinary.com/dekw8i9b8/image/upload/Miracle_Garden_03_hsuvtn"
        ]
    },

    "victory": {
        "title": "Victory Mansion",
        "location": "Downtown Austin",
        "price": "$282,000",
        "size": "80 m²",
        "description": (
            "Historic city center apartment close to attractions.\n"
            "Requires renovation but has strong potential.\n\n"
            "✅ Free daily bread and milk delivery\n"
            "✅ Nearby bakery and farmers market"
        ),
        "photos": [
            "https://res.cloudinary.com/dekw8i9b8/image/upload/Victory_Mansion_01_j2utk3",
            "https://res.cloudinary.com/dekw8i9b8/image/upload/Victory_Mansion_02_zhb2ia",
            "https://res.cloudinary.com/dekw8i9b8/image/upload/Victory_Mansion_03_fexeqo"
        ]
    }
}

# ---------------- HELPERS ----------------

user_state = {}

def get_user(user_id):
    if user_id not in user_state:
        user_state[user_id] = {}
    return user_state[user_id]

# ---------------- SEND APARTMENT ----------------

def send_apartment(line_bot_api, user_id, key):

    apartment = apartments[key]
    user = get_user(user_id)

    mode = user.get("assistant_type", "friendly")

    if mode == "friendly":
        msg = random.choice(friendly_messages[key])
    elif mode == "guide":
        msg = random.choice(guide_messages[key])
    else:
        msg = random.choice(expert_messages[key])

    text = (
        f"🏢 {apartment['title']}\n"
        f"📍 {apartment['location']}\n"
        f"💰 {apartment['price']}\n"
        f"📐 {apartment['size']}\n\n"
        f"{apartment['description']}\n\n"
        f"💡 AI Insight:\n{msg}"
    )

    line_bot_api.push_message(
        PushMessageRequest(
            to=user_id,
            messages=[
                TextMessage(text=text),
                ImageMessage(
                    original_content_url=apartment["photos"][0],
                    preview_image_url=apartment["photos"][0]
                ),
                ImageMessage(
                    original_content_url=apartment["photos"][1],
                    preview_image_url=apartment["photos"][1]
                ),
                ImageMessage(
                    original_content_url=apartment["photos"][2],
                    preview_image_url=apartment["photos"][2]
                ),
            ]
        )
    )


# ---------------- START ----------------

def start(line_bot_api, reply_token, user_id):

    user = get_user(user_id)
    user.clear()

    flex = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "🏡 AI Housing Assistant", "weight": "bold", "size": "xl"},
                {"type": "text", "text": "I’ll help you find the right apartment in Austin step by step."}
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "action": {"type": "postback", "label": "🤖 Friendly Assistant", "data": "assistant_friendly"}},
                {"type": "button", "action": {"type": "postback", "label": "📊 Guide Assistant", "data": "assistant_guide"}},
                {"type": "button", "action": {"type": "postback", "label": "🧠 Expert Assistant", "data": "assistant_expert"}}
            ]
        }
    }

    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=reply_token,
            messages=[FlexMessage(alt_text="Start", contents=FlexContainer.from_dict(flex))]
        )
    )

# ---------------- MESSAGE ----------------

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    print("EVENT WORKS")

    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)

            text = event.message.text.lower().strip()

            # simple test reply (like Telegram bot)
            reply_text = "Hello from bot"

            if text == "start":
                reply_text = "Bot is working ✅"

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )

    except Exception as e:
        print("MESSAGE ERROR:", e)
        print(traceback.format_exc())

# ---------------- FOLLOW (AUTO WELCOME) ----------------

@handler.add(FollowEvent)
def handle_follow(event):
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="👋 Thanks for adding the bot! Type 'start'")]
                )
            )

    except Exception as e:
        print("FOLLOW ERROR:", e)
        print(traceback.format_exc())


# ---------------- POSTBACKS ----------------

@handler.add(PostbackEvent)
def handle_postback(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        user_id = event.source.user_id
        data = event.postback.data
        user = get_user(user_id)

        # -------- ASSISTANT --------
        if data.startswith("assistant_"):

            user["assistant_type"] = data.split("_")[1]

            flex = {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "🏙 Step 1: Choose city"}
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "button", "action": {"type": "postback", "label": "🏙 Austin", "data": "city_austin"}}
                    ]
                }
            }

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[FlexMessage(alt_text="City", contents=FlexContainer.from_dict(flex))]
                )
            )

        # -------- CITY --------
        elif data.startswith("city_"):

            flex = {
                "type": "bubble",
                "body": {"type": "box", "layout": "vertical",
                         "contents": [{"type": "text", "text": "📍 Step 2: Choose area"}]},
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "button", "action": {"type": "postback", "label": "📍 Downtown", "data": "area_downtown"}}
                    ]
                }
            }

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[FlexMessage(alt_text="Area", contents=FlexContainer.from_dict(flex))]
                )
            )

        # -------- AREA --------
        elif data.startswith("area_"):

            flex = {
                "type": "bubble",
                "body": {"type": "box", "layout": "vertical",
                         "contents": [{"type": "text", "text": "💳 Step 3: Payment method"}]},
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "button", "action": {"type": "postback", "label": "🏦 Mortgage", "data": "payment_mortgage"}}
                    ]
                }
            }

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[FlexMessage(alt_text="Payment", contents=FlexContainer.from_dict(flex))]
                )
            )

        # -------- PAYMENT --------
        elif data.startswith("payment_"):

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=
                        "🏙 I found 3 apartments in Downtown Austin\n"
                        "💰 Price range: $282k – $300k"
                    )]
                )
            )

            send_apartment(line_bot_api, user_id, "luxor")
            send_apartment(line_bot_api, user_id, "miracle")
            send_apartment(line_bot_api, user_id, "victory")

# ---------------- RUN ----------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)