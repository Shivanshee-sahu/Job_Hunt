# 🤖 JobScout AI: IIT (ISM) Edition  
### An AI-Powered Job Scouting & Resume-Matching Pipeline

JobScout AI is a specialized recruitment tool designed to bridge the gap between **academic resumes** and **industry job requirements**.  
It automates the process of extracting skills from a PDF resume, scouting relevant job opportunities on LinkedIn, and ranking those jobs using a **weighted matching algorithm**.

---

## 🚀 Features

### 📄 PDF Resume Parsing
- Extracts high-fidelity **technical skills**, **target roles**, and **preferred locations**
- Powered by **PyMuPDF (fitz)** and **Google Gemini 1.5 Flash**

### 🔍 LinkedIn Job Scouting
- Uses **Apify’s LinkedIn Scraper** to fetch live job listings
- Handles bot detection using **residential proxies** and **session management**

### ⚖️ Weighted Match Engine
Custom scoring algorithm based on relevance:

- **Title Match (High Weight)**  
  Skills appearing directly in the job title

- **Skill Tags (Medium Weight)**  
  Matches against company-listed requirements

- **Description Scanning (Low Weight)**  
  Contextual skill matching within job descriptions

### 📊 Interactive Dashboard
- Built with **Streamlit (dark mode UI)**
- KPIs, skill-gap analysis, and direct job application links

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit  
- **LLM:** Google Gemini API  
- **Scraping API:** Apify Client  
- **Data Processing:** Pandas, NumPy  
- **PDF Processing:** PyMuPDF (fitz)  
- **Environment:** Python 3.10+

---

## ⚙️ Setup & Installation

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/job-scout-ai.git
cd job-scout-ai
## ⚙️ Setup & Installation

### 2️⃣ Install Dependencies
Install all required Python packages using:

```bash
pip install -r requirements.txt

###3️⃣Configure Environment Variables
Create a .env file in the root directory of the project and add the following keys:

APIFY_TOKEN=your_apify_token
GEMINI_API_KEY=your_google_gemini_key
LI_AT_COOKIE=your_linkedin_li_at_cookie
JSESSIONID_VALUE=your_linkedin_jsessionid
USER_AGENT=your_browser_user_agent
```
##🖥️ Usage

Launch the Streamlit application:
streamlit run main.py

##🔄 Workflow

Upload Resume
Upload your PDF resume. The system extracts and structures technical skills, roles, and preferences.

Start Scout
Initiates LinkedIn job scraping based on the extracted role and location.

Analyze Matches
View a ranked list of job opportunities with:

Company skill requirements

Your matched skills

Overall match score

##📊 Logic & Architecture

The system follows a linear, state-driven pipeline:

🔹 Extraction
Google Gemini converts unstructured resume text into a structured JSON profile.

🔹 Scouting
The extracted role and location are injected into LinkedIn search queries to fetch relevant job listings.

🔹 Ranking
Each job is scored using a weighted matching algorithm, and results are ranked based on a computed match_score in a Pandas DataFrame.
