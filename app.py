import os
import random
import logging
import traceback

from flask import Flask, request, abort

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    FlexMessage,
    ImageMessage
)

from linebot.v3.webhook import WebhookParser
from linebot.v3.webhooks import MessageEvent, FollowEvent, PostbackEvent

# ---------------- LOGGING ----------------

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# ---------------- TOKEN ----------------

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

def send_text(line_bot_api, reply_token, text):
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text=text)]
        )
    )


def send_flex(line_bot_api, reply_token, bubble):
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=reply_token,
            messages=[FlexMessage(alt_text="menu", contents=bubble)]
        )
    )


def send_apartment(line_bot_api, reply_token, user_id, key):
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

    images = []
    for url in apartment["photos"]:
        images.append(ImageMessage(original_content_url=url, preview_image_url=url))

    return text, images


# ---------------- WEBHOOK ----------------

@app.route("/callback", methods=["POST"])


def callback():
    try:
        body = request.get_data(as_text=True)
        signature = request.headers.get("X-Line-Signature")

        try:
            events = parser.parse(body, signature)
        except Exception:
            logging.error(traceback.format_exc())
            return "OK", 200

        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)

            for event in events:

                user_id = getattr(event.source, "user_id", None)

                # ❗ FIX: avoid crash
                if not user_id:
                    continue

                # ---------------- MESSAGE ----------------
                if isinstance(event, MessageEvent):

                    if hasattr(event.message, "text"):

                        user_text = event.message.text.lower()

                        # -------- START --------
                        if user_text == "start":
                            user_state[user_id] = {}

                            bubble = {
                                "type": "bubble",
                                "body": {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "🏡 AI Housing Assistant",
                                            "weight": "bold",
                                            "size": "lg"
                                        },
                                        {
                                            "type": "text",
                                            "text": "I’ll help you find the right apartment in Austin step by step.",
                                            "wrap": True,
                                            "margin": "md"
                                        }
                                    ]
                                },
                                "footer": {
                                    "type": "box",
                                    "layout": "vertical",
                                    "spacing": "sm",
                                    "contents": [
                                        {
                                            "type": "button",
                                            "style": "primary",
                                            "action": {
                                                "type": "postback",
                                                "label": "🤖 Friendly",
                                                "data": "assistant_friendly"
                                            }
                                        },
                                        {
                                            "type": "button",
                                            "style": "primary",
                                            "action": {
                                                "type": "postback",
                                                "label": "📊 Guide",
                                                "data": "assistant_guide"
                                            }
                                        },
                                        {
                                            "type": "button",
                                            "style": "primary",
                                            "action": {
                                                "type": "postback",
                                                "label": "🧠 Expert",
                                                "data": "assistant_expert"
                                            }
                                        }
                                    ]
                                }
                            }

                            send_flex(line_bot_api, event.reply_token, bubble)

                # ---------------- POSTBACK ----------------
                elif isinstance(event, PostbackEvent):

                    data = event.postback.data
                    user = get_user(user_id)

                    # -------- assistant --------
                    if data.startswith("assistant_"):
                        user["assistant_type"] = data.split("_")[1]

                        bubble = {
                            "type": "bubble",
                            "body": {
                                "type": "box",
                                "contents": [{"type": "text", "text": "🏙 Step 1: Choose city"}]
                            },
                            "footer": {
                                "type": "box",
                                "contents": [
                                    {"type": "button",
                                     "action": {"type": "postback",
                                                "label": "Austin",
                                                "data": "city_austin"}}
                                ]
                            }
                        }

                        send_flex(line_bot_api, event.reply_token, bubble)

                    # -------- city --------
                    elif data.startswith("city_"):

                        bubble = {
                            "type": "bubble",
                            "body": {
                                "type": "box",
                                "contents": [{"type": "text", "text": "📍 Step 2: Area"}]
                            },
                            "footer": {
                                "type": "box",
                                "contents": [
                                    {"type": "button",
                                     "action": {"type": "postback",
                                                "label": "Downtown",
                                                "data": "area_downtown"}}
                                ]
                            }
                        }

                        send_flex(line_bot_api, event.reply_token, bubble)

                    # -------- area --------
                    elif data.startswith("area_"):

                        bubble = {
                            "type": "bubble",
                            "body": {
                                "type": "box",
                                "contents": [{"type": "text", "text": "💳 Payment method"}]
                            },
                            "footer": {
                                "type": "box",
                                "contents": [
                                    {"type": "button",
                                     "action": {"type": "postback",
                                                "label": "Mortgage",
                                                "data": "payment_mortgage"}}
                                ]
                            }
                        }

                        send_flex(line_bot_api, event.reply_token, bubble)

                    # -------- payment --------
                    elif data.startswith("payment_"):

                        send_text(
                            line_bot_api,
                            event.reply_token,
                            "🏙 I found 3 apartments in Downtown Austin\n"
                            "💰 Price range: $282k – $300k"
                        )

                        for key in ["luxor", "miracle", "victory"]:
                            apartment = apartments[key]

                            text = (
                                f"🏢 {apartment['title']}\n"
                                f"📍 {apartment['location']}\n"
                                f"💰 {apartment['price']}\n"
                                f"📐 {apartment['size']}\n\n"
                                f"{apartment['description']}"
                            )

                            line_bot_api.push_message(
                                PushMessageRequest(
                                    to=user_id,
                                    messages=[
                                        TextMessage(text=text)
                                    ]
                                )
                            )

                    # -------- LUXOR --------
                    elif data == "choose_luxor":

                        send_text(
                            line_bot_api,
                            event.reply_token,
                            "🏢 Luxor Apartment\n\n"
                            "✨ I’d say Luxor is a really great choice if you want a modern, comfortable place to live — "
                            "it feels very easy and practical.\n\n"
                            "🏙 It’s located in the business center, which makes everyday life much simpler, "
                            "and free high-speed Wi-Fi is already included."
                        )

                    # -------- MIRACLE --------
                    elif data == "choose_miracle":

                        send_text(
                            line_bot_api,
                            event.reply_token,
                            "🏢 Miracle Garden Apartment\n\n"
                            "🌿 Miracle Garden is a wonderful option if you prefer a calm and peaceful lifestyle — "
                            "the whole area feels very relaxed and comfortable for everyday living.\n\n"
                            "🌳 There’s a nearby school, beautiful green surroundings, "
                            "and free resident parking, which is a really valuable advantage in city life."
                        )

                    # -------- VICTORY --------
                    elif data == "choose_victory":

                        send_text(
                            line_bot_api,
                            event.reply_token,
                            "🏢 Victory Mansion\n\n"
                            "🏛 Victory Mansion is a great option if you're thinking about long-term value and investment potential.\n\n"
                            "💡 It has a strong character, a friendly and stable community of neighbors, "
                            "and a warm atmosphere that makes the building feel very welcoming.\n\n"
                            "🍞 One of the unique highlights here is a daily free delivery of bread and milk, "
                            "which adds a really cozy and special touch to everyday living."
                        )

                    # -------- HELP --------
                    elif data == "help_choose":

                        send_text(
                            line_bot_api,
                            event.reply_token,
                            "💡 Here’s a simple guide to help you decide:\n\n"
                            "🏢 Luxor Apartment\n"
                            "A great option if you want modern comfort and easy everyday living.\n\n"
                            "🌿 Miracle Garden Apartment\n"
                            "Perfect if you prefer a calm and balanced lifestyle.\n\n"
                            "🏛 Victory Mansion\n"
                            "Best suited for long-term value and investment potential."
                        )

                    # -------- REPEAT --------
                    elif data == "repeat":

                        send_text(line_bot_api, event.reply_token, "🔄 Showing apartments again...")

                        for key in ["luxor", "miracle", "victory"]:
                            text, images = send_apartment(line_bot_api, event.reply_token, user_id, key)

                            line_bot_api.push_message(
                                PushMessageRequest(
                                    to=user_id,
                                    messages=[TextMessage(text=text)] + images
                                )
                            )

                    # -------- FINISH --------
                    elif data == "finish":

                        bubble = {
                            "type": "bubble",
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text":
                                            "✨ Thank you for using AI Housing Assistant!\n\n"
                                            "🏡 Your selection process is complete.\n\n"
                                            "If you’ve made a decision, you can take the next step below.\n\n"
                                            "I’m always here if you need more options or comparisons."
                                    }
                                ]
                            },
                            "footer": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": "📞 Contact Agent",
                                            "data": "contact_agent"
                                        }
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": "🔄 Compare Again",
                                            "data": "repeat"
                                        }
                                    }
                                ]
                            }
                        }

                        send_flex(line_bot_api, event.reply_token, bubble)
            return "OK", 200

    except Exception:
           logging.error(traceback.format_exc())

    return "OK", 200


# ---------------- NEXT STEP ----------------

def send_next_step(line_bot_api, reply_token):
    bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "👉 What would you like to do next?"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "🏢 View Apartments Again",
                        "data": "repeat"
                    }
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "🤔 Help me choose",
                        "data": "help_choose"
                    }
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "🏁 Finish",
                        "data": "finish"
                    }
                }
            ]
        }
    }

    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=reply_token,
            messages=[FlexMessage(alt_text="next step", contents=bubble)]
        )
    )


# ---------------- RUN ----------------

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)