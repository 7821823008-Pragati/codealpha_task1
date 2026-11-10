"""
LinguaBridge - Multi-Format Language Translator
------------------------------------------------
Streamlit app with 4 modules:
  1. Text Translation
  2. Image OCR + Translate
  3. Document Parser (txt / pdf / docx) + Download
  4. Audio Pronunciation (gTTS)

Run:
    pip install streamlit deep-translator gTTS Pillow pytesseract PyPDF2 python-docx
    streamlit run app.py

Optional: install the Tesseract OCR binary for image text extraction.
Every optional dependency is wrapped so the app never crashes if one is missing.
"""

import io
import os
import tempfile
import traceback

import streamlit as st

# --------------------------------------------------------------------------
# Page config (must be the first Streamlit command)
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="LinguaBridge | Language Translator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# Optional dependency detection (graceful degradation)
# --------------------------------------------------------------------------
try:
    from deep_translator import GoogleTranslator

    HAS_TRANSLATOR = True
except Exception:
    GoogleTranslator = None
    HAS_TRANSLATOR = False

try:
    from PIL import Image, ImageOps

    HAS_PIL = True
except Exception:
    Image = None
    ImageOps = None
    HAS_PIL = False

try:
    import pytesseract

    HAS_PYTESSERACT = True
except Exception:
    pytesseract = None
    HAS_PYTESSERACT = False

try:
    from PyPDF2 import PdfReader

    HAS_PDF = True
except Exception:
    try:
        from pypdf import PdfReader  # modern successor to PyPDF2

        HAS_PDF = True
    except Exception:
        PdfReader = None
        HAS_PDF = False

try:
    import docx  # python-docx

    HAS_DOCX = True
except Exception:
    docx = None
    HAS_DOCX = False

try:
    from gtts import gTTS

    HAS_GTTS = True
except Exception:
    gTTS = None
    HAS_GTTS = False

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------
LANGUAGES = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Hindi": "hi",
    "Marathi": "mr",
    "Japanese": "ja",
    "Arabic": "ar",
    "Chinese (Simplified)": "zh-CN",
    "Portuguese": "pt",
    "Russian": "ru",
    "Italian": "it",
    "Korean": "ko",
    "Bengali": "bn",
    "Tamil": "ta",
    "Telugu": "te",
    "Gujarati": "gu",
    "Urdu": "ur",
    "Turkish": "tr",
    "Dutch": "nl",
}
AUTO = "Auto-detect"

# Tesseract language packs (only work if installed on the machine)
OCR_LANGS = {
    "English": "eng",
    "Hindi": "hin",
    "Marathi": "mar",
    "Spanish": "spa",
    "French": "fra",
    "German": "deu",
    "Japanese": "jpn",
    "Arabic": "ara",
}

MAX_CHUNK = 4500  # Google Translate free endpoint limit is ~5000 chars

# Tiny offline phrasebook used only for the mock fallback
MOCK_PHRASES = {
    "hello": {"es": "hola", "fr": "bonjour", "de": "hallo", "hi": "नमस्ते",
              "mr": "नमस्कार", "ja": "こんにちは", "ar": "مرحبا"},
    "thank you": {"es": "gracias", "fr": "merci", "de": "danke", "hi": "धन्यवाद",
                  "mr": "धन्यवाद", "ja": "ありがとう", "ar": "شكرا"},
    "good morning": {"es": "buenos días", "fr": "bonjour", "de": "guten Morgen",
                     "hi": "सुप्रभात", "mr": "शुभ प्रभात", "ja": "おはようございます",
                     "ar": "صباح الخير"},
}

# --------------------------------------------------------------------------
# Custom CSS (Blue & White theme)
# --------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
:root {
    --navy: #1E3A8A;
    --royal: #2563EB;
    --white: #FFFFFF;
    --slate: #F8FAFC;
    --border: #E2E8F0;
}

.stApp { background-color: var(--slate); }

