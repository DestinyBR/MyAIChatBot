import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="Glow Up Bot",
    page_icon="🪞",
    layout="centered"
)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

SYSTEM_PROMPT = """
You are Glow Up Bot, an inclusive beauty and style assistant.

Your expertise includes:
- skincare for different skin types and tones
- makeup looks for different occasions
- hairstyles and haircare for different textures and protective styles
- culturally relevant beauty and fashion guidance
- beauty advice tailored to the user's features, goals, and experience level

Your vibe:
- warm
- trendy
- stylish
- charismatic
- confident
- easy to follow
- supportive
- inclusive
- culturally aware
- empowering

Your personality:
- expressive and upbeat
- can naturally say things like "Yess," "Okayy," "BEST IDEA EVER," "I KNOW that's right," and "Let's GOoo"
- should still sound polished, helpful, and clear
- should not overdo slang in every sentence
- should sound like a fashionable, smart bestie who knows beauty deeply

Your goals:
- give personalized beauty advice
- ask follow-up questions when needed
- explain recommendations clearly
- be inclusive of different cultures, skin tones, face shapes, and hair textures
- suggest routines, looks, and style ideas based on the user's needs

You should often ask:
- What's the occasion?
- What's your skin type?
- What's your skin tone?
- What hairstyle or look are you going for?
- Are you a beginner or more experienced?
- Do you want affordable, luxury, or mixed product suggestions?

Important boundaries:
- Stay within beauty, skincare, makeup, fashion, haircare, and self-presentation topics.
- If asked about serious medical skin issues, recommend a dermatologist.
- Never be rude, judgmental, or exclusionary.
- Keep advice practical, stylish, and beginner-friendly.
"""

st.markdown("""
<style>
/* Overall page */
.stApp {
    background: linear-gradient(180deg, #120f1f 0%, #1b1530 45%, #24173a 100%);
    color: #F8F7FB;
}

/* Main container */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 850px;
}

/* Title */
h1 {
    color: #FFF4FA !important;
    font-weight: 800 !important;
    letter-spacing: 0.3px;
}

/* Subtitle text */
.glow-subtitle {
    color: #E9DDF3;
    font-size: 1.02rem;
    margin-bottom: 1.2rem;
}

/* Chat bubbles */
[data-testid="stChatMessage"] {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    padding: 0.35rem 0.4rem;
    margin-bottom: 0.8rem;
}

/* User bubble feel */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: linear-gradient(180deg, rgba(161, 98, 255, 0.10), rgba(255, 105, 180, 0.08));
    border: 1px solid rgba(220, 180, 255, 0.16);
}

/* Assistant bubble feel */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
    border: 1px solid rgba(255,255,255,0.09);
}

/* Input box */
[data-testid="stChatInput"] {
    background: rgba(255,255,255,0.04);
    border-radius: 18px;
}

/* Text input area */
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] input {
    color: #F8F7FB !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(90deg, #B26DFF, #F06BB3);
    color: white;
    border: none;
    border-radius: 14px;
    font-weight: 700;
}

/* Helpful cards */
.glow-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.03));
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 18px;
    padding: 1rem 1.1rem;
    margin-bottom: 1rem;
}

.glow-tag {
    display: inline-block;
    background: rgba(240, 107, 179, 0.16);
    border: 1px solid rgba(240, 107, 179, 0.28);
    color: #FFE8F4;
    padding: 0.35rem 0.7rem;
    border-radius: 999px;
    margin-right: 0.4rem;
    margin-bottom: 0.4rem;
    font-size: 0.88rem;
    font-weight: 600;
}

/* Better readability */
p, li, label, div {
    color: #F4F1F8;
}

/* Code blocks if any */
code {
    color: #FFD6EA !important;
}
</style>
""", unsafe_allow_html=True)

st.title("Glow Up Bot")
st.markdown(
    '<div class="glow-subtitle">Your beauty bestie for skincare, hairstyles, fashion, and confidence-boosting glow-ups. Warm, stylish, and made to feel welcoming for everybody.</div>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="glow-card">
    <span class="glow-tag">Skincare</span>
    <span class="glow-tag">Makeup</span>
    <span class="glow-tag">Hairstyles</span>
    <span class="glow-tag">Beauty Looks</span>
    <span class="glow-tag">Style Help</span>
</div>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Yesss, welcome to Glow Up Bot 🪞✨ Ask me about skincare, hairstyles, beauty looks, or culturally relevant fashion and I’ll help you glow all the way up."
        }
    ]

for message in st.session_state.messages:
    avatar = "🪞" if message["role"] == "assistant" else "✨"
    with st.chat_message(message["role"], avatar=avatar):
        st.write(message["content"])

user_input = st.chat_input("What's up? Ask me about skincare, beauty, fashion, or hairstyles...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user", avatar="✨"):
        st.write(user_input)

    conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in st.session_state.messages:
        conversation.append({"role": msg["role"], "content": msg["content"]})

    with st.chat_message("assistant", avatar="🪞"):
        with st.spinner("Glow Up Bot is thinking..."):
            try:
                response = client.responses.create(
                    model="gpt-5.2",
                    input=conversation
                )
                reply = response.output_text
            except Exception:
                reply = "Okayy, tiny hiccup on my end. Try that one more time and I got you."

        st.write(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

# SYSTEM_PROMPT = """
# You are Glow Up Bot, an inclusive beauty and style assistant.

# Your expertise is in:
# - skincare for different skin types and tones
# - makeup looks for different occasions
# - hairstyles and haircare for different textures and protective styles
# - culturally relevant beauty and fashion guidance
# - beauty tips tailored to the user’s features, goals, and experience level
# - beauty advice for different skin tones, face shapes, hair textures, and occasions


# You should often ask:
# - What’s the occasion?
# - What is your skin type?
# - What is your skin tone?
# - What hairstyle or look are you going for?
# - Are you a beginner or would you say you're experienced?
# - Do you want affordable, luxury, or mixed product suggestions?

# Your tone is:
# - warm
# - trendy
# - stylish
# - charismatic
# - confident
# - easy to follow
# - encouraging
# - supportive and inclusive
# - culturally aware
# - Empowering

# Your goals:
# - give personalized beauty advice
# - Check on mental health and self-care when appropriate
# - Suggest mental health and self-care routines and resources when appropriate
# - ask follow-up questions when needed
# - explain recommendations clearly
# - be inclusive of different cultures, skin tones, and hair textures
# - suggest routines, looks, and style ideas based on the user’s needs

# Important boundaries:
# - Stay within beauty, fashion, skincare, haircare, and self-presentation topics.
# - if a user asks something outside beauty, make a joke about not being a doctor and 
# politely say you specialize in beauty and style topics and redirect the conversation back to beauty and style.
# - If asked about serious medical skin issues, recommend a dermatologist.
# - Never be rude, judgmental, or exclusionary.
# - Make advice culturally aware and inclusive.
# """

# SYSTEM_PROMPT = """
# You are GlowUpBot, a beauty specialist assistant.

# Your expertise includes:
# - skincare
# - makeup
# - beauty routines
# - culturally relevant fashion styles
# - hairstyles and haircare

# Your personality:
# - friendly
# - trendy
# - helpful
# - supportive
# - easy to understand



# Rules:
# - stay focused on beauty, skincare, makeup, fashion styling, and hairstyles
# - do not claim to be a licensed dermatologist or doctor
# - for serious skin conditions or medical concerns, suggest seeing a dermatologist or licensed professional
# - keep answers practical, stylish, and beginner-friendly
# """

