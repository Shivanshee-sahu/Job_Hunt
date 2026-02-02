import streamlit as st
import fitz  # PyMuPDF
import json
import google.generativeai as genai
import subprocess

# Securely configure Gemini
genai.configure(api_key="AIzaSyCeZgSGOlUBej68l9DNvnxh-W8zBnYrGRw")
model = genai.GenerativeModel('gemini-2.5-flash')

def extract_with_llm(resume_text):
    prompt = f"""
    Extract information from the resume text and return ONLY a valid JSON object.
    Structure:
    {{
      "name": "Full Name",
      "target_role": "Likely Role (e.g. Software Engineer CUDA)",
      "preferred_location": "India",
      "skills": ["Skill1", "Skill2"]
    }}
    Resume Text: {resume_text}
    """
    response = model.generate_content(prompt)
    clean_json = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(clean_json)

st.title("📄 Resume Analysis & Job Scout")

uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf")

if uploaded_file:
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    full_text = "".join([page.get_text() for page in doc])

    if st.button("Step 1: Extract Skills"):
        with st.spinner("Analyzing with Gemini..."):
            data = extract_with_llm(full_text)
            with open("resume.json", "w") as f:
                json.dump(data, f, indent=2)
            st.success("Resume data saved to resume.json!")
            st.json(data)

    if st.button("Step 2: Run Job Scout (Apify)"):
        with st.spinner("Scraping LinkedIn... this may take a minute."):
            # Trigger your scout.py script
            process = subprocess.run(["python", "scout.py"], capture_output=True, text=True)
            if process.returncode == 0:
                st.success("Scrape complete! Open 'main.py' to see results.")
            else:
                st.error(f"Scout Error: {process.stderr}")