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

    line_bot_api.push_message(
        PushMessageRequest(
            to=user_id,
            messages=[TextMessage(text=text)]
        )
    )

    images = [
        ImageMessage(original_content_url=url, preview_image_url=url)
        for url in apartment["photos"]
    ]
    for i in range(0, len(images), 5):
        line_bot_api.push_message(
            PushMessageRequest(
                to=user_id,
                messages=images[i:i+5]
            )
        )


def send_all_apartments(user_id):
    line_bot_api.push_message(
        PushMessageRequest(
            to=user_id,
            messages=[TextMessage(
                text="🏙 I found 3 apartments in Downtown Austin\n💰 Price range: $282k – $300k"
            )]
        )
    )
    for key in ["luxor", "miracle", "victory"]:
        send_apartment(user_id, key)
    line_bot_api.push_message(
        PushMessageRequest(
            to=user_id,
            messages=[TextMessage(
                text="🏡 Which apartment would you like?\n\n"
                     "1 - Luxor\n"
                     "2 - Miracle\n"
                     "3 - Victory\n"
                     "4 - Help me choose"
            )]
        )
    )


def send_next_step(user_id):
    line_bot_api.push_message(
        PushMessageRequest(
            to=user_id,
            messages=[TextMessage(
                text="👉 What would you like to do next?\n\n"
                     "1 - 🏢 View Apartments Again\n"
                     "2 - 🏁 Finish"
            )]
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
                                         "1 - Friendly\n"
                                         "2 - Guide\n"
                                         "3 - Expert"
                                )]
                            )
                        )

                    # ---- CHOOSE ASSISTANT ----
                    elif step == "choose_assistant" and text in ["1", "2", "3"]:
                        modes = {"1": "friendly", "2": "guide", "3": "expert"}
                        user["assistant_type"] = modes[text]
                        user["step"] = "choose_city"
                        line_bot_api.reply_message(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[TextMessage(
                                    text=f"✅ {modes[text].capitalize()} mode selected!\n\n"
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
                        send_all_apartments(user_id)

                    # ---- CHOOSE APARTMENT ----
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
                                    messages=[TextMessage(text="🔄 Showing apartments again...")]
                                )
                            )
                            send_all_apartments(user_id)
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