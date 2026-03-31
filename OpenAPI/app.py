import base64
import io
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# -----------------------------
# Setup
# -----------------------------
load_dotenv()

st.set_page_config(
    page_title="Glow Up Bot",
    page_icon="🪞",
    layout="wide",
)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OPENAI_API_KEY is missing. Add it to your .env file first.")
    st.stop()

client = OpenAI(api_key=api_key)

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

PROFILE_PATH = DATA_DIR / "profile.json"
OUTFITS_PATH = DATA_DIR / "saved_outfits.json"

SYSTEM_PROMPT = """
You are Glow Up Bot, a warm, stylish, inclusive beauty and fashion assistant.

You help with:
- makeup looks
- hairstyles
- skincare basics
- outfit styling
- undertone-aware color choices
- face-shape-aware suggestions
- beauty inspiration images

Style:
- upbeat but clear
- supportive and specific
- can say things like "Yess" or "Okayy" occasionally
- not too slang-heavy

Rules:
- stay focused on beauty, style, skincare, makeup, hair, and outfits
- when analyzing a face photo, be careful and say when something is only an estimate
- explain WHY a recommendation fits the user
- keep answers practical
"""

DEFAULT_PROFILE = {
    "name": "",
    "favorite_colors": [],
    "favorite_styles": [],
    "best_colors": [],
    "skin_tone": "",
    "undertone": "",
    "face_shape": "",
    "hair_texture": "",
    "budget": "",
    "notes": [],
}

DEFAULT_OUTFIT_GAME = {
    "occasion": "",
    "vibe": "",
    "top": "",
    "bottom": "",
    "dress": "",
    "outerwear": "",
    "shoes": "",
    "bag": "",
    "accessories": "",
    "colors": "",
    "notes": "",
}

# -----------------------------
# Persistence helpers
# -----------------------------
def load_json(path: Path, fallback: Any) -> Any:
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return fallback
    return fallback


def save_json(path: Path, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def safe_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def merge_unique(old_items: List[str], new_items: List[str]) -> List[str]:
    seen = {item.lower(): item for item in old_items}
    for item in new_items:
        clean = str(item).strip()
        if clean and clean.lower() not in seen:
            seen[clean.lower()] = clean
    return list(seen.values())


# -----------------------------
# Session state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Heyy, I’m Glow Up Bot 🪞✨\n\n"
                "I can help with outfits, makeup, skincare, hair, voice questions, "
                "face-photo analysis, and beauty inspo images."
            ),
        }
    ]

if "profile" not in st.session_state:
    saved_profile = load_json(PROFILE_PATH, DEFAULT_PROFILE.copy())
    merged = DEFAULT_PROFILE.copy()
    merged.update(saved_profile)
    st.session_state.profile = merged

if "saved_outfits" not in st.session_state:
    st.session_state.saved_outfits = load_json(OUTFITS_PATH, [])

if "outfit_game" not in st.session_state:
    st.session_state.outfit_game = DEFAULT_OUTFIT_GAME.copy()

if "draft_prompt" not in st.session_state:
    st.session_state.draft_prompt = ""

if "last_face_analysis" not in st.session_state:
    st.session_state.last_face_analysis = ""

if "generated_image_bytes" not in st.session_state:
    st.session_state.generated_image_bytes = None

# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(178,109,255,0.14), transparent 28%),
            radial-gradient(circle at top right, rgba(240,107,179,0.12), transparent 28%),
            linear-gradient(180deg, #090816 0%, #160f2c 52%, #120a22 100%);
    }

    .block-container {
        max-width: 1400px;
        padding-top: 1.4rem;
        padding-bottom: 2rem;
    }

    .hero-card {
        background: linear-gradient(135deg, rgba(82,40,119,0.90), rgba(50,24,74,0.92));
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 28px;
        padding: 2rem;
        box-shadow: 0 18px 42px rgba(0,0,0,0.25);
        margin-bottom: 1rem;
    }

    .hero-title {
        text-align: center;
        font-size: 3rem;
        font-weight: 800;
        color: #fff7fb;
        margin-bottom: 0.5rem;
    }

    .hero-sub {
        text-align: center;
        color: #f8edf8;
        max-width: 980px;
        margin: 0 auto;
        font-size: 1.08rem;
        line-height: 1.7;
    }

    .soft-card {
        background: rgba(31, 21, 54, 0.78);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 10px 24px rgba(0,0,0,0.18);
    }

    .chip {
        display: inline-block;
        margin: 0.25rem 0.3rem 0 0;
        padding: 0.4rem 0.8rem;
        border-radius: 999px;
        background: linear-gradient(135deg, rgba(173,103,255,0.24), rgba(235,102,167,0.20));
        border: 1px solid rgba(255,255,255,0.10);
        color: #fff3fb;
        font-size: 0.92rem;
    }

    div.stButton > button {
        width: 100%;
        min-height: 68px;
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.10);
        background: linear-gradient(135deg, rgba(173,103,255,0.92), rgba(235,102,167,0.90));
        color: white;
        font-weight: 700;
    }

    [data-testid="stChatInput"] > div {
        border-radius: 22px;
        background: rgba(42,31,61,0.94);
        border: 1px solid rgba(255,255,255,0.10);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Utility helpers
# -----------------------------
def profile_summary(profile: Dict[str, Any]) -> str:
    parts = []
    for key in ["favorite_colors", "favorite_styles", "best_colors"]:
        values = safe_list(profile.get(key, []))
        if values:
            parts.append(f"{key.replace('_', ' ')}: {', '.join(values)}")
    for key in ["skin_tone", "undertone", "face_shape", "hair_texture", "budget"]:
        val = str(profile.get(key, "")).strip()
        if val:
            parts.append(f"{key.replace('_', ' ')}: {val}")
    note_values = safe_list(profile.get("notes", []))
    if note_values:
        parts.append(f"notes: {', '.join(note_values[:5])}")
    return " | ".join(parts) if parts else "No saved profile yet."


def profile_chips(profile: Dict[str, Any]) -> str:
    chips = []
    for color in safe_list(profile.get("favorite_colors", []))[:3]:
        chips.append(f"<span class='chip'>Favorite color: {color}</span>")
    for style in safe_list(profile.get("favorite_styles", []))[:3]:
        chips.append(f"<span class='chip'>Style: {style}</span>")
    if profile.get("undertone"):
        chips.append(f"<span class='chip'>Undertone: {profile['undertone']}</span>")
    if profile.get("face_shape"):
        chips.append(f"<span class='chip'>Face shape: {profile['face_shape']}</span>")
    if profile.get("skin_tone"):
        chips.append(f"<span class='chip'>Skin tone: {profile['skin_tone']}</span>")
    if profile.get("hair_texture"):
        chips.append(f"<span class='chip'>Hair: {profile['hair_texture']}</span>")
    if not chips:
        chips.append("<span class='chip'>No saved preferences yet</span>")
    return "".join(chips)


def to_data_url(file_bytes: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(file_bytes).decode('utf-8')}"


def quick_actions(profile: Dict[str, Any]) -> List[Dict[str, str]]:
    fave_styles = ", ".join(safe_list(profile.get("favorite_styles", []))) or "my style"
    fave_colors = ", ".join(safe_list(profile.get("favorite_colors", []))) or "my colors"
    return [
        {"label": "💄 Makeup Look", "prompt": "Create a flattering makeup look for me and explain why it fits me."},
        {"label": "🪮 Hair Ideas", "prompt": "Give me hairstyle ideas that match my face shape and vibe."},
        {"label": "👗 Style Me", "prompt": f"Style me around {fave_styles} and give me a full outfit idea."},
        {"label": "🎨 My Colors", "prompt": f"Help me use {fave_colors} in makeup and outfits."},
        {"label": "🧴 Routine", "prompt": "Build me a simple morning and night beauty routine."},
        {"label": "🛍️ Products", "prompt": "Recommend beauty products that fit my features and budget."},
        {"label": "📸 Analyze My Face", "prompt": "Use my face photo to estimate face shape, undertone, and flattering makeup placement."},
        {"label": "🖼️ Outfit Image", "prompt": "Generate an outfit inspo image based on my saved style and colors."},
    ]


# -----------------------------
# OpenAI helpers
# -----------------------------
def extract_profile_updates(conversation_text: str, current_profile: Dict[str, Any]) -> Dict[str, Any]:
    schema = {
        "type": "object",
        "properties": {
            "favorite_colors": {"type": "array", "items": {"type": "string"}},
            "favorite_styles": {"type": "array", "items": {"type": "string"}},
            "best_colors": {"type": "array", "items": {"type": "string"}},
            "skin_tone": {"type": "string"},
            "undertone": {"type": "string"},
            "face_shape": {"type": "string"},
            "hair_texture": {"type": "string"},
            "budget": {"type": "string"},
            "notes": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "favorite_colors",
            "favorite_styles",
            "best_colors",
            "skin_tone",
            "undertone",
            "face_shape",
            "hair_texture",
            "budget",
            "notes",
        ],
        "additionalProperties": False,
    }

    try:
        response = client.responses.create(
            model="gpt-5",
            input=[
                {
                    "role": "system",
                    "content": (
                        "Extract only stable beauty/style preferences from the text. "
                        "Do not invent facts. Return empty strings/lists when unknown."
                    ),
                },
                {"role": "user", "content": conversation_text},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "profile_update",
                    "schema": schema,
                    "strict": True,
                }
            },
        )

        data = json.loads(response.output_text)

        updated = current_profile.copy()
        updated["favorite_colors"] = merge_unique(
            safe_list(updated.get("favorite_colors", [])),
            safe_list(data.get("favorite_colors", [])),
        )
        updated["favorite_styles"] = merge_unique(
            safe_list(updated.get("favorite_styles", [])),
            safe_list(data.get("favorite_styles", [])),
        )
        updated["best_colors"] = merge_unique(
            safe_list(updated.get("best_colors", [])),
            safe_list(data.get("best_colors", [])),
        )
        updated["notes"] = merge_unique(
            safe_list(updated.get("notes", [])),
            safe_list(data.get("notes", [])),
        )

        for key in ["skin_tone", "undertone", "face_shape", "hair_texture", "budget"]:
            val = str(data.get(key, "")).strip()
            if val:
                updated[key] = val

        save_json(PROFILE_PATH, updated)
        return updated
    except Exception:
        return current_profile


