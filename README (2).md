# 🌐 LinguaFlow – Text and Document Language Translator

LinguaFlow is a small web application built with **Python and Streamlit**. It translates typed text and uploaded documents (PDF, DOCX, TXT) between many languages, using the free Google Translate service through the `deep-translator` library. No API key and no database are needed.

Built for the CodeAlpha Artificial Intelligence internship.

---

## 1. Features

**Text Translator tab**
- Source language (with *Auto Detect*) and target language dropdowns
- Swap languages button
- Large text box with character and word counter
- Translate and Clear buttons
- Output panel with a built-in copy icon
- Recent translations (kept in session state) with a Clear history button
- Clear messages for empty input, same source/target language, no internet, and too many requests

**Document Translator tab**
- Upload `.pdf`, `.docx` or `.txt` (drag-and-drop or browse), maximum 10 MB
- Shows the file name and size
- Progress bar while translating
- Preview of the extracted text and the translated text
- Download button for the translated file

---

## 2. Project structure

```
linguaflow/
├── app.py                 # the whole application (one file)
├── requirements.txt       # libraries to install
├── README.md              # this file
└── .streamlit/
    └── config.toml        # light blue theme + 10 MB upload limit
```

`requirements.txt`

```
streamlit>=1.40
deep-translator>=1.11.4
pypdf>=4.0.0
python-docx>=1.1.0
```

---

## 3. Installation on Windows (VS Code)

Use the **VS Code terminal** (Terminal → New Terminal). If it opens PowerShell, use the PowerShell commands. If it opens Command Prompt, use the Command Prompt ones.

**Step 1 – Check that Python is installed** (3.9 or newer; 3.10–3.12 are the safest)

```
python --version
```

If you get an error, install Python from python.org and tick **"Add Python to PATH"** during setup.

**Step 2 – Create the project folder and open it in VS Code** (run in any terminal)

```
mkdir linguaflow
cd linguaflow
code .
```

Now copy `app.py`, `requirements.txt`, `README.md` and the `.streamlit` folder into this folder. In VS Code open a new terminal; it starts inside `linguaflow`.

