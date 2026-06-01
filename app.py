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
    ImageMessage
)

from linebot.v3.webhook import WebhookParser
from linebot.v3.webhooks import MessageEvent, PostbackEvent

# ---------------- LOGGING ----------------

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# ---------------- TOKEN ----------------

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


# ---------------- MESSAGES ----------------

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
        "description":
            "Modern apartment in the business center with modern interior design.\n"
            "Move-in ready, no renovation required.\n\n"
            "✅ Free high-speed Wi-Fi included\n"
            "✅ Metro and transport nearby",
        "photos": [
            "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975318/Luxor_01_iyx5uc.jpg",
            "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975444/Luxor_02_x4upom.jpg",
            "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975443/Luxor_03_yglqcw.jpg"
        ]
    },

    "miracle": {
        "title": "Miracle Garden Apartment",
        "location": "Downtown Austin",
        "price": "$295,000",
        "size": "85 m²",
        "description":
            "Apartment near central park in a quiet and green neighborhood.\n"
            "School nearby. Renovation completed one year ago.\n\n"
            "✅ Free resident parking\n"
            "✅ Modern and practical layout",
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
        "description":
            "Historic city center apartment close to attractions.\n"
            "Requires renovation but has strong potential.\n\n"
            "✅ Free daily bread and milk delivery\n"
            "✅ Nearby bakery and farmers market",
        "photos": [
            "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975445/Victory_Mansion_01_mx3sme.jpg",
            "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975445/Victory_Mansion_02_at00es.jpg",
            "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975446/Victory_Mansion_03_vu0zpn.jpg"
        ]
    }
}


# ---------------- HELPERS ----------------

def send_text(reply_token, text):
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text=text)]
        )
    )


# Send apartment info (text + photos) via push
def send_apartment(user_id, key):
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

    # Apartment text
    line_bot_api.push_message(
        PushMessageRequest(
            to=user_id,
            messages=[TextMessage(text=text)]
        )
    )

    # Apartment photos
    images = [
        ImageMessage(original_content_url=url, preview_image_url=url)
        for url in apartment["photos"]
    ]

    # LINE allows up to 5 messages at a time, so we split into batches
    for i in range(0, len(images), 5):
        line_bot_api.push_message(
            PushMessageRequest(
                to=user_id,
                messages=images[i:i + 5]
            )
        )


