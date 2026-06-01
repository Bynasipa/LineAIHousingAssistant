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
    ImageMessage,
    FlexContainer
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

# ---------------- APARTMENTS ----------------

apartments = {
    "luxor": {
        "title": "Luxor Apartment",
        "location": "Downtown Austin",
        "price": "$300,000",
        "size": "82 m²",
        "description": "Modern apartment in the business center with modern interior design. Move-in ready, no renovation required.",
        "features": ["Free high-speed Wi-Fi included", "Metro and transport nearby"],
        "cover": "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975318/Luxor_01_iyx5uc.jpg",
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
        "description": "Apartment near central park in a quiet and green neighborhood. School nearby. Renovation completed one year ago.",
        "features": ["Free resident parking", "Modern and practical layout"],
        "cover": "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975445/Miracle_Garden_01_ee1iuk.jpg",
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
        "description": "Historic city center apartment close to attractions. Requires renovation but has strong potential.",
        "features": ["Free daily bread and milk delivery", "Nearby bakery and farmers market"],
        "cover": "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975445/Victory_Mansion_01_mx3sme.jpg",
        "photos": [
            "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975445/Victory_Mansion_01_mx3sme.jpg",
            "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975445/Victory_Mansion_02_at00es.jpg",
            "https://res.cloudinary.com/dekw8i9b8/image/upload/v1779975446/Victory_Mansion_03_vu0zpn.jpg"
        ]
    }
}


# ---------------- FLEX CARD BUILDER ----------------

def build_apartment_card(key, mode):
    apt = apartments[key]

    if mode == "friendly":
        insight = random.choice(friendly_messages[key])
    elif mode == "guide":
        insight = random.choice(guide_messages[key])
    else:
        insight = random.choice(expert_messages[key])

    features_text = "  ✅ " + "\n  ✅ ".join(apt["features"])

    card = {
        "type": "bubble",
        "size": "kilo",
        "hero": {
            "type": "image",
            "url": apt["cover"],
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover",
            "action": {
                "type": "postback",
                "label": "view_photos",
                "data": f"action=photos&apt={key}"
            }
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
                    "spacing": "sm",
                    "margin": "xs",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"📍 {apt['location']}",
                            "size": "xs",
                            "color": "#888888",
                            "flex": 1,
                            "wrap": True
                        },
                        {
                            "type": "text",
                            "text": apt["size"],
                            "size": "xs",
                            "color": "#888888",
                            "align": "end"
                        }
                    ]
                },
                {
                    "type": "text",
                    "text": apt["price"],
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
                    "text": f"💡 {insight}",
                    "size": "xs",
                    "color": "#555577",
                    "wrap": True,
                    "margin": "sm",
                    "style": "italic"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "paddingAll": "12px",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "📸 View All Photos",
                        "data": f"action=photos&apt={key}"
                    },
                    "style": "secondary",
                    "height": "sm",
                    "color": "#f0f0f0"
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "✅ Choose This Apartment",
                        "data": f"action=choose&apt={key}"
                    },
                    "style": "primary",
                    "height": "sm",
                    "color": "#e63946"
                }
            ]
        }
    }
    return card


def build_carousel(user_id):
    user = get_user(user_id)
    mode = user.get("assistant_type", "friendly")

    bubbles = [build_apartment_card(key, mode) for key in ["luxor", "miracle", "victory"]]

    return {
        "type": "carousel",
        "contents": bubbles
    }


# ---------------- HELPERS ----------------

def send_text(reply_token, text):
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text=text)]
        )
    )


def push_text(user_id, text):
    line_bot_api.push_message(
        PushMessageRequest(
            to=user_id,
            messages=[TextMessage(text=text)]
        )
    )


