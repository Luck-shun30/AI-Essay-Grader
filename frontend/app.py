import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
from dotenv import load_dotenv
import json
from backend.gemini_api import build_gemini_prompt, get_gemini_response
from backend.file_utils import read_uploaded_file, load_user_settings, save_user_settings, save_grammar_spelling_issues, load_grammar_spelling_issues
from backend.clipboard_utils import copy_to_clipboard
import language_tool_python
import toml

load_dotenv()

if 'grading_result' not in st.session_state:
    st.session_state.grading_result = None
if 'essay' not in st.session_state:
    st.session_state.essay = ""
if 'rubric' not in st.session_state:
    st.session_state.rubric = ""
if 'extra' not in st.session_state:
    st.session_state.extra = ""

def apply_theme():
    # Read theme from user settings and update .streamlit/config.toml
    settings_path = os.path.join(os.path.dirname(__file__), '../user_settings.json')
    config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.streamlit'))
    config_path = os.path.join(config_dir, 'config.toml')
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    try:
        settings = load_user_settings(settings_path)
        theme = settings.get('theme', 'Dark Blue')
    except Exception:
        theme = 'Dark Blue'
    theme_presets = {
        'Dark Blue': {
            'base': 'dark',
            'primaryColor': '#1f77b4',
            'backgroundColor': '#18191A',
            'secondaryBackgroundColor': '#23272F',
            'textColor': '#f8f9fa',
        },
        'Dark Green': {
            'base': 'dark',
            'primaryColor': '#2ecc40',
            'backgroundColor': '#18191A',
            'secondaryBackgroundColor': '#23272F',
            'textColor': '#f8f9fa',
        },
        'Light Blue': {
            'base': 'light',
            'primaryColor': '#1f77b4',
            'backgroundColor': '#f8f9fa',
            'secondaryBackgroundColor': '#f0f2f6',
            'textColor': '#222',
        },
        'Light Green': {
            'base': 'light',
            'primaryColor': '#2ecc40',
            'backgroundColor': '#f8f9fa',
            'secondaryBackgroundColor': '#f0f2f6',
            'textColor': '#222',
        },
    }
    preset = theme_presets.get(theme, theme_presets['Dark Blue'])
    config = {
        'theme': {
            'base': preset['base'],
            'primaryColor': preset['primaryColor'],
            'backgroundColor': preset['backgroundColor'],
            'secondaryBackgroundColor': preset['secondaryBackgroundColor'],
            'textColor': preset['textColor'],
        }
    }
    with open(config_path, 'w') as f:
        toml.dump(config, f)

