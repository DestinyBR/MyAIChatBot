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
.stApp {
    background: linear-gradient(180deg, #120f1f 0%, #1a1430 45%, #24173b 100%);
    color: #F8F7FB;
}

.block-container {
    max-width: 900px;
    padding-top: 1.8rem;
    padding-bottom: 2rem;
}

h1, h2, h3 {
    color: #FFF7FB !important;
}

.glow-hero {
    background: linear-gradient(135deg, rgba(178,109,255,0.16), rgba(240,107,179,0.14));
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 24px;
    padding: 1.4rem 1.2rem;
    margin-bottom: 1rem;
    box-shadow: 0 0 0 2px rgba(240,107,179,0.5);
}

.glow-title {
    font-size: 3rem;
    font-weight: 800;
    margin-bottom: 0.35rem;
    color: #FFF4FA;
    letter-spacing: 0.2px;
}

.glow-subtitle {
    font-size: 1.06rem;
    color: #EFE6F7;
    line-height: 1.6;
}

.glow-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.03));
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 20px;
    padding: 1rem;
    margin-bottom: 1rem;
}

.glow-tag {
    display: inline-block;
    background: rgba(240, 107, 179, 0.14);
    border: 1px solid rgba(240, 107, 179, 0.25);
    color: #FFEAF4;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    margin-right: 0.45rem;
    margin-bottom: 0.45rem;
    font-size: 0.88rem;
    font-weight: 700;
}

.glow-tip {
    color: #E8DDF4;
    font-size: 0.96rem;
    margin-top: 0.25rem;
}

[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 0.4rem 0.45rem;
    margin-bottom: 0.9rem;
}

[data-testid="stChatInput"] {
    background: rgba(255,255,255,0.04);
    border-radius: 18px;
}

[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] input {
    color: #F8F7FB !important;
}

.stButton > button {
    width: 100%;
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.08);
    background: linear-gradient(90deg, rgba(178,109,255,0.95), rgba(240,107,179,0.92));
    color: white;
    font-weight: 800;
    padding: 0.6rem 0.8rem;
}

.stButton > button:hover {
    border: 1px solid rgba(255,255,255,0.14);
    filter: brightness(1.03);
}

p, li, div, label {
    color: #F5F2F8;
}

hr {
    border-color: rgba(255,255,255,0.08);
}
 /* CHAT INPUT CONTAINER */
[data-testid="stChatInput"] {
    background: linear-gradient(135deg, rgba(178,109,255,0.15), rgba(240,107,179,0.12));
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 20px;
    padding: 0.4rem;
    backdrop-filter: blur(10px);
}

/* INPUT FIELD */
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] input {
    background: transparent !important;
    color: #F8F7FB !important;
    border: none !important;
    font-size: 1rem;
}

/* REMOVE UGLY RED BORDER */
[data-testid="stChatInput"] textarea:focus,
[data-testid="stChatInput"] input:focus {
    outline: none !important;
    box-shadow: 0 0 0 2px rgba(178,109,255,0.6) !important;
}

/* SEND BUTTON */
[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, #B26DFF, #F06BB3);
    border-radius: 12px;
    border: none;
    color: white;
    transition: 0.2s ease;
}

/* BUTTON HOVER */
[data-testid="stChatInput"] button:hover {
    filter: brightness(1.1);
    transform: scale(1.03);
}           
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Yesss, welcome to Glow Up Bot 🪞✨ I’m your beauty bestie for skincare, hairstyles, makeup, and style help. Ask me anything glow-up related and let’s GOoo."
        }
    ]

if "prefill" not in st.session_state:
    st.session_state.prefill = ""

st.markdown("""
<div class="glow-hero">
    <div class="glow-title">Glow Up Bot 🪞</div>
    <div class="glow-subtitle">
        Warm, stylish, and inclusive beauty guidance for skincare, makeup, hairstyles, and culturally relevant fashion.
        Made to feel welcoming, expressive, and easy to use for everybody.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="glow-card">
    <span class="glow-tag">Skincare</span>
    <span class="glow-tag">Makeup</span>
    <span class="glow-tag">Hairstyles</span>
    <span class="glow-tag">Fashion</span>
    <span class="glow-tag">Beauty Routines</span>
    <div class="glow-tip">Pick a starter button below or type your own beauty question.</div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

with col1:
    if st.button("✨ Skincare Help"):
        st.session_state.prefill = "My skin has been acting up lately. Can you help me build a skincare routine?"

with col2:
    if st.button("💄 Makeup Look"):
        st.session_state.prefill = "Help me choose a makeup look for an event."

with col3:
    if st.button("🪮 Hairstyle Ideas"):
        st.session_state.prefill = "What hairstyle would look best for me based on my vibe and hair texture?"

with col4:
    if st.button("👗 Style Me"):
        st.session_state.prefill = "Help me put together a stylish look that fits my personality and occasion."

st.markdown("---")

for message in st.session_state.messages:
    avatar = "🪞" if message["role"] == "assistant" else "✨"
    with st.chat_message(message["role"], avatar=avatar):
        st.write(message["content"])

prompt = st.chat_input(
    "What's up? Ask me about skincare, beauty, fashion, or hairstyles..."
)

user_input = prompt or st.session_state.prefill

if user_input:
    st.session_state.prefill = ""

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

