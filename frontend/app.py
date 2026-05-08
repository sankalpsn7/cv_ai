import streamlit as st
import requests
import pandas as pd



st.set_page_config(page_title="AI HR Assistant", page_icon="📄", layout="wide")



# Pointing to your default dev port
API_BASE_URL = "http://localhost:5000"

st.title("📄 AI Resume Analyzer & ATS")
st.markdown("Upload resumes and a Job Description to generate ATS scores, gap analyses, and interview questions.")

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "analysis_attempted" not in st.session_state:
    st.session_state.analysis_attempted = False


# Layout: Split into two columns for a clean, minimalist look
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Job Setup")
    job_description = st.text_area("Paste Job Description Here", height=200)
    
    st.subheader("2. Candidate Resumes")
    uploaded_files = st.file_uploader("Upload PDF Resumes", type=["pdf"], accept_multiple_files=True)
    
    analyze_button = st.button("Analyze Candidates", type="primary")

with col2:
    st.subheader("Analysis Results")
    


    if analyze_button:
        if not job_description or not uploaded_files:
            st.warning("Please provide both a Job Description and at least one Resume.")
        else:
            st.session_state.analysis_results = None  # ← clear old results immediately
            st.session_state.analysis_attempted = False
            with st.spinner("Analyzing resumes..."):
                files_payload = [
                    ("files", (file.name, file.getvalue(), "application/pdf")) 
                    for file in uploaded_files
                ]
                data_payload = {"job_description": job_description}
                
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/analyze_batch", 
                        data=data_payload, 
                        files=files_payload
                    )
                    
                    if response.status_code == 200:
                        # Update the session state with the new results
                        st.session_state.analysis_results = response.json().get("results", [])
                        st.session_state.analysis_attempted = True
                        st.session_state.messages = []
                    else:
                        st.error(f"Backend Error: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"Failed to connect to backend: {e}")

    # Render results OUTSIDE the button click logic so they persist
    
    if st.session_state.analysis_results:
        sorted_results = sorted(
            st.session_state.analysis_results, 
            key=lambda x: x['ats_match_score'], 
            reverse=True
        )
        
        # Quick ranking table
        st.markdown("#### 🏆 Candidate Ranking")
        for i, c in enumerate(sorted_results):
            score = c['ats_match_score']
            color = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
            st.write(f"{i+1}. {color} **{c['candidate_name']}** — {score}%")
        
            # CSV DOWNLOAD BUTTON
        df = pd.DataFrame([{
            "Candidate": c['candidate_name'],
            "ATS Score": c['ats_match_score'],
            "Top Strength": c['strengths'][0] if c['strengths'] else "",
            "Key Red Flag": c['red_flags'][0] if c['red_flags'] else ""
        } for c in sorted_results])

        st.download_button(
            "📥 Download Results as CSV",
            df.to_csv(index=False),
            "ats_results.csv",
            "text/csv"
        )

        st.divider()
        # then render expanders using sorted_results
    if st.session_state.analysis_results:
        for idx, candidate in enumerate(sorted_results):
            with st.expander(f"🧑‍💻 {candidate['candidate_name']} - Match: {candidate['ats_match_score']}%", expanded=(idx==0)):
                st.metric("ATS Match Score", f"{candidate['ats_match_score']}%")
                st.markdown("### 🌟 Strengths")
                for strength in candidate['strengths']:
                    st.write(f"✅ {strength}")
                st.markdown("### ⚠️ Missing Skills / Red Flags")
                for flag in candidate['red_flags']:
                    st.write(f"🚩 {flag}")
                st.markdown("### ❓ Recommended Interview Questions")
                for q in candidate['interview_questions']:
                    st.write(f"- {q}")


            
    elif st.session_state.analysis_attempted:
        st.info("No results found. Please check the job description and try again.")
    else:
        # Clean default state before any interaction
        st.write("Upload resumes and click Analyze to see results here.")

st.divider()

# --- RAG CHAT INTERFACE ---
st.subheader("💬 Chat with Candidate CVs (RAG)")
st.markdown("Ask specific questions across all analyzed resumes.")

# Initialize chat history in Streamlit session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("e.g., Which candidate has experience with PostgreSQL?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call the FastAPI Chat Endpoint
    with st.chat_message("assistant"):
        with st.spinner("Searching resumes..."):
            try:
                chat_response = requests.post(
                    f"{API_BASE_URL}/chat_cv",
                    json={"query": prompt}
                )
                if chat_response.status_code == 200:
                    answer = chat_response.json().get("answer", "No answer generated.")
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error("Error querying the RAG system.")
            except Exception as e:
                st.error(f"Connection error: {e}")