# "What's next?" menu after viewing an apartment
def send_next_step(user_id):
    bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "👉 What would you like to do next?",
                    "weight": "bold",
                    "size": "md"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                        "type": "postback",
                        "label": "🏢 View Apartments Again",
                        "data": "repeat"
                    }
                },
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                        "type": "postback",
                        "label": "🤔 Help me choose",
                        "data": "help_choose"
                    }
                },
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                        "type": "postback",
                        "label": "🏁 Finish",
                        "data": "finish"
                    }
                }
            ]
        }
    }

    line_bot_api.push_message(
        PushMessageRequest(
            to=user_id,
            messages=[FlexMessage(alt_text="next step", contents=bubble)]
        )
    )


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
                logging.warning("No user_id found in event source")
                continue

            user = get_user(user_id)

            # ---------------- MESSAGE ----------------
            if isinstance(event, MessageEvent):

                if hasattr(event.message, "text"):
                    text = event.message.text.lower()

                    if text == "start":
                        user_state[user_id] = {}

                        bubble = {
                            "type": "bubble",
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {"type": "text", "text": "🏡 AI Housing Assistant", "weight": "bold", "size": "lg"},
                                    {"type": "text",
                                     "text": "I will help you find the perfect apartment in Austin step by step.",
                                     "wrap": True}
                                ]
                            },
                            "footer": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {"type": "button",
                                     "action": {"type": "postback", "label": "Friendly", "data": "assistant_friendly"}},
                                    {"type": "button",
                                     "action": {"type": "postback", "label": "Guide", "data": "assistant_guide"}},
                                    {"type": "button",
                                     "action": {"type": "postback", "label": "Expert", "data": "assistant_expert"}}
                                ]
                            }
                        }

                        line_bot_api.reply_message(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[FlexMessage(alt_text="start", contents=bubble)]
                            )
                        )

            # ---------------- POSTBACK ----------------
            elif isinstance(event, PostbackEvent):

                data = event.postback.data

                # -------- ASSISTANT --------
                if data.startswith("assistant_"):
                    user["assistant_type"] = data.split("_")[1]

                    bubble = {
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
                                {"type": "button",
                                 "action": {"type": "postback", "label": "Austin", "data": "city_austin"}}
                            ]
                        }
                    }

                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[FlexMessage(alt_text="step1", contents=bubble)]
                        )
                    )

                # -------- CITY --------
                elif data.startswith("city_"):

                    bubble = {
                        "type": "bubble",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "text", "text": "📍 Step 2: Choose area"}
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "button",
                                 "action": {"type": "postback", "label": "Downtown", "data": "area_downtown"}}
                            ]
                        }
                    }

                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[FlexMessage(alt_text="step2", contents=bubble)]
                        )
                    )

                # -------- AREA --------
                elif data.startswith("area_"):

                    bubble = {
                        "type": "bubble",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "text", "text": "💳 Step 3: Payment method"}
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "button",
                                 "action": {"type": "postback", "label": "Mortgage", "data": "payment_mortgage"}}
                            ]
                        }
                    }

                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[FlexMessage(alt_text="step3", contents=bubble)]
                        )
                    )

                # -------- PAYMENT --------
                elif data.startswith("payment_"):

                    # 1) Один reply на токен
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(
                                text="🏙 I found 3 apartments in Downtown Austin\n💰 Price range: $282k – $300k"
                            )]
                        )
                    )

                    # 2) Send all apartments via push
                    for key in ["luxor", "miracle", "victory"]:
                        send_apartment(user_id, key)

                    # 3) Apartment selection menu (push)
                    choose_bubble = {
                        "type": "bubble",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "text", "text": "🏡 Which apartment would you like?"}
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "button",
                                 "action": {"type": "postback", "label": "Luxor", "data": "choose_luxor"}},
                                {"type": "button",
                                 "action": {"type": "postback", "label": "Miracle", "data": "choose_miracle"}},
                                {"type": "button",
                                 "action": {"type": "postback", "label": "Victory", "data": "choose_victory"}},
                                {"type": "button",
                                 "action": {"type": "postback", "label": "Help me choose", "data": "help_choose"}}
                            ]
                        }
                    }

                    line_bot_api.push_message(
                        PushMessageRequest(
                            to=user_id,
                            messages=[FlexMessage(alt_text="choose", contents=choose_bubble)]
                        )
                    )

                # -------- CHOOSE --------
                elif data == "choose_luxor":
                    send_text(event.reply_token,
                              "🏢 Luxor Apartment\n\n"
                              "✨ I'd say Luxor is a really great choice if you want a modern, comfortable place to live — "
                              "it feels very easy and practical.\n\n"
                              "🏙 It's located in the business center, which makes everyday life much simpler, "
                              "and free high-speed Wi-Fi is already included.")
                    send_next_step(user_id)

                elif data == "choose_miracle":
                    send_text(event.reply_token,
                              "🌿 Miracle Garden is a wonderful option if you prefer a calm and peaceful lifestyle — "
                              "the whole area feels very relaxed and comfortable for everyday living.\n\n"
                              "🌳 There's a nearby school, beautiful green surroundings, "
                              "and free resident parking.")
                    send_next_step(user_id)

                elif data == "choose_victory":
                    send_text(event.reply_token,
                              "🏛 Victory Mansion is a great option for long-term value and investment potential.\n\n"
                              "It has a strong character, friendly neighbors, and a warm atmosphere.\n\n"
                              "Bonus: free bread & milk delivery.")
                    send_next_step(user_id)

                elif data == "help_choose":
                    send_text(event.reply_token,
                              "✨ Luxor = modern\n"
                              "🌿 Miracle = calm\n"
                              "🏛 Victory = investment")
                    send_next_step(user_id)

                # -------- REPEAT --------
                elif data == "repeat":
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text="🔄 Showing apartments again...")]
                        )
                    )

                    for key in ["luxor", "miracle", "victory"]:
                        send_apartment(user_id, key)

                    send_next_step(user_id)

                # -------- FINISH --------
                elif data == "finish":

                    bubble = {
                        "type": "bubble",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "text", "text": "✨ Thank you for using AI Housing Assistant!", "wrap": True},
                                {"type": "text", "text": "🏡 Your selection process is complete.", "wrap": True},
                                {"type": "text", "text": "I'm always here if you need more options.", "wrap": True}
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "button", "style": "primary", "action": {"type": "postback", "label":
                                    "📞 Contact Agent", "data": "contact_agent"}},
                                {"type": "button", "style": "primary", "action": {"type": "postback", "label":
                                    "🏦 Mortgage", "data": "mortgage_help"}},
                                {"type": "button", "style": "primary", "action": {"type": "postback", "label":
                                    "🔄 Compare Again", "data": "repeat"}}
                            ]
                        }
                    }

                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[FlexMessage(alt_text="finish", contents=bubble)]
                        )
                    )

                # -------- ADDED HANDLERS for finish buttons --------
                elif data == "contact_agent":
                    send_text(event.reply_token,
                              "📞 You can contact our agent.")

                elif data == "mortgage_help":
                    send_text(event.reply_token,
                              "🏦 You can contact a mortgage specialist.")

                # (Optional: if something unknown comes in – we ignore it, but better to reply)
                else:
                    # Reply just in case, so LINE doesn't time out
                    send_text(event.reply_token, "I'm sorry, I didn't understand that. Please use the buttons.")

        return "OK", 200

    except Exception as e:
        logging.error(traceback.format_exc())
        return "error", 500


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