def main():
    st.title("AI Essay Grader ✍️")
    st.markdown("""
        <div style='margin-bottom: 1.5em;'>
        Upload or enter the student's essay, the grading rubric, and any extra grading instructions. The AI will analyze, score, and provide detailed feedback with specific quotes from the essay.
        </div>
    """, unsafe_allow_html=True)

    # Always apply dark mode with blue accent
    apply_theme()

    # Target word count input (now on main page)
    st.markdown("#### Target Word Count (optional)")
    target_word_count = st.text_input("Target Word Count", value="")
    try:
        target_word_count = int(target_word_count) if target_word_count.strip() else None
    except ValueError:
        st.error("Target word count must be a number.")
        target_word_count = None

    # Inputs in columns for conciseness
    with st.expander("📝 Essay Input", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            essay_input_method = st.radio("Essay input method:", ["Text Input", "File Upload"], key="essay_method")
        with col2:
            if essay_input_method == "Text Input":
                essay = st.text_area("Student Essay", height=150, value=st.session_state.essay, key="essay_input")
                st.session_state.essay = essay
            else:
                uploaded_essay = st.file_uploader("Upload Essay File", type=['txt', 'docx', 'pdf'], key="essay_upload")
                essay = read_uploaded_file(uploaded_essay)
                if uploaded_essay:
                    st.success(f"✅ Uploaded: {uploaded_essay.name}")
                    st.session_state.essay = essay

    # Word count metric and progress bar
    essay = st.session_state.essay
    word_count = len(essay.split()) if essay else 0
    st.markdown(f"**Word Count:** {word_count}")
    if target_word_count:
        progress = min(word_count / target_word_count, 1.0)
        st.progress(progress, text=f"{word_count} / {target_word_count} words")
        if word_count > target_word_count:
            st.info(f"You have exceeded the target by {word_count - target_word_count} words.")

    # Grammar and spelling checks
    if essay:
        if st.button("Check Grammar & Spelling", key="grammar_check"):
            import time
            progress_placeholder = st.empty()
            animation_placeholder = st.empty()
            for i in range(10):
                progress_placeholder.progress((i+1)*10, text=f"Checking... {(i+1)*10}%")
                animation_placeholder.markdown(
                    f"<div style='text-align:center; font-size:2em;'>🔎 <span style='animation: bounce 1s infinite;'>{'.' * ((i % 3) + 1)}</span></div>"
                    "<style>@keyframes bounce {0%, 100% {transform: translateY(0);} 50% {transform: translateY(-10px);}}</style>",
                    unsafe_allow_html=True
                )
                time.sleep(0.05)
            try:
                tool = language_tool_python.LanguageToolPublicAPI('en-US')
                matches = tool.check(essay)
                grammar_issues = [m for m in matches if m.ruleIssueType == 'grammar']
                spelling_issues = [m for m in matches if m.ruleIssueType == 'misspelling']
                all_issues = []
                for m in grammar_issues:
                    all_issues.append({
                        'type': 'grammar',
                        'text': essay[m.offset:m.offset + m.errorLength],
                        'offset': m.offset,
                        'message': m.message,
                        'suggestions': m.replacements
                    })
                for m in spelling_issues:
                    all_issues.append({
                        'type': 'spelling',
                        'text': essay[m.offset:m.offset + m.errorLength],
                        'offset': m.offset,
                        'message': m.message,
                        'suggestions': m.replacements
                    })
                save_grammar_spelling_issues(all_issues)
                progress_placeholder.empty()
                animation_placeholder.empty()
                if grammar_issues or spelling_issues:
                    st.markdown("### 📝 Grammar & Spelling Checks")
                    if grammar_issues:
                        st.warning(f"Grammar issues found: {len(grammar_issues)}")
                        for m in grammar_issues[:5]:
                            error_text = essay[m.offset:m.offset + m.errorLength]
                            suggestions = ', '.join(m.replacements) if m.replacements else 'No suggestions'
                            st.markdown(f"- **{error_text}** (at position {m.offset}): {m.message} <br>**Suggestions:** {suggestions}", unsafe_allow_html=True)
                        if len(grammar_issues) > 5:
                            st.markdown(f"...and {len(grammar_issues) - 5} more.")
                    if spelling_issues:
                        st.warning(f"Spelling issues found: {len(spelling_issues)}")
                        for m in spelling_issues[:5]:
                            error_text = essay[m.offset:m.offset + m.errorLength]
                            suggestions = ', '.join(m.replacements) if m.replacements else 'No suggestions'
                            st.markdown(f"- **{error_text}** (at position {m.offset}): {m.message} <br>**Suggestions:** {suggestions}", unsafe_allow_html=True)
                        if len(spelling_issues) > 5:
                            st.markdown(f"...and {len(spelling_issues) - 5} more.")
                else:
                    st.success("No grammar or spelling issues detected!")
            except language_tool_python.utils.LanguageToolError as e:
                progress_placeholder.empty()
                animation_placeholder.empty()
                st.error("Grammar & spelling check service is currently unavailable. Please try again later.")
            except Exception as e:
                progress_placeholder.empty()
                animation_placeholder.empty()
                st.error(f"Unexpected error: {e}")

    with st.expander("📋 Rubric Input", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            rubric_input_method = st.radio("Rubric input method:", ["Text Input", "File Upload"], key="rubric_method")
        with col2:
            if rubric_input_method == "Text Input":
                rubric = st.text_area("Essay Rubric", height=100, value=st.session_state.rubric, key="rubric_input")
                st.session_state.rubric = rubric
            else:
                uploaded_rubric = st.file_uploader("Upload Rubric File", type=['txt', 'docx', 'pdf'], key="rubric_upload")
                rubric = read_uploaded_file(uploaded_rubric)
                if uploaded_rubric:
                    st.success(f"✅ Uploaded: {uploaded_rubric.name}")
                    st.session_state.rubric = rubric

    with st.expander("⚙️ Additional Instructions", expanded=False):
        extra = st.text_area("Extra Grading Instructions (optional)", height=68, 
                            placeholder="Any specific grading criteria or instructions...", 
                            value=st.session_state.extra, key="extra_input")
        st.session_state.extra = extra

    # Centered Grade button
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    grade_clicked = st.button("Grade Essay", type="primary")
    st.markdown("</div>", unsafe_allow_html=True)

    essay = st.session_state.essay
    rubric = st.session_state.rubric
    extra = st.session_state.extra

    if grade_clicked:
        if not essay or not rubric:
            st.error("Please provide both the essay and rubric.")
            return
        # Progress bar and animation
        progress_placeholder = st.empty()
        animation_placeholder = st.empty()
        import time
        progress = 0
        for i in range(10):
            progress += 10
            progress_placeholder.progress(progress, text=f"Grading... {progress}%")
            animation_placeholder.markdown(
                f"<div style='text-align:center; font-size:2em;'>🧠 <span style='animation: bounce 1s infinite;'>{'.' * ((i % 3) + 1)}</span></div>"
                "<style>@keyframes bounce {0%, 100% {transform: translateY(0);} 50% {transform: translateY(-10px);}}</style>",
                unsafe_allow_html=True
            )
            time.sleep(0.08)
        with st.spinner("Grading essay with Gemini..."):
            prompt = build_gemini_prompt(essay, rubric, extra)
            try:
                result = get_gemini_response(prompt)
                try:
                    json_result = json.loads(result)
                    grade = json_result.get("overall_grade", "N/A")
                    feedback = json_result.get("detailed_specific_feedback", "No feedback available")
                    st.session_state.grading_result = {"grade": grade, "feedback": feedback}
                except json.JSONDecodeError:
                    st.error("Error parsing AI response. Raw response:")
                    st.text(result)
            except Exception as e:
                st.error(f"Error: {e}")
        progress_placeholder.empty()
        animation_placeholder.empty()

    if st.session_state.grading_result:
        grade = st.session_state.grading_result["grade"]
        feedback = st.session_state.grading_result["feedback"]
        st.markdown("""
        <div style="text-align: center; padding: 18px 10px 10px 10px; background-color: #f0f2f6; border-radius: 12px; margin: 24px 0 10px 0;">
            <h1 style="color: #1f77b4; margin: 0;">{}</h1>
            <p style="margin: 5px 0 0 0; color: #666; font-size: 1.1em;">Overall Grade</p>
        </div>
        """.format(grade), unsafe_allow_html=True)
        # Feedback and actions in columns
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("### 📝 Feedback")
        with col2:
            copy_clicked = st.button("📋 Copy", key="copy_button")
            if copy_clicked:
                try:
                    copy_to_clipboard(grade, feedback)
                    st.success("✅ Copied!")
                except Exception as e:
                    st.error(f"Copy failed: {e}")
        st.markdown(feedback)
        # Download button centered below feedback
        st.markdown("<div style='text-align:center; margin-top: 1em;'>", unsafe_allow_html=True)
        download_text = f"Overall Grade: {grade}\n\nDetailed Feedback:\n{feedback}"
        st.download_button(
            label="📥 Download Feedback",
            data=download_text,
            file_name="essay_feedback.txt",
            mime="text/plain",
            key="download_button"
        )
        st.markdown("</div>", unsafe_allow_html=True)

def settings_page():
    import getpass
    from backend.file_utils import load_user_settings, save_user_settings
    st.title("User Settings ⚙️")
    settings_path = os.path.join(os.path.dirname(__file__), '../user_settings.json')
    settings = load_user_settings(settings_path)
    
    name = st.text_input("Your Name", value=settings.get("name", ""))
    grading_scale = st.selectbox("Preferred Grading Scale", ["A-F", "1-10", "Percentage"], index=["A-F", "1-10", "Percentage"].index(settings.get("grading_scale", "A-F")))
    default_rubric = st.text_area("Default Rubric (optional)", value=settings.get("default_rubric", ""), height=80)
    theme = st.selectbox("Theme", ["Dark Blue", "Dark Green", "Light Blue", "Light Green"], index=["Dark Blue", "Dark Green", "Light Blue", "Light Green"].index(settings.get("theme", "Dark Blue")))
    
    if st.button("Save Settings", type="primary"):
        new_settings = {
            "name": name,
            "grading_scale": grading_scale,
            "default_rubric": default_rubric,
            "theme": theme
        }
        save_user_settings(new_settings, settings_path)
        st.success("Settings saved! Please reload the app to see theme changes.")
        apply_theme()
    st.info("Settings are stored locally in user_settings.json. Theme changes require a reload.")

def grammar_spelling_database_page():
    st.title("Grammar & Spelling Database 🗂️")
    issues = load_grammar_spelling_issues()
    if not issues:
        st.info("No grammar or spelling issues have been recorded yet.")
        return
    grammar_issues = [i for i in issues if i['type'] == 'grammar']
    spelling_issues = [i for i in issues if i['type'] == 'spelling']
    st.header("Grammar Issues")
    if grammar_issues:
        for i, issue in enumerate(grammar_issues, 1):
            st.markdown(f"**{i}.** <span style='color:#e67e22'><b>{issue['text']}</b></span> (at position {issue['offset']}): {issue['message']}<br>**Suggestions:** {', '.join(issue['suggestions']) if issue['suggestions'] else 'No suggestions'}", unsafe_allow_html=True)
    else:
        st.write("No grammar issues found.")
    st.header("Spelling Issues")
    if spelling_issues:
        for i, issue in enumerate(spelling_issues, 1):
            st.markdown(f"**{i}.** <span style='color:#e74c3c'><b>{issue['text']}</b></span> (at position {issue['offset']}): {issue['message']}<br>**Suggestions:** {', '.join(issue['suggestions']) if issue['suggestions'] else 'No suggestions'}", unsafe_allow_html=True)
    else:
        st.write("No spelling issues found.")

# Navigation
PAGES = {
    "Essay Grader": main,
    "User Settings": settings_page,
    "Grammar & Spelling Database": grammar_spelling_database_page
}

def run():
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", list(PAGES.keys()))
    page = PAGES[selection]
    page()

if __name__ == "__main__":
    run() 