def send_photos(user_id, key):
    apt = apartments[key]
    push_text(user_id, f"📸 {apt['title']} — All Photos")
    images = [
        ImageMessage(original_content_url=url, preview_image_url=url)
        for url in apt["photos"]
    ]
    for i in range(0, len(images), 5):
        line_bot_api.push_message(
            PushMessageRequest(
                to=user_id,
                messages=images[i:i + 5]
            )
        )


def send_carousel(reply_token, user_id):
    carousel = build_carousel(user_id)
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=reply_token,
            messages=[
                TextMessage(
                    text="🏙 I found 3 apartments in Downtown Austin\n💰 Price range: $282k – $300k\n\n👇 Swipe to browse:"
                ),
                FlexMessage(
                    alt_text="3 Apartments in Downtown Austin",
                    contents=FlexContainer.from_dict(carousel)
                )
            ]
        )
    )


def push_carousel(user_id):
    carousel = build_carousel(user_id)
    line_bot_api.push_message(
        PushMessageRequest(
            to=user_id,
            messages=[
                TextMessage(
                    text="🏙 Here are the apartments again:\n\n👇 Swipe to browse:"
                ),
                FlexMessage(
                    alt_text="3 Apartments in Downtown Austin",
                    contents=FlexContainer.from_dict(carousel)
                )
            ]
        )
    )