**Step 3 – Create a virtual environment** (a private box for this project's libraries)

```
python -m venv venv
```

**Step 4 – Activate it**

PowerShell:

```
venv\Scripts\Activate.ps1
```

Command Prompt:

```
venv\Scripts\activate.bat
```

You should see `(venv)` at the start of the line.
If PowerShell says *"running scripts is disabled"*, run this once and try again:

```
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**Step 5 – Install the libraries**

```
pip install -r requirements.txt
```

**Step 6 – Run the application**

```
streamlit run app.py
```

The browser opens at `http://localhost:8501`. If it does not, open that address yourself. (If Streamlit asks for an email the first time, just press Enter.)

**Step 7 – Stop the application**

Click inside the terminal and press **Ctrl + C**. To leave the virtual environment type `deactivate`.

**Next time:** open the folder in VS Code, activate the virtual environment (Step 4), and run Step 6.

---

## 4. How the code is organised (`app.py`)

| Section | What it does |
|---|---|
| 1. Settings | Numbers you can change: upload limit (10 MB), chunk size (4500), history size, etc. |
| 2. Languages | Asks the translator which languages it supports and builds a *name → code* dictionary (for example `"Marathi" → "mr"`). Only supported languages are shown. Common languages are listed first. |
| 3. Core translation | `translate_chunk` translates one piece of text (retries up to 3 times). `split_into_chunks` cuts long text at line breaks into pieces under 4500 characters, because Google accepts about 5000 characters per request. `translate_long_text` translates the pieces in order and joins them. `friendly_error` turns technical errors into simple messages. |
| 4. Reading files | One function per format: `extract_text_from_pdf` (PyPDF), `extract_text_from_docx` (python-docx), `extract_text_from_txt` (built-in `decode`). `check_uploaded_file` validates type, size and file signature. |
| 5. Document translation | `translate_docx` translates paragraph by paragraph and keeps fonts and bold/italic where possible. `translate_document` runs the whole workflow: validate → extract → check for text → translate → create file. |
| 6. Session state | `st.session_state` remembers things between clicks (Streamlit re-runs the file on every click). Also the button callbacks: swap, clear, history. |
| 7. Look and feel | A small CSS block: light-blue background, white rounded cards, shadows, blue–indigo gradient buttons, mobile rules. |
| 8–9. The two tabs | `show_text_tab()` and `show_document_tab()`. |
| 10. Page layout | Creates the two tabs and the footer. |

**Library methods in simple English**
- `GoogleTranslator(source="en", target="mr")` – creates a translator object.
- `.translate(text)` – sends the text to Google and returns the translated text.
- `GoogleTranslator().get_supported_languages(as_dict=True)` – returns the supported languages as `{name: code}`.
- `PdfReader(file).pages` – the pages of a PDF; `page.extract_text()` – the text on one page.
- `Document(file).paragraphs` – the paragraphs of a Word file; `document.save(buffer)` – writes a Word file.
- `st.download_button(...)` – shows a button that downloads data to the user's computer.

---

## 5. What was tested and what was not

I could only test inside a sandbox with **no access to PyPI or Google Translate**, so please read this honestly.

| Item | Status |
|---|---|
| `app.py` compiles with no syntax errors | ✅ Tested |
| No unused or missing imports (static check) | ✅ Tested |
| `split_into_chunks` (short, long, one huge line, no spaces): chunks ≤ 4500 characters, order kept, no text lost | ✅ Tested |
| `extract_text_from_txt` for UTF-8, UTF-8 with BOM, UTF-16 and Windows-1252 files, including Devanagari text | ✅ Tested |
| Running the Streamlit interface (layout, CSS, buttons, tabs) | ⚠️ Not run here – **you must run it and check (Section 6)** |
| Real translation through Google Translate | ⚠️ Not run here – needs internet on your computer |
| PDF extraction, DOCX reading and writing with real files | ⚠️ Not run here – libraries could not be installed |
| Language names such as "Chinese (Simplified)" appearing in the dropdown | ⚠️ Expected from deep-translator's language list; the app only shows languages the library reports, and the nine common languages should appear. Please confirm in the dropdown. |
| Translated PDF output, OCR, text-to-speech, dark theme | ❌ Not implemented (see Limitations) |

Streamlit **1.40 or newer** is required because the CSS uses container keys.

---

## 6. Manual test cases

Run these after `streamlit run app.py`. Internet is required.

### Text translation

| # | Steps | Expected result |
|---|---|---|
| T1 | From: Auto Detect, To: Hindi. Type `Hello, how are you?` and click **Translate**. | Hindi text appears in the output panel. |
| T2 | From: English, To: Marathi. Translate `Good morning. I am a student.` | Marathi text appears. |
| T3 | Click **Translate** with an empty box. | Warning: "Please type or paste some text first." |
| T4 | Set From = English and To = English, enter text, click Translate. | Warning about same languages. |
| T5 | Type text, check the counter below the box. | Shows the correct characters and words. |
| T6 | Click **Clear text**. | Input and output are both emptied. |
| T7 | Translate English → French, then click **⇄**. | Languages swap and the French text moves to the input box. Translate again to get English back. |
| T8 | With From = Auto Detect click **⇄**. | Warning that Auto Detect cannot be swapped. |
| T9 | Do 3 translations, open **Recent translations**, then click **Clear history**. | List shows them (newest first), then becomes empty. |
| T10 | Turn off Wi-Fi and click Translate. | Error: "Could not reach the translation service…" |
| T11 | Paste about 8000 characters. | Translates successfully (split into chunks). |
| T12 | Click the copy icon at the top-right of the output box and paste into Notepad. | The translated text is pasted. |

### Document translation

Create these small files first: `sample.txt` (a few English sentences), `sample.docx` (a Word file with a heading, a bold word and 2–3 paragraphs), `sample.pdf` (use Word → Save As PDF).

| # | Steps | Expected result |
|---|---|---|
| D1 | Upload `sample.txt`, To: Hindi, click **Translate Document**. | Progress bar, both previews, download of `sample_translated_hi.txt`. |
| D2 | Upload `sample.docx`, To: Marathi. | Previews appear; download `sample_translated_mr.docx`. Open it in Word: same paragraph order, headings and bold kept where possible. |
| D3 | Upload `sample.pdf`, To: Spanish. | Extracted text preview, translated preview, download `sample_translated_es.txt`. |
| D4 | Upload a scanned PDF or a PDF of photographs. | Error explaining that OCR is needed. |
| D5 | Upload an empty `.txt` file. | Error: "The uploaded file is empty." |
| D6 | Rename `notes.txt` to `notes.pdf` and upload it. | Error: "not a real PDF file". |
| D7 | Try to upload a `.png` or `.xlsx`. | The uploader refuses the file type. |
| D8 | Upload a file larger than 10 MB. | Rejected by the uploader (10 MB limit). |
| D9 | Upload a `.txt` saved in Notepad as "UTF-8" and as "ANSI". | Both are read correctly. |
| D10 | Upload a file, translate, then choose a different target language. | The old result disappears; click Translate Document again for the new one. |

---

## 7. Application workflow (for your presentation)

**Text translation**
1. The user types text and chooses From and To languages.
2. The program checks the text is not empty and the languages differ.
3. Names are changed into codes ("Marathi" → "mr").
4. Long text is cut into small chunks.
5. Each chunk is sent to Google Translate through `deep-translator`.
6. The translated chunks are joined in the same order.
7. The result is shown, and saved in the recent history.

**Document translation**
1. The user uploads a PDF, DOCX or TXT file.
2. The program validates the file type, size and signature.
3. The correct reader extracts the text (PyPDF, python-docx, or plain decoding).
4. If there is no text, a clear message is shown (for scanned PDFs: OCR needed).
5. The text is split into chunks and translated in order.
6. A new file is created: DOCX for Word input, TXT for PDF and TXT input.
7. Both previews are shown and the user downloads the translated file.

**One-line summary:** *Upload or type → extract text → split into chunks → translate with Google → join → show and download.*

---

## 8. Possible viva questions with easy answers

1. **What is LinguaFlow?** A Streamlit web app that translates text and PDF, DOCX and TXT documents.
2. **Why Streamlit?** It builds a web interface using only Python, so no HTML, JavaScript or separate backend is needed.
3. **Which translation service do you use?** Google Translate through the `deep-translator` library. It needs no API key, but it needs internet.
4. **What does `deep-translator` do?** It is a Python wrapper that sends our text to translation services and returns the result.
5. **How do you detect the source language automatically?** By passing `source="auto"` to `GoogleTranslator`; Google detects it.
6. **Why do you split text into chunks?** Google accepts about 5000 characters per request, so long text is cut into pieces under 4500 characters and translated one by one.
7. **How do you avoid cutting sentences in half?** The text is split at line breaks. Only a single extremely long line is cut at a space.
8. **How are language codes handled?** A dictionary maps names to codes (for example "Hindi" → "hi"). It comes from the library, so only supported languages are shown.
9. **How do you read a PDF?** With PyPDF: open the file, loop through the pages and call `extract_text()` on each.
10. **What about scanned PDFs?** They contain pictures, not text, so PyPDF finds nothing. OCR would be needed. The app shows a message instead of pretending to work.
11. **How do you keep Word formatting?** Each paragraph is made of runs with their own font and style. The translation is put into the first run, so its style is kept. Complex formatting may still change.
12. **Why is PDF output a TXT file?** It is the simplest reliable option. A translated PDF needs a font for every language and layout handling.
13. **What is `st.session_state`?** Streamlit re-runs the script on every click; session state stores values (such as history) between runs.
14. **How do you handle errors?** `try-except` blocks around translation and file reading, and `friendly_error` shows simple messages (no internet, too many requests, damaged file).
15. **How do you validate uploads?** Check the extension, check that the file is not empty or over 10 MB, and check the file signature (`%PDF` for PDF; DOCX files are zip files that start with `PK`).
16. **How do you handle large files or API limits?** Chunking, a retry (up to 3 times with a short wait), and a clear "too many requests" message.
17. **What is a virtual environment?** A private folder of libraries for one project, so projects do not conflict.
18. **What are the limitations?** No OCR, PDF layout and tables are lost, only normal DOCX paragraphs are translated (not tables or headers), and the free service can be slow or limited.
19. **What would you add next?** OCR for scanned PDFs, translated PDF output, tables in DOCX, text-to-speech, and DeepL as an optional provider.
20. **Is the translation real?** Yes. Every translation is a live request to Google Translate; nothing is hard-coded.

---

## 9. Troubleshooting

**Installation**
- `'python' is not recognized` – reinstall Python and tick *Add Python to PATH*, or try `py --version` and use `py` instead of `python`.
- `running scripts is disabled` when activating – see Step 4 (`Set-ExecutionPolicy`), or use Command Prompt.
- `pip is not recognized` – use `python -m pip install -r requirements.txt`.
- `No matching distribution found` or timeouts – check your internet, then try `python -m pip install --upgrade pip` and install again.
- `streamlit is not recognized` – the virtual environment is not active (look for `(venv)`), or use `python -m streamlit run app.py`.
- `ModuleNotFoundError: No module named 'docx'` – the package is called `python-docx`, not `docx`. Run `pip install python-docx`.
- Streamlit complains about `key` in `st.container` or `wrap_lines` – your Streamlit is too old: `pip install --upgrade streamlit`.
- Port busy – `streamlit run app.py --server.port 8502`.

**Translation / API connection**
- "Could not reach the translation service" – no internet, or a firewall/VPN/college network is blocking Google. Try a mobile hotspot.
- "Too many requests" – you sent many requests quickly. Wait a minute and try again.
- Language dropdown fails to load at startup – the app asks the library for its language list; this works offline in recent versions of `deep-translator`. If it fails, upgrade it: `pip install --upgrade deep-translator`.
- Translation returns the same text – the source and target may be the same, or the text contains only numbers or symbols.

**File processing**
- "No readable text was found in this PDF" – the PDF is scanned (images). OCR is required.
- "Could not read this PDF/DOCX file. It may be damaged." – re-save the file from Word and try again. Old `.doc` files must be saved as `.docx`.
- "This PDF is password-protected" – remove the password first.
- Strange characters in a TXT file – save it as UTF-8 in Notepad (File → Save As → Encoding).
- Hindi/Marathi text looks like boxes when opening the `.txt` – open it in VS Code or Notepad, which support UTF-8.
- Extra text from a PDF appears in the wrong order – PDFs with columns or tables do not extract in reading order. This is a known limitation of plain text extraction.

---

## 10. Limitations of this first version

- PDF input produces a **TXT** download. Layout, tables, images and fonts are not preserved.
- Scanned PDFs are not supported (OCR needed).
- In DOCX files only normal paragraphs are translated; tables, text boxes, headers and footers are left untouched.
- It uses free Google Translate, so it needs internet and very large files can be slow.
- Text-to-speech and dark-theme toggle were not added, to keep the code simple. (The page follows a fixed light-blue theme.)

## 11. Optional: DeepL instead of Google

DeepL needs a free API key from deepl.com (an account is required) and supports fewer languages than Google, so check that your languages are supported before using it. `deep-translator` already includes a `DeeplTranslator` class, so no extra package is needed: replace `GoogleTranslator(...)` with `DeeplTranslator(api_key="YOUR_KEY", source="en", target="de", use_free_api=True)`. The language list and codes would also need to change, so this is not part of the basic demo. Never put the key in code you share; read it from an environment variable.