/* Hero header */
.hero {
    background: linear-gradient(135deg, var(--navy) 0%, var(--royal) 100%);
    color: var(--white);
    padding: 28px 32px;
    border-radius: 12px;
    box-shadow: 0 6px 18px rgba(30, 58, 138, 0.25);
    margin-bottom: 22px;
}
.hero h1 { color: var(--white) !important; margin: 0; font-size: 2rem; }
.hero p { color: #DBEAFE; margin: 6px 0 0 0; font-size: 1rem; }

/* Headings */
h1, h2, h3, h4 { color: var(--navy); }

/* Cards */
.card {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 18px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
    margin-bottom: 12px;
}
.card-title {
    color: var(--navy);
    font-weight: 700;
    font-size: 1.05rem;
    margin-bottom: 2px;
}

/* Buttons */
.stButton > button, .stDownloadButton > button {
    background-color: var(--royal);
    color: var(--white);
    border: none;
    border-radius: 8px;
    padding: 0.55rem 1.4rem;
    font-weight: 600;
    box-shadow: 0 2px 6px rgba(37, 99, 235, 0.35);
    transition: all 0.15s ease-in-out;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    background-color: var(--navy);
    color: var(--white);
    box-shadow: 0 4px 12px rgba(30, 58, 138, 0.4);
    transform: translateY(-1px);
}
.stButton > button:focus, .stDownloadButton > button:focus {
    color: var(--white);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.35);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: var(--white);
    padding: 6px;
    border-radius: 12px;
    border: 1px solid var(--border);
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 18px;
    color: var(--navy);
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background-color: var(--royal) !important;
    color: var(--white) !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: var(--white);
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: var(--navy); }
.side-card {
    background: var(--slate);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 14px;
    margin-top: 10px;
    font-size: 0.88rem;
    color: #334155;
}

/* Inputs */
.stTextArea textarea, .stTextInput input {
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
    background-color: var(--white) !important;
    color: #000000 !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--royal) !important;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important;
}
div[data-baseweb="select"] > div {
    border-radius: 8px !important;
    border-color: var(--border) !important;
}
[data-testid="stFileUploader"] section {
    border: 2px dashed #93C5FD;
    border-radius: 12px;
    background: var(--white);
    color: #000000 !important;
}