def build_model_messages(user_text: str) -> List[Dict[str, Any]]:
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT + "\n\nSaved profile: " + profile_summary(st.session_state.profile),
        }
    ]
    messages.extend(st.session_state.messages[-12:])
    messages.append({"role": "user", "content": user_text})
    return messages


def ask_glowup_bot(user_text: str) -> str:
    response = client.responses.create(
        model="gpt-5",
        input=build_model_messages(user_text),
        truncation="auto",
    )
    return response.output_text


def transcribe_audio(audio_bytes: bytes) -> str:
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "voice_question.wav"
    transcript = client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=audio_file,
    )
    return getattr(transcript, "text", "").strip()


def analyze_face_photo(image_bytes: bytes, mime: str, extra_context: str = "") -> str:
    data_url = to_data_url(image_bytes, mime)
    prompt = f"""
Analyze this selfie for beauty guidance.

Please:
- estimate likely face shape
- estimate visible skin tone
- estimate likely undertone if possible
- mention uncertainty clearly when needed
- suggest flattering blush placement
- suggest contour/bronzer strategy
- suggest lip shades
- suggest brow direction
- suggest 3 hairstyle directions
- suggest 1 makeup look that would flatter the face

Keep it supportive and beginner-friendly.

Extra context from the user:
{extra_context}
"""
    response = client.responses.create(
        model="gpt-5",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": data_url, "detail": "high"},
                ],
            }
        ],
        truncation="auto",
    )
    return response.output_text


