from pathlib import Path

app_code = r'''import base64
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI


# -----------------------------
# App setup
# -----------------------------
load_dotenv()

st.set_page_config(
    page_title="Glow Up Bot",
    page_icon="🪞",
    layout="wide",
)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OPENAI_API_KEY not found. Add it to your .env file or Streamlit secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
PROFILE_PATH = DATA_DIR / "glowup_profile.json"

SYSTEM_PROMPT = """
You are Glow Up Bot, an inclusive beauty and style assistant.

Your expertise includes:
- skincare for different skin types and tones
- makeup looks for different occasions
- hairstyles and haircare for different textures and protective styles
- culturally relevant beauty and fashion guidance
- beauty advice tailored to face shape, undertone, skin tone, hair texture, vibe, budget, and experience level

Your vibe:
- warm
- trendy
- polished
- expressive
- supportive
- inclusive
- culturally aware
- empowering

Your personality:
- naturally upbeat and stylish
- can occasionally say things like "Yess," "Okayy," "Let’s gooo," and "I know that’s right"
- should still sound clear, thoughtful, and expert
- should not overuse slang

Important behavior:
- stay focused on beauty, style, skincare, makeup, fashion, haircare, and self-presentation
- if asked about serious medical skin issues, recommend a dermatologist
- ask follow-up questions when needed
- be specific and practical
- personalize advice to the user profile whenever profile details are available
- when giving recommendations, explain WHY they fit the user
- when useful, structure answers with short sections and bullet points

When profile details are available, use them:
- favorite colors
- preferred styles
- best colors already found
- face shape
- undertone
- skin tone
- hair texture
- budget

At the end of recommendations, include a tiny "Saved profile update" line ONLY if new stable preferences were clearly stated or inferred.
"""


# -----------------------------
# Persistence helpers
# -----------------------------
DEFAULT_PROFILE: Dict[str, object] = {
    "name": "",
    "favorite_colors": [],
    "favorite_styles": [],
    "best_colors": [],
    "undertone": "",
    "skin_tone": "",
    "face_shape": "",
    "hair_texture": "",
    "budget": "",
    "notes": []
}


def load_profile() -> Dict[str, object]:
    if PROFILE_PATH.exists():
        try:
            data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
            merged = DEFAULT_PROFILE.copy()
            merged.update(data)
            return merged
        except Exception:
            return DEFAULT_PROFILE.copy()
    return DEFAULT_PROFILE.copy()


def save_profile(profile: Dict[str, object]) -> None:
    PROFILE_PATH.write_text(json.dumps(profile, indent=2), encoding="utf-8")


def safe_list(value) -> List[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def merge_unique(old_list: List[str], new_items: List[str]) -> List[str]:
    seen = {item.lower(): item for item in old_list}
    for item in new_items:
        if item and item.lower() not in seen:
            seen[item.lower()] = item
    return list(seen.values())


def initialize_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Heyy, I’m glad you’re here! I’m Glow Up Bot 🪞✨ "
                    "I can help with makeup, skincare, hair, fashion, vibe matching, "
                    "and image-based beauty inspo."
                ),
            }
        ]
    if "profile" not in st.session_state:
        st.session_state.profile = load_profile()
    if "draft_input" not in st.session_state:
        st.session_state.draft_input = ""
    if "last_face_analysis" not in st.session_state:
        st.session_state.last_face_analysis = ""
    if "generated_image_b64" not in st.session_state:
        st.session_state.generated_image_b64 = None


initialize_state()


# -----------------------------
# CSS
# -----------------------------
st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(182,123,255,0.16), transparent 30%),
            radial-gradient(circle at top right, rgba(255,120,190,0.14), transparent 28%),
            linear-gradient(180deg, #090816 0%, #160f2c 45%, #130c25 100%);
    }

    .block-container {
        max-width: 1400px;
        padding-top: 1.6rem;
        padding-bottom: 2rem;
    }

    .hero-card {
        background: linear-gradient(135deg, rgba(83,40,122,0.88), rgba(53,25,77,0.90));
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 30px;
        padding: 2rem 2rem 1.4rem 2rem;
        box-shadow: 0 16px 40px rgba(0,0,0,0.28);
        margin-bottom: 1rem;
    }

    .hero-title {
        text-align: center;
        font-size: 3rem;
        font-weight: 800;
        color: #fff7fb;
        margin-bottom: 0.4rem;
    }

    .hero-subtitle {
        text-align: center;
        max-width: 950px;
        margin: 0 auto;
        font-size: 1.12rem;
        line-height: 1.75;
        color: #f8edf8;
    }

    .section-card {
        background: rgba(34, 22, 60, 0.76);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px;
        padding: 1rem 1rem 0.8rem 1rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.18);
        margin-bottom: 1rem;
    }

    .profile-chip-wrap {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin-top: 0.6rem;
    }

    .profile-chip {
        background: linear-gradient(135deg, rgba(170,108,255,0.26), rgba(255,108,170,0.22));
        border: 1px solid rgba(255,255,255,0.10);
        color: #fff3fb;
        border-radius: 999px;
        padding: 0.45rem 0.9rem;
        font-size: 0.95rem;
    }

    .small-muted {
        color: #e8dff2;
        opacity: 0.9;
        font-size: 0.98rem;
        text-align: center;
        margin-top: 0.35rem;
    }

    div.stButton > button {
        width: 100%;
        min-height: 72px;
        border-radius: 22px;
        border: 1px solid rgba(255,255,255,0.10);
        background: linear-gradient(135deg, rgba(173,103,255,0.90), rgba(235,102,167,0.90));
        color: white;
        font-size: 1.04rem;
        font-weight: 700;
        box-shadow: 0 10px 24px rgba(0,0,0,0.18);
    }

    div.stButton > button:hover {
        border: 1px solid rgba(255,255,255,0.16);
        transform: translateY(-1px);
    }

    [data-testid="stChatInput"] {
        border-radius: 22px;
    }

    [data-testid="stChatInput"] > div {
        border-radius: 22px;
        background: rgba(42, 31, 61, 0.92);
        border: 1px solid rgba(255,255,255,0.10);
    }

    [data-testid="stChatMessage"] {
        background: rgba(25, 18, 43, 0.45);
        border-radius: 24px;
        padding: 0.2rem 0.4rem;
    }

    .sidebar-note {
        font-size: 0.95rem;
        color: #f2e9fb;
        line-height: 1.5;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# UI helpers
# -----------------------------
def profile_chip_html(profile: Dict[str, object]) -> str:
    chips = []
    mapping = [
        ("favorite_colors", "Favorite color"),
        ("favorite_styles", "Style"),
        ("best_colors", "Best color"),
        ("undertone", "Undertone"),
        ("skin_tone", "Skin tone"),
        ("face_shape", "Face shape"),
        ("hair_texture", "Hair"),
        ("budget", "Budget"),
    ]
    for key, label in mapping:
        value = profile.get(key, "")
        if isinstance(value, list):
            for item in value[:3]:
                chips.append(f"<span class='profile-chip'>{label}: {item}</span>")
        elif str(value).strip():
            chips.append(f"<span class='profile-chip'>{label}: {value}</span>")
    if not chips:
        chips.append("<span class='profile-chip'>No saved style profile yet</span>")
    return "<div class='profile-chip-wrap'>" + "".join(chips) + "</div>"


def build_profile_summary(profile: Dict[str, object]) -> str:
    parts = []
    for key in ["favorite_colors", "favorite_styles", "best_colors"]:
        values = safe_list(profile.get(key, []))
        if values:
            nice = key.replace("_", " ")
            parts.append(f"{nice}: {', '.join(values)}")
    for key in ["undertone", "skin_tone", "face_shape", "hair_texture", "budget"]:
        value = str(profile.get(key, "")).strip()
        if value:
            parts.append(f"{key.replace('_', ' ')}: {value}")
    return " | ".join(parts) if parts else "No saved profile yet."


def button_prompt_map(profile: Dict[str, object]) -> List[Dict[str, str]]:
    fav_colors = ", ".join(safe_list(profile.get("favorite_colors", []))) or "my favorite colors"
    fav_styles = ", ".join(safe_list(profile.get("favorite_styles", []))) or "my style"
    best_colors = ", ".join(safe_list(profile.get("best_colors", []))) or "the shades that suit me best"

    return [
        {
            "label": "✨ Build My Routine",
            "prompt": "Build me a simple skincare and beauty routine for morning and night.",
        },
        {
            "label": "💄 Makeup Look",
            "prompt": "Create a flattering makeup look for me and explain why it suits my features.",
        },
        {
            "label": "🪮 Hair Ideas",
            "prompt": "Give me hairstyle ideas that match my face shape, vibe, and hair texture.",
        },
        {
            "label": "👗 Style Me",
            "prompt": f"Style me around {fav_styles} and help me build an outfit I would love.",
        },
        {
            "label": "🎨 My Colors",
            "prompt": f"Based on what you know, help me use {fav_colors} and {best_colors} in makeup and outfits.",
        },
        {
            "label": "📸 Analyze My Face",
            "prompt": "I uploaded a face photo. Analyze my face shape, skin tone, and undertone, then suggest makeup ideas.",
        },
        {
            "label": "🛍️ Products For Me",
            "prompt": "Recommend beauty products that fit my features, goals, and budget.",
        },
        {
            "label": "🌟 Save My Vibe",
            "prompt": "Summarize my beauty vibe and save the most useful style preferences for future chats.",
        },
    ]


def image_to_data_url(uploaded_file) -> Optional[str]:
    if uploaded_file is None:
        return None
    mime = uploaded_file.type or "image/jpeg"
    raw = uploaded_file.getvalue()
    encoded = base64.b64encode(raw).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


# -----------------------------
# OpenAI helpers
# -----------------------------
def extract_profile_updates(conversation_text: str, current_profile: Dict[str, object]) -> Dict[str, object]:
    schema_instruction = f"""
Extract only stable beauty/style profile details from the conversation.

Return JSON with these exact keys:
favorite_colors, favorite_styles, best_colors, undertone, skin_tone, face_shape, hair_texture, budget, notes

Rules:
- favorite_colors, favorite_styles, best_colors, notes must be arrays of strings
- other keys must be strings
- if unknown, use empty string or empty list
- do not invent facts
- include only useful beauty/style facts that are likely to matter later

Current profile:
{json.dumps(current_profile, ensure_ascii=False)}
"""
    try:
        response = client.responses.create(
            model="gpt-5",
            input=[
                {"role": "system", "content": schema_instruction},
                {"role": "user", "content": conversation_text},
            ],
            text={"format": {"type": "json_object"}},
        )
        data = json.loads(response.output_text)

        updated = current_profile.copy()
        updated["favorite_colors"] = merge_unique(
            safe_list(current_profile.get("favorite_colors", [])),
            safe_list(data.get("favorite_colors", [])),
        )
        updated["favorite_styles"] = merge_unique(
            safe_list(current_profile.get("favorite_styles", [])),
            safe_list(data.get("favorite_styles", [])),
        )
        updated["best_colors"] = merge_unique(
            safe_list(current_profile.get("best_colors", [])),
            safe_list(data.get("best_colors", [])),
        )
        updated["notes"] = merge_unique(
            safe_list(current_profile.get("notes", [])),
            safe_list(data.get("notes", [])),
        )

        for field in ["undertone", "skin_tone", "face_shape", "hair_texture", "budget"]:
            new_val = str(data.get(field, "")).strip()
            if new_val:
                updated[field] = new_val

        return updated
    except Exception:
        return current_profile


def build_conversation_input(messages: List[Dict[str, str]], profile: Dict[str, object]) -> List[Dict[str, str]]:
    profile_summary = build_profile_summary(profile)
    system = {
        "role": "system",
        "content": SYSTEM_PROMPT + f"\n\nSaved user profile: {profile_summary}",
    }
    convo = [system]
    convo.extend(messages[-18:])
    return convo


def ask_glowup_bot(user_text: str) -> str:
    conversation = build_conversation_input(st.session_state.messages, st.session_state.profile)
    conversation.append({"role": "user", "content": user_text})

    response = client.responses.create(
        model="gpt-5",
        input=conversation,
    )
    return response.output_text


def transcribe_audio(audio_bytes: bytes) -> str:
    import io

    file_obj = io.BytesIO(audio_bytes)
    file_obj.name = "voice_prompt.wav"
    transcript = client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=file_obj,
    )
    return getattr(transcript, "text", "").strip()


def analyze_face_image(image_data_url: str, extra_context: str = "") -> str:
    prompt = f"""
Analyze this face photo for beauty guidance.

Tasks:
1. Estimate likely face shape
2. Estimate visible skin tone
3. Estimate likely undertone if possible
4. Mention uncertainty when relevant
5. Suggest flattering:
   - makeup placement
   - blush placement
   - brow shape direction
   - lip colors
   - highlight/bronzer strategy
   - 3 hairstyle directions

Keep it practical, warm, and beginner-friendly.
If the image is unclear, say what additional photo would help.

Additional user context:
{extra_context}
"""
    response = client.responses.create(
        model="gpt-5",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": image_data_url},
                ],
            }
        ],
    )
    return response.output_text


def generate_inspo_image(prompt: str) -> Optional[bytes]:
    try:
        result = client.images.generate(
            model="gpt-image-1",
            prompt=(
                "Create a polished beauty inspiration image. "
                "Fashion editorial style, flattering lighting, clean composition. "
                + prompt
            ),
            size="1024x1024",
        )
        image_b64 = result.data[0].b64_json
        if image_b64:
            return base64.b64decode(image_b64)
    except Exception:
        return None
    return None


# -----------------------------
# Sidebar profile controls
# -----------------------------
with st.sidebar:
    st.markdown("## Your Glow Profile")
    st.markdown(
        "<div class='sidebar-note'>Save a few details so Glow Up Bot can personalize future answers.</div>",
        unsafe_allow_html=True,
    )

    with st.form("profile_form"):
        name = st.text_input("Name or nickname", value=str(st.session_state.profile.get("name", "")))
        favorite_colors = st.text_input(
            "Favorite colors",
            value=", ".join(safe_list(st.session_state.profile.get("favorite_colors", []))),
            placeholder="pink, plum, chocolate brown",
        )
        favorite_styles = st.text_input(
            "Favorite styles",
            value=", ".join(safe_list(st.session_state.profile.get("favorite_styles", []))),
            placeholder="soft glam, streetwear, classy, natural",
        )
        best_colors = st.text_input(
            "Best colors on you",
            value=", ".join(safe_list(st.session_state.profile.get("best_colors", []))),
            placeholder="wine red, gold, emerald",
        )
        undertone = st.text_input("Undertone", value=str(st.session_state.profile.get("undertone", "")))
        skin_tone = st.text_input("Skin tone", value=str(st.session_state.profile.get("skin_tone", "")))
        face_shape = st.text_input("Face shape", value=str(st.session_state.profile.get("face_shape", "")))
        hair_texture = st.text_input("Hair texture", value=str(st.session_state.profile.get("hair_texture", "")))
        budget = st.selectbox(
            "Budget",
            ["", "Affordable", "Mid-range", "Luxury", "Mixed"],
            index=["", "Affordable", "Mid-range", "Luxury", "Mixed"].index(
                str(st.session_state.profile.get("budget", "")) if str(st.session_state.profile.get("budget", "")) in ["", "Affordable", "Mid-range", "Luxury", "Mixed"] else ""
            ),
        )

        save_clicked = st.form_submit_button("Save profile")

    if save_clicked:
        st.session_state.profile["name"] = name.strip()
        st.session_state.profile["favorite_colors"] = [x.strip() for x in favorite_colors.split(",") if x.strip()]
        st.session_state.profile["favorite_styles"] = [x.strip() for x in favorite_styles.split(",") if x.strip()]
        st.session_state.profile["best_colors"] = [x.strip() for x in best_colors.split(",") if x.strip()]
        st.session_state.profile["undertone"] = undertone.strip()
        st.session_state.profile["skin_tone"] = skin_tone.strip()
        st.session_state.profile["face_shape"] = face_shape.strip()
        st.session_state.profile["hair_texture"] = hair_texture.strip()
        st.session_state.profile["budget"] = budget.strip()
        save_profile(st.session_state.profile)
        st.success("Profile saved.")

    if st.button("Clear saved profile", use_container_width=True):
        st.session_state.profile = DEFAULT_PROFILE.copy()
        save_profile(st.session_state.profile)
        st.success("Saved preferences cleared.")


# -----------------------------
# Main header
# -----------------------------
st.markdown(
    """
    <div class="hero-card">
        <div class="hero-title">Glow Up Bot 🪞</div>
        <div class="hero-subtitle">
            I’m your beauty and style bestie for skincare, makeup, hair, outfit vibes,
            inspiration images, voice chat, and face-photo based suggestions.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="section-card">
        <div class="small-muted"><strong>Saved beauty profile</strong></div>
        {profile_chip_html(st.session_state.profile)}
        <div class="small-muted">Tap a quick action or type your own question below.</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Quick action buttons
# -----------------------------
quick_actions = button_prompt_map(st.session_state.profile)
button_cols = st.columns(4, gap="large")

for idx, action in enumerate(quick_actions):
    with button_cols[idx % 4]:
        if st.button(action["label"], key=f"action_{idx}", use_container_width=True):
            st.session_state.draft_input = action["prompt"]


# -----------------------------
# Voice and photo tools
# -----------------------------
tool_col1, tool_col2 = st.columns([1, 1], gap="large")

with tool_col1:
    st.markdown("### 🎙️ Voice input")
    voice_audio = st.audio_input("Record your beauty question", key="voice_prompt")
    if voice_audio is not None:
        if st.button("Use voice question", key="transcribe_btn", use_container_width=True):
            with st.spinner("Transcribing your voice note..."):
                try:
                    transcript = transcribe_audio(voice_audio.getvalue())
                    if transcript:
                        st.session_state.draft_input = transcript
                        st.success(f"Added to chat input: {transcript}")
                    else:
                        st.warning("I couldn't hear enough audio to transcribe.")
                except Exception as exc:
                    st.error(f"Audio transcription failed: {exc}")

with tool_col2:
    st.markdown("### 📸 Face photo analysis")
    face_photo = st.camera_input("Take a clear front-facing photo", key="face_photo")
    photo_note = st.text_input(
        "Optional photo context",
        placeholder="prom makeup, natural glam, bold lips, beginner friendly...",
        key="photo_context"
    )
    if face_photo is not None and st.button("Analyze my photo", key="analyze_face", use_container_width=True):
        with st.spinner("Analyzing your features and building suggestions..."):
            try:
                image_data_url = image_to_data_url(face_photo)
                analysis = analyze_face_image(image_data_url, photo_note)
                st.session_state.last_face_analysis = analysis
                st.session_state.messages.append(
                    {"role": "assistant", "content": "Photo analysis complete:\n\n" + analysis}
                )

                profile_after = extract_profile_updates(
                    "Face analysis result:\n" + analysis,
                    st.session_state.profile,
                )
                st.session_state.profile = profile_after
                save_profile(profile_after)
                st.rerun()
            except Exception as exc:
                st.error(f"Photo analysis failed: {exc}")


# -----------------------------
# Chat history
# -----------------------------
for message in st.session_state.messages:
    avatar = "🪞" if message["role"] == "assistant" else "✨"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])


# -----------------------------
# Chat input
# -----------------------------
typed_prompt = st.chat_input("What’s up? Ask me about skincare, beauty, fashion, hair, or your photo.")
final_prompt = typed_prompt or st.session_state.draft_input

if final_prompt:
    st.session_state.draft_input = ""

    st.session_state.messages.append({"role": "user", "content": final_prompt})
    with st.chat_message("user", avatar="✨"):
        st.markdown(final_prompt)

    with st.chat_message("assistant", avatar="🪞"):
        with st.spinner("Glow Up Bot is thinking..."):
            try:
                reply = ask_glowup_bot(final_prompt)
            except Exception as exc:
                reply = f"Okayy, tiny hiccup on my end. Try that one more time. Error: {exc}"

        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    combined_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-8:]])
    updated_profile = extract_profile_updates(combined_text, st.session_state.profile)
    st.session_state.profile = updated_profile
    save_profile(updated_profile)


# -----------------------------
# Inspiration image generator
# -----------------------------
st.markdown("### 🖼️ Generate beauty inspiration")
image_prompt = st.text_input(
    "Describe the inspo image you want",
    placeholder="soft glam prom look for deep skin with rose gold shimmer and plum lip",
)

if st.button("Generate inspo image", use_container_width=True):
    if not image_prompt.strip():
        st.warning("Add a prompt first so I know what to generate.")
    else:
        with st.spinner("Creating your inspo image..."):
            img_bytes = generate_inspo_image(image_prompt.strip())
            if img_bytes:
                st.session_state.generated_image_b64 = base64.b64encode(img_bytes).decode("utf-8")
            else:
                st.error("Image generation failed. Try a shorter prompt.")

if st.session_state.generated_image_b64:
    st.image(base64.b64decode(st.session_state.generated_image_b64), caption="Glow Up inspo image", use_container_width=True)


# -----------------------------
# Footer guidance
# -----------------------------
with st.expander("Recommended repo files for deployment"):
    st.code(
        "OpenAPI/\n"
        "├── app.py\n"
        "├── requirements.txt\n"
        "├── .streamlit/\n"
        "│   └── secrets.toml   # for local dev you can keep OPENAI_API_KEY in .env instead\n"
        "└── data/\n"
        "    └── glowup_profile.json",
        language="text",
    )
'''

requirements = """streamlit>=1.50.0
openai>=1.99.0
python-dotenv>=1.0.1
"""

deploy_notes = """# Deploy notes

1. Push `app.py` and `requirements.txt` to GitHub.
2. In Streamlit Community Cloud, choose your repo and set the main file path to `OpenAPI/app.py`.
3. Add `OPENAI_API_KEY` in the app's Secrets settings.
4. Deploy and Streamlit will create a public `*.streamlit.app` link.
"""

Path("/mnt/data/glowup_app.py").write_text(app_code, encoding="utf-8")
Path("/mnt/data/requirements.txt").write_text(requirements, encoding="utf-8")
Path("/mnt/data/deploy_notes.txt").write_text(deploy_notes, encoding="utf-8")

print("Created files:")
print("/mnt/data/glowup_app.py")
print("/mnt/data/requirements.txt")
print("/mnt/data/deploy_notes.txt")