.badge-ok, .badge-miss {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    margin: 2px 4px 2px 0;
}
.badge-ok { background: #DBEAFE; color: var(--navy); }
.badge-miss { background: #F1F5F9; color: #64748B; border: 1px solid var(--border); }

#MainMenu, footer { visibility: hidden; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------
DEFAULT_STATE = {
    "text_result": "",
    "image_ocr_text": "",
    "image_result": "",
    "doc_source_text": "",
    "doc_result": "",
    "doc_name": "",
    "last_translation": "",
    "last_translation_lang": "English",
    "tts_audio": None,
    "tts_label": "",
}
for _k, _v in DEFAULT_STATE.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# --------------------------------------------------------------------------
# Backend helpers
# --------------------------------------------------------------------------
def chunk_text(text: str, limit: int = MAX_CHUNK):
    """Split text into chunks below `limit`, preserving line breaks where possible."""
    chunks, current = [], ""
    for line in text.split("\n"):
        # Hard-split extremely long single lines
        while len(line) > limit:
            cut = line.rfind(" ", 0, limit)
            cut = cut if cut > 0 else limit
            piece, line = line[:cut], line[cut:].lstrip()
            if current:
                chunks.append(current)
                current = ""
            chunks.append(piece)
        if len(current) + len(line) + 1 > limit:
            if current:
                chunks.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        chunks.append(current)
    return chunks


def mock_translate(text: str, target_name: str) -> str:
    """Offline fallback: phrasebook lookup + clearly labelled simulation."""
    code = LANGUAGES.get(target_name, "en")
    lowered = text.strip().lower().rstrip("!.?")
    if lowered in MOCK_PHRASES and code in MOCK_PHRASES[lowered]:
        return MOCK_PHRASES[lowered][code]
    return f"[Simulated {target_name} translation]\n{text}"


def translate_text(text: str, target_name: str, source_name: str = AUTO):
    """
    Translate text. Returns (translated_text, warning_message_or_None).
    Never raises: falls back to mock simulation on any failure.
    """
    text = (text or "").strip()
    if not text:
        return "", None

    if not HAS_TRANSLATOR:
        return (
            mock_translate(text, target_name),
            "The `deep-translator` package is not installed, so a simulated "
            "translation is shown. Run: pip install deep-translator",
        )

    target = LANGUAGES.get(target_name, "en")
    source = "auto" if source_name == AUTO else LANGUAGES.get(source_name, "auto")

    try:
        translator = GoogleTranslator(source=source, target=target)
        parts = []
        for chunk in chunk_text(text):
            if not chunk.strip():
                parts.append(chunk)
                continue
            out = translator.translate(chunk)
            parts.append(out if out else chunk)
        return "\n".join(parts), None
    except Exception as exc:  # network down, rate limit, bad language code...
        return (
            mock_translate(text, target_name),
            f"Live translation failed ({type(exc).__name__}: {exc}). "
            "Showing a simulated result instead. Check your internet connection.",
        )


def tesseract_available():
    """Return (ok: bool, message: str)."""
    if not HAS_PIL:
        return False, "Pillow is not installed (pip install Pillow)."
    if not HAS_PYTESSERACT:
        return False, "pytesseract is not installed (pip install pytesseract)."
    try:
        version = pytesseract.get_tesseract_version()
        return True, f"Tesseract {version}"
    except Exception:
        return False, "The Tesseract OCR binary was not found on this machine."


def run_ocr(image_bytes: bytes, ocr_lang_code: str):
    """
    Extract text from an image. Returns (text, warning_or_None).
    Never raises.
    """
    if not HAS_PIL:
        return "", "Pillow is not installed, so the image cannot be processed."

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.load()
        img = ImageOps.exif_transpose(img)
        gray = ImageOps.autocontrast(img.convert("L"))
    except Exception as exc:
        return "", f"Could not open this image ({type(exc).__name__}: {exc})."

    ok, msg = tesseract_available()
    if not ok:
        return "", f"OCR unavailable: {msg} Type or paste the text manually below."

    try:
        text = pytesseract.image_to_string(gray, lang=ocr_lang_code)
        return text.strip(), None
    except Exception as exc:
        # Language pack missing? retry with English
        if ocr_lang_code != "eng":
            try:
                text = pytesseract.image_to_string(gray, lang="eng")
                return (
                    text.strip(),
                    f"Language pack '{ocr_lang_code}' is not installed; used English OCR instead.",
                )
            except Exception as exc2:
                return "", f"OCR failed ({type(exc2).__name__}: {exc2})."
        return "", f"OCR failed ({type(exc).__name__}: {exc})."


def _save_temp(data: bytes, suffix: str) -> str:
    """Write bytes to a NamedTemporaryFile(delete=False) and return its path."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(data)
        tmp.flush()
    finally:
        tmp.close()
    return tmp.name


def _safe_remove(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def extract_document_text(uploaded_file):
    """
    Extract text from .txt / .pdf / .docx. Returns (text, warning_or_None).
    Never raises.
    """
    name = uploaded_file.name
    ext = os.path.splitext(name)[1].lower()
    data = uploaded_file.getvalue()
    tmp_path = None

    try:
        if ext == ".txt":
            for enc in ("utf-8-sig", "utf-8", "utf-16", "latin-1"):
                try:
                    return data.decode(enc).strip(), None
                except Exception:
                    continue
            return data.decode("utf-8", errors="ignore").strip(), \
                "Some characters could not be decoded and were skipped."

        if ext == ".pdf":
            if not HAS_PDF:
                return "", "PDF support missing. Run: pip install PyPDF2"
            tmp_path = _save_temp(data, ".pdf")
            reader = PdfReader(tmp_path)
            if getattr(reader, "is_encrypted", False):
                try:
                    reader.decrypt("")
                except Exception:
                    return "", "This PDF is password-protected and cannot be read."
            pages = []
            for page in reader.pages:
                try:
                    pages.append(page.extract_text() or "")
                except Exception:
                    pages.append("")
            text = "\n\n".join(p.strip() for p in pages if p.strip())
            if not text:
                return "", ("No selectable text found. This may be a scanned PDF; "
                            "try converting pages to images and using the OCR tab.")
            return text, None

        if ext == ".docx":
            if not HAS_DOCX:
                return "", "DOCX support missing. Run: pip install python-docx"
            tmp_path = _save_temp(data, ".docx")
            document = docx.Document(tmp_path)
            lines = [p.text for p in document.paragraphs if p.text.strip()]
            for table in document.tables:
                for row in table.rows:
                    cells = [c.text.strip() for c in row.cells if c.text.strip()]
                    if cells:
                        lines.append(" | ".join(cells))
            text = "\n".join(lines).strip()
            if not text:
                return "", "No text content found in this document."
            return text, None

        return "", f"Unsupported file type: {ext}"

    except Exception as exc:
        return "", f"Could not read '{name}' ({type(exc).__name__}: {exc})."
    finally:
        _safe_remove(tmp_path)


def build_docx_bytes(text: str):
    """Create a .docx file in memory. Returns bytes or None."""
    if not HAS_DOCX:
        return None
    try:
        document = docx.Document()
        document.add_heading("Translated Document", level=1)
        for para in text.split("\n"):
            document.add_paragraph(para)
        buf = io.BytesIO()
        document.save(buf)
        return buf.getvalue()
    except Exception:
        return None


def generate_tts(text: str, lang_name: str):
    """
    Generate mp3 bytes using gTTS via a temp file.
    Returns (audio_bytes_or_None, warning_or_None). Never raises.
    """
    text = (text or "").strip()
    if not text:
        return None, "There is no text to convert to speech."
    if not HAS_GTTS:
        return None, "gTTS is not installed. Run: pip install gTTS"

    lang_code = LANGUAGES.get(lang_name, "en")
    tmp_path = None
    try:
        # gTTS limits are generous, but keep requests reasonable
        trimmed = text[:3000]
        tts = gTTS(text=trimmed, lang=lang_code, slow=False)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp_path = tmp.name
        tmp.close()
        tts.save(tmp_path)
        with open(tmp_path, "rb") as fh:
            audio = fh.read()
        if not audio:
            return None, "Audio generation returned an empty file."
        note = None
        if len(text) > 3000:
            note = "Text was longer than 3000 characters; audio covers the first 3000."
        return audio, note
    except Exception as exc:
        return None, (f"Audio generation failed ({type(exc).__name__}: {exc}). "
                      "gTTS needs an internet connection and a supported language.")
    finally:
        _safe_remove(tmp_path)


def remember_translation(text: str, lang_name: str):
    """Store the most recent translation so the TTS tab can reuse it."""
    if text:
        st.session_state["last_translation"] = text
        st.session_state["last_translation_lang"] = lang_name


def card_header(title: str, subtitle: str = ""):
    sub = f"<div style='color:#64748B;font-size:0.88rem'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"<div class='card'><div class='card-title'>{title}</div>{sub}</div>",
        unsafe_allow_html=True,
    )


def show_image(img_source):
    """Display an image compatibly across Streamlit versions."""
    try:
        st.image(img_source, use_container_width=True)
    except TypeError:
        st.image(img_source, use_column_width=True)


def badge(label: str, ok: bool) -> str:
    cls = "badge-ok" if ok else "badge-miss"
    icon = "✓" if ok else "✕"
    return f"<span class='{cls}'>{icon} {label}</span>"


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🌐 LinguaBridge")
    st.caption("Translate text, images, documents & speech.")

    target_lang = st.selectbox(
        "Target language",
        list(LANGUAGES.keys()),
        index=list(LANGUAGES.keys()).index("Hindi"),
        help="Language to translate into (used in every tab).",
    )
    source_lang = st.selectbox(
        "Source language",
        [AUTO] + list(LANGUAGES.keys()),
        index=0,
        help="Leave on Auto-detect unless you know the original language.",
    )

    ocr_ok, ocr_msg = tesseract_available()
    st.markdown(
        "<div class='side-card'><b>System status</b><br>"
        + badge("Translator", HAS_TRANSLATOR)
        + badge("OCR", ocr_ok)
        + badge("PDF", HAS_PDF)
        + badge("DOCX", HAS_DOCX)
        + badge("TTS", HAS_GTTS)
        + "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='side-card'>Live translation and speech need an internet "
        "connection. If a feature is unavailable, the app shows a warning and "
        "falls back safely instead of crashing.</div>",
        unsafe_allow_html=True,
    )

# --------------------------------------------------------------------------
# Hero header
# --------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <h1>🌐 LinguaBridge Translator</h1>
        <p>One workspace for text, images, documents and pronunciation.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_text, tab_image, tab_doc, tab_tts = st.tabs(
    ["📝 Text Translation", "🖼️ Image OCR & Translate", "📄 Document Parser", "🔊 Audio Pronunciation"]
)

# ==========================================================================
# TAB 1: Text translation
# ==========================================================================
with tab_text:
    card_header("Text Translation", "Type or paste text on the left; the translation appears on the right.")
    col_src, col_out = st.columns(2, gap="large")

    with col_src:
        st.markdown("#### Source text")
        source_text = st.text_area(
            "Enter text to translate",
            height=280,
            placeholder="Type or paste your text here...",
            label_visibility="collapsed",
            key="text_input",
        )
        st.caption(f"{len(source_text)} characters")
        do_translate = st.button("Translate", key="btn_translate_text")

    if do_translate:
        if not source_text.strip():
            st.warning("Please enter some text to translate.")
        else:
            with st.spinner("Translating..."):
                result, warn = translate_text(source_text, target_lang, source_lang)
            st.session_state["text_result"] = result
            remember_translation(result, target_lang)
            if warn:
                st.warning(warn)

    with col_out:
        st.markdown(f"#### Translation ({target_lang})")
        st.text_area(
            "Translated output",
            value=st.session_state["text_result"],
            height=280,
            disabled=True,
            label_visibility="collapsed",
        )
        if st.session_state["text_result"]:
            st.download_button(
                "Download translation (.txt)",
                data=st.session_state["text_result"].encode("utf-8"),
                file_name="translation.txt",
                mime="text/plain",
                key="dl_text",
            )

# ==========================================================================
# TAB 2: Image OCR & translate
# ==========================================================================
with tab_image:
    card_header("Image OCR & Translate", "Upload a PNG/JPG image, extract its text, then translate it instantly.")

    ocr_ok, ocr_msg = tesseract_available()
    if not ocr_ok:
        st.warning(
            f"{ocr_msg} Image text extraction is disabled, but you can still "
            "type or paste the text below to translate it."
        )

    ocr_lang_name = st.selectbox(
        "Language of the text inside the image",
        list(OCR_LANGS.keys()),
        index=0,
        key="ocr_lang",
        help="Requires the matching Tesseract language pack. Falls back to English if missing.",
    )

    uploaded_img = st.file_uploader(
        "Upload an image", type=["png", "jpg", "jpeg"], key="img_upload"
    )

    col_img, col_ocr = st.columns(2, gap="large")

    if uploaded_img is not None:
        with col_img:
            st.markdown("#### Preview")
            try:
                show_image(uploaded_img)
            except Exception as exc:
                st.warning(f"Could not preview the image ({type(exc).__name__}).")

        if st.button("Extract text & translate", key="btn_ocr"):
            with st.spinner("Reading image..."):
                extracted, warn = run_ocr(uploaded_img.getvalue(), OCR_LANGS[ocr_lang_name])
            if warn:
                st.warning(warn)
            st.session_state["image_ocr_text"] = extracted
            if extracted:
                with st.spinner("Translating..."):
                    result, warn2 = translate_text(extracted, target_lang, source_lang)
                st.session_state["image_result"] = result
                remember_translation(result, target_lang)
                if warn2:
                    st.warning(warn2)
            else:
                st.session_state["image_result"] = ""
                if not warn:
                    st.warning("No text could be detected in this image.")

    with col_ocr:
        st.markdown("#### Extracted text (editable)")
        edited_ocr = st.text_area(
            "Extracted text",
            value=st.session_state["image_ocr_text"],
            height=200,
            label_visibility="collapsed",
            key=f"ocr_edit_{hash(st.session_state['image_ocr_text']) % 10**8}",
            placeholder="Extracted text appears here. You can also type text manually.",
        )
        if st.button("Translate this text", key="btn_ocr_retranslate"):
            if not edited_ocr.strip():
                st.warning("There is no text to translate.")
            else:
                with st.spinner("Translating..."):
                    result, warn = translate_text(edited_ocr, target_lang, source_lang)
                st.session_state["image_ocr_text"] = edited_ocr
                st.session_state["image_result"] = result
                remember_translation(result, target_lang)
                if warn:
                    st.warning(warn)

    if st.session_state["image_result"]:
        st.markdown(f"#### Translation ({target_lang})")
        st.text_area(
            "Image translation output",
            value=st.session_state["image_result"],
            height=200,
            disabled=True,
            label_visibility="collapsed",
        )
        st.download_button(
            "Download translation (.txt)",
            data=st.session_state["image_result"].encode("utf-8"),
            file_name="image_translation.txt",
            mime="text/plain",
            key="dl_image",
        )

# ==========================================================================
# TAB 3: Document parser
# ==========================================================================
with tab_doc:
    card_header("Document Parser", "Upload a .txt, .pdf or .docx file, translate it, and download the result.")

    missing = []
    if not HAS_PDF:
        missing.append("PDF (pip install PyPDF2)")
    if not HAS_DOCX:
        missing.append("DOCX (pip install python-docx)")
    if missing:
        st.warning("Some document formats are unavailable: " + ", ".join(missing))

    uploaded_doc = st.file_uploader(
        "Upload a document", type=["txt", "pdf", "docx"], key="doc_upload"
    )

    if uploaded_doc is not None:
        if st.button("Parse & translate document", key="btn_doc"):
            with st.spinner("Extracting text..."):
                extracted, warn = extract_document_text(uploaded_doc)
            if warn:
                st.warning(warn)
            st.session_state["doc_source_text"] = extracted
            st.session_state["doc_name"] = os.path.splitext(uploaded_doc.name)[0]
            if extracted:
                with st.spinner("Translating document..."):
                    result, warn2 = translate_text(extracted, target_lang, source_lang)
                st.session_state["doc_result"] = result
                remember_translation(result, target_lang)
                if warn2:
                    st.warning(warn2)
            else:
                st.session_state["doc_result"] = ""

    if st.session_state["doc_source_text"]:
        col_a, col_b = st.columns(2, gap="large")
        with col_a:
            st.markdown("#### Original text")
            st.text_area(
                "Original document text",
                value=st.session_state["doc_source_text"],
                height=320,
                disabled=True,
                label_visibility="collapsed",
            )
            st.caption(f"{len(st.session_state['doc_source_text'])} characters extracted")
        with col_b:
            st.markdown(f"#### Translation ({target_lang})")
            st.text_area(
                "Translated document text",
                value=st.session_state["doc_result"],
                height=320,
                disabled=True,
                label_visibility="collapsed",
            )

        if st.session_state["doc_result"]:
            base = st.session_state["doc_name"] or "document"
            dl1, dl2, _ = st.columns([1, 1, 2])
            with dl1:
                st.download_button(
                    "Download as .txt",
                    data=st.session_state["doc_result"].encode("utf-8"),
                    file_name=f"{base}_translated.txt",
                    mime="text/plain",
                    key="dl_doc_txt",
                )
            with dl2:
                docx_bytes = build_docx_bytes(st.session_state["doc_result"])
                if docx_bytes:
                    st.download_button(
                        "Download as .docx",
                        data=docx_bytes,
                        file_name=f"{base}_translated.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key="dl_doc_docx",
                    )

# ==========================================================================
# TAB 4: Audio pronunciation (TTS)
# ==========================================================================
with tab_tts:
    card_header("Audio Pronunciation", "Hear any translated text spoken aloud with Google Text-to-Speech.")

    if not HAS_GTTS:
        st.warning("gTTS is not installed, so audio is unavailable. Run: pip install gTTS")

    mode = st.radio(
        "Text to speak",
        ["Use my latest translation", "Type custom text"],
        horizontal=True,
        key="tts_mode",
    )

    if mode == "Use my latest translation":
        tts_text = st.session_state["last_translation"]
        tts_lang = st.session_state["last_translation_lang"]
        if tts_text:
            st.text_area(
                "Text that will be spoken",
                value=tts_text,
                height=160,
                disabled=True,
            )
            st.caption(f"Speech language: {tts_lang}")
        else:
            st.info("No translation yet. Translate something in another tab first, or choose 'Type custom text'.")
    else:
        tts_text = st.text_area(
            "Enter text to speak",
            height=160,
            placeholder="Type text in the language you choose below...",
            key="tts_custom_text",
        )
        tts_lang = st.selectbox(
            "Speech language",
            list(LANGUAGES.keys()),
            index=list(LANGUAGES.keys()).index(target_lang),
            key="tts_custom_lang",
        )

    if st.button("Generate audio", key="btn_tts"):
        if not (tts_text or "").strip():
            st.warning("Please provide some text first.")
        else:
            with st.spinner("Generating audio..."):
                audio_bytes, warn = generate_tts(tts_text, tts_lang)
            if warn:
                st.warning(warn)
            st.session_state["tts_audio"] = audio_bytes
            st.session_state["tts_label"] = tts_lang

    if st.session_state["tts_audio"]:
        st.markdown(f"#### Playback ({st.session_state['tts_label']})")
        try:
            st.audio(st.session_state["tts_audio"], format="audio/mp3")
        except Exception as exc:
            st.warning(f"Audio player could not load ({type(exc).__name__}).")
        st.download_button(
            "Download audio (.mp3)",
            data=st.session_state["tts_audio"],
            file_name="pronunciation.mp3",
            mime="audio/mpeg",
            key="dl_tts",
        )

# --------------------------------------------------------------------------
# Footer
# --------------------------------------------------------------------------
st.markdown(
    "<div style='text-align:center;color:#64748B;font-size:0.82rem;margin-top:28px'>"
    "LinguaBridge · Built with Streamlit · Translations are machine-generated; "
    "review important content before use."
    "</div>",
    unsafe_allow_html=True,
)