def generate_outfit_image(prompt: str) -> Optional[bytes]:
    """
    Uses Responses API with the built-in image_generation tool.
    Depending on SDK version, the image payload may appear in slightly different places.
    """
    response = client.responses.create(
        model="gpt-5",
        input=prompt,
        tools=[{"type": "image_generation"}],
        tool_choice={"type": "image_generation"},
    )

    # Try a few common result shapes
    if hasattr(response, "output"):
        for item in response.output:
            item_type = getattr(item, "type", "")
            if item_type == "image_generation_call":
                result = getattr(item, "result", None)
                if isinstance(result, str):
                    try:
                        return base64.b64decode(result)
                    except Exception:
                        pass

                if isinstance(result, list):
                    for piece in result:
                        b64_data = getattr(piece, "b64_json", None) or getattr(piece, "image_base64", None)
                        if b64_data:
                            return base64.b64decode(b64_data)

            if hasattr(item, "result"):
                result = getattr(item, "result")
                if isinstance(result, str):
                    try:
                        return base64.b64decode(result)
                    except Exception:
                        pass

    return None


def outfit_feedback_prompt(game: Dict[str, str], profile: Dict[str, Any]) -> str:
    return f"""
We are building an outfit together.

Saved user profile:
{profile_summary(profile)}

Current outfit draft:
- Occasion: {game.get('occasion', '')}
- Vibe: {game.get('vibe', '')}
- Top: {game.get('top', '')}
- Bottom: {game.get('bottom', '')}
- Dress: {game.get('dress', '')}
- Outerwear: {game.get('outerwear', '')}
- Shoes: {game.get('shoes', '')}
- Bag: {game.get('bag', '')}
- Accessories: {game.get('accessories', '')}
- Colors: {game.get('colors', '')}
- Notes: {game.get('notes', '')}

Please:
1. Say what works
2. Point out what clashes or feels incomplete
3. Suggest improvements
4. End with a short section called "Final Outfit Check"
"""


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("## Save your beauty profile")

    with st.form("profile_form"):
        name = st.text_input("Name", value=st.session_state.profile.get("name", ""))
        favorite_colors = st.text_input(
            "Favorite colors",
            value=", ".join(safe_list(st.session_state.profile.get("favorite_colors", []))),
            placeholder="plum, pink, brown, emerald",
        )
        favorite_styles = st.text_input(
            "Favorite styles",
            value=", ".join(safe_list(st.session_state.profile.get("favorite_styles", []))),
            placeholder="soft glam, classy, streetwear",
        )
        best_colors = st.text_input(
            "Best colors on you",
            value=", ".join(safe_list(st.session_state.profile.get("best_colors", []))),
            placeholder="gold, wine, cream",
        )
        hair_texture = st.text_input("Hair texture", value=st.session_state.profile.get("hair_texture", ""))
        budget = st.selectbox(
            "Budget",
            ["", "Affordable", "Mid-range", "Luxury", "Mixed"],
            index=["", "Affordable", "Mid-range", "Luxury", "Mixed"].index(
                st.session_state.profile.get("budget", "")
                if st.session_state.profile.get("budget", "") in ["", "Affordable", "Mid-range", "Luxury", "Mixed"]
                else ""
            ),
        )

        saved = st.form_submit_button("Save preferences")

    if saved:
        st.session_state.profile["name"] = name.strip()
        st.session_state.profile["favorite_colors"] = [x.strip() for x in favorite_colors.split(",") if x.strip()]
        st.session_state.profile["favorite_styles"] = [x.strip() for x in favorite_styles.split(",") if x.strip()]
        st.session_state.profile["best_colors"] = [x.strip() for x in best_colors.split(",") if x.strip()]
        st.session_state.profile["hair_texture"] = hair_texture.strip()
        st.session_state.profile["budget"] = budget.strip()
        save_json(PROFILE_PATH, st.session_state.profile)
        st.success("Preferences saved.")

    if st.button("Clear saved profile", use_container_width=True):
        st.session_state.profile = DEFAULT_PROFILE.copy()
        save_json(PROFILE_PATH, st.session_state.profile)
        st.success("Profile cleared.")


