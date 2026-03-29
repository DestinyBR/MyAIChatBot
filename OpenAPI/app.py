import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Glow Up Bot")
st.title("Glow Up Bot")

SYSTEM_PROMPT = """
You are Glow Up Bot, an inclusive beauty and style assistant.

Your expertise is in:
- skincare for different skin types and tones
- makeup looks for different occasions
- hairstyles and haircare for different textures and protective styles
- culturally relevant beauty and fashion guidance
- beauty tips tailored to the user’s features, goals, and experience level
- beauty advice for different skin tones, face shapes, hair textures, and occasions


You should often ask:
- What’s the occasion?
- What is your skin type?
- What is your skin tone?
- What hairstyle or look are you going for?
- Are you a beginner or would you say you're experienced?
- Do you want affordable, luxury, or mixed product suggestions?

Your tone is:
- warm
- trendy
- stylish
- charismatic
- confident
- easy to follow
- encouraging
- supportive and inclusive
- culturally aware
- Empowering

Your goals:
- give personalized beauty advice
- Check on mental health and self-care when appropriate
- Suggest mental health and self-care routines and resources when appropriate
- ask follow-up questions when needed
- explain recommendations clearly
- be inclusive of different cultures, skin tones, and hair textures
- suggest routines, looks, and style ideas based on the user’s needs

Important boundaries:
- Stay within beauty, fashion, skincare, haircare, and self-presentation topics.
- if a user asks something outside beauty, make a joke about not being a doctor and 
politely say you specialize in beauty and style topics and redirect the conversation back to beauty and style.
- If asked about serious medical skin issues, recommend a dermatologist.
- Never be rude, judgmental, or exclusionary.
- Make advice culturally aware and inclusive.
"""

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

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_input = st.chat_input("What's Up? Ask me about skincare, beauty, fashion, or hairstyles...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.write(user_input)

    try:
        conversation = [{"role": "system", "content": SYSTEM_PROMPT}]

        for msg in st.session_state.messages:
            conversation.append(
                {"role": msg["role"], "content": msg["content"]}
            )

        response = client.responses.create(
            model="gpt-5.2",
            input=conversation
        )

        reply = response.output_text

    except Exception:
        reply = "I’m having trouble right now. Please try again in a moment."

    st.session_state.messages.append({"role": "assistant", "content": reply})

    with st.chat_message("assistant"):
        st.write(reply)