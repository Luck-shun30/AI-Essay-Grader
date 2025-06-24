import pyperclip

def copy_to_clipboard(grade, feedback):
    clipboard_text = f"Overall Grade: {grade}\n\nDetailed Feedback:\n{feedback}"
    pyperclip.copy(clipboard_text) 