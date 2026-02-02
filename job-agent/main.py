import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import json
import google.generativeai as genai
import os
import ast
from apify_client import ApifyClient
from urllib.parse import quote
from dotenv import load_dotenv

# --------------------------------------------------
# 1. INITIAL CONFIG & SESSION STATE
# --------------------------------------------------
load_dotenv()

st.set_page_config(page_title="JobScout AI | IIT ISM Edition", page_icon="🤖", layout="wide")

if "step" not in st.session_state:
    st.session_state.step = "upload"
if "resume_data" not in st.session_state:
    st.session_state.resume_data = {}

# Configure Gemini
genai.configure(api_key="AIzaSyBr4yxULYf9vZgw5HlNG6yXG6zjTTpYlF8")
model = genai.GenerativeModel('gemini-2.5-flash')


# --------------------------------------------------
# 2. CORE LOGIC FUNCTIONS
# --------------------------------------------------

def get_score(row, my_skills):
    """
    Calculates a weighted match score.
    Higher priority for skills found in Title and official Skills list.
    """
    score = 0
    title = str(row.get("title", "")).lower()
    description = str(row.get("descriptionText", "")).lower()

    # Official Skill tags from scraper
    job_skills = row.get("clean_skills", [])
    if not isinstance(job_skills, list):
        job_skills = []
    job_skills_text = " ".join([str(s) for s in job_skills]).lower()

    for skill in my_skills:
        s_lower = str(skill).lower()
        # High Priority: Title Match
        if s_lower in title:
            score += 10
        # Medium Priority: LinkedIn Skill Tag Match
        if s_lower in job_skills_text:
            score += 5
        # Lower Priority: Found in description prose
        elif s_lower in description:
            score += 2

    return score


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


def run_scout_api(job_title, location):
    token = os.getenv("APIFY_TOKEN")
    if not token:
        raise ValueError("APIFY_TOKEN not found in .env file.")

    client = ApifyClient(token)
    search_url = f"https://www.linkedin.com/jobs/search/?keywords={quote(job_title)}&location={quote(location)}"

    run_input = {
        "cookies": [
            {"domain": ".linkedin.com", "name": "li_at", "value": os.getenv("LI_AT_COOKIE")},
            {"domain": ".www.linkedin.com", "name": "JSESSIONID",
             "value": os.getenv("JSESSIONID_VALUE", "").replace('"', '')}
        ],
        "searchUrl": search_url,
        "userAgent": os.getenv("USER_AGENT",
                               "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"),
        "count": 15,
        "scrapeCompany": True,
        "scrapeSkills": True,
        "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]}
    }

    run = client.actor("curious_coder/linkedin-jobs-search-scraper").call(run_input=run_input)

    if "Failed to authorize" in run.get("statusMessage", ""):
        raise Exception("LinkedIn detected the bot. Wait 15 mins and refresh cookies.")

    jobs = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    df = pd.DataFrame(jobs)
    df.to_csv("found_jobs.csv", index=False)
    return df


# --------------------------------------------------
# 3. HELPERS & CSS
# --------------------------------------------------
def safe_parse(val, key=None):
    if pd.isna(val) or val == "": return {} if key else []
    try:
        data = ast.literal_eval(val)
        if key and isinstance(data, dict): return data.get(key, "N/A")
        return data
    except:
        return val


def get_workplace_safe(val):
    parsed = safe_parse(val)
    if isinstance(parsed, list) and len(parsed) > 0:
        return parsed[0].get("localizedName", "On-site")
    return "On-site"


@st.cache_data
def load_and_clean_data():
    if not os.path.exists("found_jobs.csv"): return None
    df = pd.read_csv("found_jobs.csv")

    cols = df.columns
    df["clean_location"] = df["location"].apply(
        lambda x: safe_parse(x, "defaultLocalizedName")) if "location" in cols else "India"
    df["clean_salary"] = df["salary"].apply(
        lambda x: safe_parse(x, "formattedBaseSalary")) if "salary" in cols else "Competitive"
    df["clean_skills"] = df["skills"].apply(lambda x: safe_parse(x)) if "skills" in cols else [[] for _ in
                                                                                               range(len(df))]
    df["workplace"] = df["jobWorkplaceTypes"].apply(get_workplace_safe) if "jobWorkplaceTypes" in cols else "On-site"

    df["clean_salary"] = df["clean_salary"].replace("N/A", "Competitive")
    return df


