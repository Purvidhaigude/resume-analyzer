
import streamlit as st
import os
import google.generativeai as genai
import plotly.graph_objects as go
import fitz  # 🔹 PyMuPDF

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# ---------------------- Gemini Response ----------------------
def get_gemini_response(prompt, pdf_content=None, job_desc=""):
    model = genai.GenerativeModel("gemini-1.5-flash")

    parts = []
    if job_desc:
        parts.append(f"Job Description:\n{job_desc}")
    if pdf_content:
        parts.append(pdf_content[0])   # ab ye text hai
    parts.append(prompt)

    response = model.generate_content(parts)
    return response.text


# ---------------------- PDF Setup (PyMuPDF) ----------------------
def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        pdf_text = ""
        for page in pdf_document:
            text = page.get_text("text")   # har page ka text nikalna
            pdf_text += text + "\n"
        return [pdf_text] if pdf_text.strip() else None
    else:
        return None


# ---------------------- Streamlit UI ----------------------
st.set_page_config(page_title="ATS Resume Expert + Chatbot", page_icon="🤖", layout="wide")

st.title("📄 ATS Resume Expert + 🤖 Chatbot")
st.caption("Analyze your resume & chat with AI (English or Simple Language)")

# Job description + resume upload
job_desc = st.text_area("📝 Job Description", key="jobdesc")
uploaded_file = st.file_uploader("📂 Upload your Resume (PDF)", type=["pdf"])

if uploaded_file is not None:
    st.success("✅ PDF Uploaded Successfully!")

# ---------------------- Buttons ----------------------
col1, col2 = st.columns(2)
with col1:
    submit1 = st.button("🔍 Tell Me About the Resume")
with col2:
    submit2 = st.button("📊 Percentage Match & Missing Skills")

# Prompts for buttons
input_prompt1 = """
You are an experienced Technical Human Resource Manager. 
Review the resume against the job description and give strengths & weaknesses.
"""

input_prompt2 = """
You are an ATS system. 
Evaluate the resume vs job description. 
Give percentage match, missing keywords, and improvement tips.
"""

# ---------------------- Button Logic ----------------------
if submit1:
    if uploaded_file:
        pdf_content = input_pdf_setup(uploaded_file)
        response = get_gemini_response(input_prompt1, pdf_content, job_desc)
        st.subheader("📝 Resume Analysis")
        st.write(response)
    else:
        st.warning("⚠️ Please upload your resume.")

elif submit2:
    if uploaded_file:
        pdf_content = input_pdf_setup(uploaded_file)
        response = get_gemini_response(input_prompt2, pdf_content, job_desc)

        # Extract percentage if available
        try:
            percent = int([s for s in response.split() if "%" in s][0].replace("%", ""))
        except:
            percent = 75

        # Gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=percent,
            title={'text': "ATS Match %"},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "purple"}}
        ))
        st.plotly_chart(fig)

        st.subheader("📊 Detailed ATS Report")
        st.write(response)
    else:
        st.warning("⚠️ Please upload your resume.")

# ---------------------- Chatbot ----------------------
st.markdown("---")
st.header("💬 Chat with Resume Coach")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User query
if user_input := st.chat_input("Ask you'r question..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Decide style based on query
    if "own language" in user_input.lower() or "simple" in user_input.lower():
        style_prompt = """
        You are a friendly mentor. 
        Answer in **very simple human language** (like talking to a friend). 
        Avoid technical terms. End with 2-3 bullet point summary.
        """
    else:
        style_prompt = """
        You are a professional career advisor. 
        Answer in **formal English**, structured and clear. 
        End with a short summary in bullet points.
        """

    pdf_context = input_pdf_setup(uploaded_file) if uploaded_file else None
    ai_response = get_gemini_response(f"{style_prompt}\nUser Query: {user_input}", pdf_context, job_desc)

    with st.chat_message("assistant"):
        st.markdown(ai_response)

    st.session_state.messages.append({"role": "assistant", "content": ai_response})
