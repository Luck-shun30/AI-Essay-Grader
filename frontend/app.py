import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
from dotenv import load_dotenv
import json
from backend.gemini_api import build_gemini_prompt, get_gemini_response
from backend.file_utils import read_uploaded_file
from backend.clipboard_utils import copy_to_clipboard

load_dotenv()

if 'grading_result' not in st.session_state:
    st.session_state.grading_result = None
if 'essay' not in st.session_state:
    st.session_state.essay = ""
if 'rubric' not in st.session_state:
    st.session_state.rubric = ""
if 'extra' not in st.session_state:
    st.session_state.extra = ""

def main():
    st.title("AI Essay Grader ✍️")
    st.markdown("""
        <div style='margin-bottom: 1.5em;'>
        Upload or enter the student's essay, the grading rubric, and any extra grading instructions. The AI will analyze, score, and provide detailed feedback with specific quotes from the essay.
        </div>
    """, unsafe_allow_html=True)

    if not os.getenv('GEMINI_API_KEY'):
        st.error("GEMINI_API_KEY not found in environment variables. Please add it to your .env file.")
        st.stop()
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
        extra = st.text_area("Extra Grading Instructions (optional)", height=60, 
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

if __name__ == "__main__":
    main() 