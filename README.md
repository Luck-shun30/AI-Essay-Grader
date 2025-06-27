# AI Essay Grader ✍️

A modern, customizable web app for grading essays using AI (Google Gemini). Upload essays, provide rubrics, and receive detailed, actionable feedback with grading and rubric support.

---

## Features
- **AI-Powered Grading:** Uses Google Gemini API for essay analysis and feedback.
- **Flexible Input:** Upload essays and rubrics as text, PDF, or DOCX, or type directly.
- **Customizable Settings:**
  - User profile (name, grading scale, default rubric)
  - Theme selection (light/dark/auto)
  - Multiple rubric templates (coming soon)
- **Progress & Animations:** Visual feedback during grading.
- **Download & Share:** Download feedback or copy/share results.

---

## Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Luck-shun30/AI-Essay-Grader
cd AI-Essay-Grader
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
- Create a `.env` file in the root directory.
- Add your Google Gemini API key:
  ```
  GEMINI_API_KEY=your_api_key_here
  ```

### 4. Run the App
```bash
streamlit run frontend/app.py
```

---

## Usage
- Use the sidebar to navigate between the Essay Grader and User Settings.
- In **User Settings**, set your name, grading scale, theme, and (soon) rubric templates.
- In **Essay Grader**:
  - Enter or upload an essay and rubric.
  - Optionally add extra grading instructions.
  - Click **Grade Essay** to receive feedback and a grade.
  - Download or share the results.

---

## Customization
- **Themes:** Select your preferred theme in User Settings.
- **Rubric Templates:** (Coming soon) Save and reuse multiple rubrics.
- **Progress Bar/Animations:** Visual feedback during grading.

---

## File Structure
```
AI-Essay-Grader/
  backend/
    clipboard_utils.py
    file_utils.py
    gemini_api.py
  frontend/
    app.py
  requirements.txt
  README.md
```

---

## Contributing
Pull requests and suggestions are welcome! Please open an issue to discuss changes or new features.

---

## License
MIT License