def send_next_step(user_id):
    push_text(
        user_id,
        "👉 What would you like to do next?\n\n"
        "1 - 🏢 View Apartments Again\n"
        "2 - 🏁 Finish"
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

            # ---------------- POSTBACK EVENT ----------------
            if isinstance(event, PostbackEvent):
                data = event.postback.data
                params = dict(p.split("=") for p in data.split("&") if "=" in p)
                action = params.get("action")
                apt_key = params.get("apt")

                logging.info("POSTBACK: action=%s apt=%s", action, apt_key)

                if action == "photos" and apt_key in apartments:
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(
                                text=f"📸 Loading photos for {apartments[apt_key]['title']}..."
                            )]
                        )
                    )
                    send_photos(user_id, apt_key)

                elif action == "choose" and apt_key in apartments:
                    apt = apartments[apt_key]
                    user["step"] = "next_step"
                    user["chosen"] = apt_key

                    summaries = {
                        "luxor": "✨ Great choice for modern comfortable living.\n🏙 Located in the business center with free Wi-Fi.",
                        "miracle": "🌿 Calm and peaceful lifestyle.\n🌳 Nearby school, green surroundings, free parking.",
                        "victory": "🏛 Great for long-term investment.\n🎁 Bonus: free bread & milk delivery every day."
                    }

                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(
                                text=f"🏠 You selected: {apt['title']}\n\n{summaries[apt_key]}"
                            )]
                        )
                    )
                    send_next_step(user_id)

            # ---------------- MESSAGE EVENT ----------------
            elif isinstance(event, MessageEvent):
                logging.info("MESSAGE EVENT received")

                if hasattr(event.message, "text"):
                    text = event.message.text.strip().lower()
                    step = user.get("step", "")
                    logging.info("Text: [%s] Step: [%s]", text, step)

                    # ---- START ----
                    if text == "start":
                        user_state[user_id] = {"step": "choose_assistant"}
                        line_bot_api.reply_message(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[TextMessage(
                                    text="🏡 Welcome to AI Housing Assistant!\n\n"
                                         "I will help you find the perfect apartment in Austin.\n\n"
                                         "Please choose your assistant type:\n\n"
                                         "1 - 😊 Friendly\n"
                                         "2 - 🧭 Guide\n"
                                         "3 - 🧠 Expert"
                                )]
                            )
                        )

                    # ---- CHOOSE ASSISTANT ----
                    elif step == "choose_assistant" and text in ["1", "2", "3"]:
                        modes = {"1": "friendly", "2": "guide", "3": "expert"}
                        mode_labels = {"1": "😊 Friendly", "2": "🧭 Guide", "3": "🧠 Expert"}
                        user["assistant_type"] = modes[text]
                        user["step"] = "choose_city"
                        line_bot_api.reply_message(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[TextMessage(
                                    text=f"✅ {mode_labels[text]} mode selected!\n\n"
                                         "🏙 Step 1: Choose city\n\n"
                                         "1 - Austin"
                                )]
                            )
                        )

                    # ---- CHOOSE CITY ----
                    elif step == "choose_city" and text == "1":
                        user["step"] = "choose_area"
                        line_bot_api.reply_message(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[TextMessage(
                                    text="📍 Step 2: Choose area\n\n"
                                         "1 - Downtown"
                                )]
                            )
                        )

                    # ---- CHOOSE AREA ----
                    elif step == "choose_area" and text == "1":
                        user["step"] = "choose_payment"
                        line_bot_api.reply_message(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[TextMessage(
                                    text="💳 Step 3: Payment method\n\n"
                                         "1 - Mortgage"
                                )]
                            )
                        )

                    # ---- CHOOSE PAYMENT ----
                    elif step == "choose_payment" and text == "1":
                        user["step"] = "choose_apartment"
                        line_bot_api.reply_message(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[TextMessage(text="🔍 Searching for apartments...")]
                            )
                        )
                        push_carousel(user_id)

                    # ---- CHOOSE APARTMENT (text fallback) ----
                    elif step == "choose_apartment" and text in ["1", "2", "3", "4"]:
                        user["step"] = "next_step"
                        if text == "1":
                            send_text(event.reply_token,
                                      "🏢 Luxor Apartment\n\n"
                                      "✨ Great choice for modern comfortable living.\n"
                                      "🏙 Located in the business center with free Wi-Fi.")
                        elif text == "2":
                            send_text(event.reply_token,
                                      "🌿 Miracle Garden\n\n"
                                      "Calm and peaceful lifestyle.\n"
                                      "🌳 Nearby school, green surroundings, free parking.")
                        elif text == "3":
                            send_text(event.reply_token,
                                      "🏛 Victory Mansion\n\n"
                                      "Great for long-term investment.\n"
                                      "Bonus: free bread & milk delivery.")
                        elif text == "4":
                            send_text(event.reply_token,
                                      "✨ Luxor = modern\n"
                                      "🌿 Miracle = calm\n"
                                      "🏛 Victory = investment")
                        send_next_step(user_id)

                    # ---- NEXT STEP ----
                    elif step == "next_step" and text in ["1", "2"]:
                        if text == "1":
                            user["step"] = "choose_apartment"
                            line_bot_api.reply_message(
                                ReplyMessageRequest(
                                    reply_token=event.reply_token,
                                    messages=[TextMessage(
                                        text="🏡 Which apartment would you like?\n\n"
                                             "1 - Luxor\n"
                                             "2 - Miracle\n"
                                             "3 - Victory\n"
                                             "4 - Help me choose"
                                    )]
                                )
                            )
                        elif text == "2":
                            user["step"] = "finish"
                            line_bot_api.reply_message(
                                ReplyMessageRequest(
                                    reply_token=event.reply_token,
                                    messages=[TextMessage(
                                        text="✨ Thank you for using AI Housing Assistant!\n\n"
                                             "🏡 Your selection process is complete.\n\n"
                                             "1 - 📞 Contact Agent\n"
                                             "2 - 🏦 Mortgage"
                                    )]
                                )
                            )

                    # ---- FINISH OPTIONS ----
                    elif step == "finish" and text in ["1", "2"]:
                        if text == "1":
                            send_text(event.reply_token, "📞 You can contact our agent.")
                        elif text == "2":
                            send_text(event.reply_token, "🏦 You can contact a mortgage specialist.")

                    # ---- UNKNOWN ----
                    else:
                        line_bot_api.reply_message(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[TextMessage(text="Please type Start to begin.")]
                            )
                        )

        return "OK", 200

    except Exception as e:
        logging.error("FULL ERROR: %s", traceback.format_exc())
        return "error", 500


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