st.markdown("""
<style>
.stApp { background: #0b1220; color: #e5e7eb; }
.job-card { background: #111827; padding: 26px; border-radius: 16px; border: 1px solid #1f2937; margin-bottom: 22px; }
.job-title { font-size: 1.35rem; font-weight: 700; color: #f8fafc; margin-bottom: 10px; }
.skill-tag { display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: 0.75rem; margin: 4px; color: #38bdf8; border: 1px solid #38bdf8; background: rgba(56, 189, 248, 0.1); }
.match-tag { background: #1e3a8a !important; color: #60a5fa !important; border: 1px solid #60a5fa !important; font-weight: bold; }
.apply-btn a { display: inline-block; background: #0ea5e9; color: white !important; padding: 10px 22px; border-radius: 10px; text-decoration: none; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# 4. APP FLOW
# --------------------------------------------------

if st.session_state.step == "upload":
    st.markdown("# 📄 Upload Resume")
    uploaded_file = st.file_uploader("Upload IIT (ISM) Student PDF", type="pdf")
    if uploaded_file:
        if st.button("Analyze & Start Scout"):
            with st.spinner("Gemini is parsing your resume..."):
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                text = "".join([page.get_text() for page in doc])
                st.session_state.resume_data = extract_with_llm(text)
                st.session_state.step = "scout"
                st.rerun()

elif st.session_state.step == "scout":
    res = st.session_state.resume_data
    st.markdown(f"# 🚀 Scouting for {res.get('target_role')}")
    st.write(f"Location focus: **{res.get('preferred_location')}**")
    if st.button("Start Scraping"):
        with st.spinner("Running LinkedIn Scraper..."):
            try:
                run_scout_api(res.get("target_role"), res.get("preferred_location"))
                st.cache_data.clear()
                st.session_state.step = "dashboard"
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

elif st.session_state.step == "dashboard":
    raw_df = load_and_clean_data()
    if raw_df is None:
        st.error("No jobs data found.");
        st.button("Restart", on_click=lambda: st.session_state.update({"step": "upload"}))
    else:
        st.markdown(f"# 🤖 JobScout <span style='color:#38bdf8'>AI</span>", unsafe_allow_html=True)
        st.info(f"Verified for {st.session_state.resume_data.get('name')} | IIT (ISM) Dhanbad")

        with st.sidebar:
            st.header("⚙️ Filter Engine")
            extracted_skills = st.session_state.resume_data.get("skills", [])
            my_skills = st.multiselect("Match these skills:",
                                       options=list(set(extracted_skills + ["C++", "CUDA", "Python", "ML"])),
                                       default=extracted_skills[:8])
            selected_workplace = st.selectbox("Workplace", ["All", "Remote", "On-site", "Hybrid"])

        df = raw_df.copy()
        if selected_workplace != "All":
            df = df[df["workplace"] == selected_workplace]

        # Score and Sort
        df["match_score"] = df.apply(lambda row: get_score(row, my_skills), axis=1)
        df = df.sort_values("match_score", ascending=False)

        # KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Leads", len(df))
        c2.metric("Best Matches", len(df[df["match_score"] > 5]))
        c3.metric("Remote Roles", len(df[df["workplace"] == "Remote"]) if "workplace" in df.columns else 0)

        # Job List Render
        for _, row in df.iterrows():
            # Find which of OUR skills are in THIS job
            job_text = (str(row["title"]) + " " + " ".join([str(s) for s in row["clean_skills"]]) + " " + str(
                row.get("descriptionText", ""))).lower()
            found_matches = [s for s in my_skills if str(s).lower() in job_text]

            # Card UI
            border = "border: 1px solid #0ea5e9;" if row["match_score"] > 5 else "border: 1px solid #1f2937;"
            st.markdown(f"<div class='job-card' style='{border}'>", unsafe_allow_html=True)

            col_logo, col_info = st.columns([1, 7])
            with col_logo:
                logo = row["companyLogo"] if pd.notna(
                    row["companyLogo"]) else "https://via.placeholder.com/80/111827/38bdf8?text=JOB"
                st.image(logo, width=75)

            with col_info:
                st.markdown(f"<div class='job-title'>{row['title']}</div>", unsafe_allow_html=True)
                st.markdown(f"**🏢 {row['companyName']}** | 📍 {row['clean_location']} | 💼 {row['workplace']}")

                # 1. SHOW MATCHED SKILLS (Our skills the company wants)
                if found_matches:
                    match_html = "".join([f"<span class='skill-tag match-tag'>⭐ {m}</span>" for m in found_matches])
                    st.markdown(f"**Your Matched Skills:**<br>{match_html}", unsafe_allow_html=True)

                # 2. SHOW COMPANY SKILL TAGS (Official LinkedIn tags)
                company_skills = [s for s in row['clean_skills'] if s not in found_matches]
                if company_skills:
                    comp_html = "".join([f"<span class='skill-tag'>{s}</span>" for s in company_skills[:5]])
                    st.markdown(f"**Other Company Tags:**<br>{comp_html}", unsafe_allow_html=True)

                # 3. SHOW DESCRIPTION SNIPPET
                with st.expander("📝 View Job Requirements & Description"):
                    st.write(str(row.get("descriptionText", "No description provided."))[:1000] + "...")

                st.markdown(
                    f"<div class='apply-btn' style='margin-top:15px'><a href='{row['link']}' target='_blank'>INITIATE APPLICATION</a></div>",
                    unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)