# -----------------------------
# Header
# -----------------------------
st.markdown(
    """
    <div class="hero-card">
        <div class="hero-title">Glow Up Bot 🪞</div>
        <div class="hero-sub">
            Beauty chat + outfit builder + saved preferences + voice input + face scan + outfit image generation.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="soft-card">
        <strong>Saved profile</strong><br/>
        {profile_chips(st.session_state.profile)}
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Quick actions
# -----------------------------
st.markdown("### Quick actions")
action_cols = st.columns(4, gap="large")
for i, action in enumerate(quick_actions(st.session_state.profile)):
    with action_cols[i % 4]:
        if st.button(action["label"], key=f"quick_{i}", use_container_width=True):
            st.session_state.draft_prompt = action["prompt"]

# -----------------------------
# Voice + face scan
# -----------------------------
tool_col1, tool_col2 = st.columns(2, gap="large")

with tool_col1:
    st.markdown("### 🎙️ Voice input")
    voice_audio = st.audio_input("Record a beauty or outfit question")
    if voice_audio is not None:
        if st.button("Use voice message", key="use_voice_btn", use_container_width=True):
            try:
                transcript = transcribe_audio(voice_audio.getvalue())
                if transcript:
                    st.session_state.draft_prompt = transcript
                    st.success(f"Added to chat: {transcript}")
                else:
                    st.warning("I couldn’t hear enough to transcribe that.")
            except Exception as e:
                st.error(f"Voice transcription failed: {e}")

with tool_col2:
    st.markdown("### 📸 Face scan")
    selfie = st.camera_input("Take a clear front-facing photo")
    face_context = st.text_input(
        "Optional face-scan goal",
        placeholder="soft glam, prom, no-makeup makeup, bold lip...",
    )
    if selfie is not None and st.button("Analyze my face", key="analyze_face_btn", use_container_width=True):
        try:
            analysis = analyze_face_photo(selfie.getvalue(), selfie.type or "image/jpeg", face_context)
            st.session_state.last_face_analysis = analysis
            st.session_state.messages.append({"role": "assistant", "content": "Photo analysis:\n\n" + analysis})
            st.session_state.profile = extract_profile_updates(analysis, st.session_state.profile)
            st.success("Face analysis added to chat and memory.")
            st.rerun()
        except Exception as e:
            st.error(f"Face analysis failed: {e}")

# -----------------------------
# Outfit builder
# -----------------------------
st.markdown("### 🎮 Build an outfit with me")
left, right = st.columns([1.25, 1], gap="large")
g = st.session_state.outfit_game

with left:
    r1 = st.columns(2)
    with r1[0]:
        g["occasion"] = st.text_input("Occasion", value=g["occasion"], placeholder="birthday dinner, class, brunch")
    with r1[1]:
        g["vibe"] = st.text_input("Vibe", value=g["vibe"], placeholder="soft glam, classy, edgy, cozy")

    r2 = st.columns(3)
    with r2[0]:
        g["top"] = st.text_input("Top", value=g["top"], placeholder="corset top, fitted tee")
    with r2[1]:
        g["bottom"] = st.text_input("Bottom", value=g["bottom"], placeholder="wide-leg jeans, satin skirt")
    with r2[2]:
        g["dress"] = st.text_input("Dress option", value=g["dress"], placeholder="slip dress, midi dress")

    r3 = st.columns(3)
    with r3[0]:
        g["outerwear"] = st.text_input("Outerwear", value=g["outerwear"], placeholder="cropped blazer")
    with r3[1]:
        g["shoes"] = st.text_input("Shoes", value=g["shoes"], placeholder="heels, sneakers, boots")
    with r3[2]:
        g["bag"] = st.text_input("Bag", value=g["bag"], placeholder="mini bag, tote, clutch")

    r4 = st.columns(2)
    with r4[0]:
        g["accessories"] = st.text_input("Accessories", value=g["accessories"], placeholder="gold hoops, layered chains")
    with r4[1]:
        g["colors"] = st.text_input("Colors", value=g["colors"], placeholder="plum, black, cream")

    g["notes"] = st.text_area("Extra notes", value=g["notes"], placeholder="modest, comfy, budget-friendly")

    btns = st.columns(3)
    with btns[0]:
        if st.button("Get styling feedback", key="style_feedback_btn", use_container_width=True):
            st.session_state.draft_prompt = outfit_feedback_prompt(g, st.session_state.profile)

    with btns[1]:
        if st.button("Save outfit", key="save_outfit_btn", use_container_width=True):
            summary = {
                "name": f"{(g.get('occasion') or 'Saved')} look",
                "details": g.copy(),
            }
            st.session_state.saved_outfits.insert(0, summary)
            save_json(OUTFITS_PATH, st.session_state.saved_outfits)
            st.success("Outfit saved.")

    with btns[2]:
        if st.button("Generate outfit image", key="generate_outfit_image_btn", use_container_width=True):
            image_prompt = f"""
Create a polished outfit inspiration image based on this outfit:

Occasion: {g.get('occasion', '')}
Vibe: {g.get('vibe', '')}
Top: {g.get('top', '')}
Bottom: {g.get('bottom', '')}
Dress: {g.get('dress', '')}
Outerwear: {g.get('outerwear', '')}
Shoes: {g.get('shoes', '')}
Bag: {g.get('bag', '')}
Accessories: {g.get('accessories', '')}
Colors: {g.get('colors', '')}
Notes: {g.get('notes', '')}

Saved user profile:
{profile_summary(st.session_state.profile)}

Make it stylish, cohesive, modern, and fashion-editorial.
"""
            try:
                image_bytes = generate_outfit_image(image_prompt)
                if image_bytes:
                    st.session_state.generated_image_bytes = image_bytes
                    st.success("Outfit image generated.")
                else:
                    st.warning("The image tool ran, but no image payload came back. Update your OpenAI package if needed.")
            except Exception as e:
                st.error(f"Image generation failed: {e}")

with right:
    st.markdown("#### Saved outfits")
    if st.session_state.saved_outfits:
        for idx, outfit in enumerate(st.session_state.saved_outfits[:8]):
            with st.expander(outfit.get("name", f"Outfit {idx+1}")):
                details = outfit.get("details", {})
                for key, value in details.items():
                    if value:
                        st.write(f"**{key.title()}**: {value}")

                row = st.columns(2)
                with row[0]:
                    if st.button("Use in chat", key=f"use_saved_{idx}", use_container_width=True):
                        st.session_state.draft_prompt = (
                            "Help me improve this saved outfit and add makeup + hair suggestions:\n\n"
                            + json.dumps(details, indent=2)
                        )
                with row[1]:
                    if st.button("Delete", key=f"delete_saved_{idx}", use_container_width=True):
                        st.session_state.saved_outfits.pop(idx)
                        save_json(OUTFITS_PATH, st.session_state.saved_outfits)
                        st.rerun()
    else:
        st.info("No saved outfits yet.")

if st.session_state.generated_image_bytes:
    st.markdown("### 🖼️ Generated outfit image")
    st.image(st.session_state.generated_image_bytes, use_container_width=True)

# -----------------------------
# Chat history
# -----------------------------
st.markdown("### 💬 Chat")
for msg in st.session_state.messages:
    avatar = "🪞" if msg["role"] == "assistant" else "✨"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# -----------------------------
# Chat input
# -----------------------------
typed_input = st.chat_input("Ask me about beauty, fashion, colors, makeup, skincare, or your outfit...")
final_prompt = typed_input or st.session_state.draft_prompt

if final_prompt:
    st.session_state.draft_prompt = ""

    st.session_state.messages.append({"role": "user", "content": final_prompt})

    with st.chat_message("user", avatar="✨"):
        st.markdown(final_prompt)

    with st.chat_message("assistant", avatar="🪞"):
        with st.spinner("Glow Up Bot is thinking..."):
            try:
                reply = ask_glowup_bot(final_prompt)
            except Exception as e:
                reply = f"Okayy, tiny hiccup on my end. Try that again. Error: {e}"
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    recent_text = "\n".join(f"{m['role']}: {m['content']}" for m in st.session_state.messages[-8:])
    st.session_state.profile = extract_profile_updates(recent_text, st.session_state.profile)