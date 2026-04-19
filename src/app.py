# import streamlit as st
# from rag_pipeline import RAGPipeline

# st.set_page_config(page_title="RAG Chat", layout="wide")

# st.title("📄 RAG Chat with PDF")

# uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
# # Load pipeline once
# @st.cache_resource
# def load_pipeline():
#     pipeline = RAGPipeline()
#     pipeline.load()
#     return pipeline

# pipeline = None

# if uploaded_file is not None:
#     with open("temp.pdf", "wb") as f:
#         f.write(uploaded_file.read())

#     pipeline = load_pipeline()

#     # Re-ingest with new file
#     with st.spinner("Processing PDF..."):
#         pipeline.ingest("temp.pdf")

#     st.success("PDF processed! You can now ask questions.")

# # Chat history
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # Show chat history
# for msg in st.session_state.messages:
#     with st.chat_message(msg["role"]):
#         st.markdown(msg["content"])

# # Input
# if pipeline is not None and (prompt := st.chat_input("Ask a question from your document...")):

#     # User message
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     # Assistant response
#     with st.chat_message("assistant"):
#         with st.spinner("Thinking..."):
#             result = pipeline.query(prompt)

#             answer = result["answer"]
#             sources = result["sources"]

#             st.markdown(answer)

#             # Show sources
#             with st.expander("📎 Sources"):
#                 for s in sources:
#                     st.write(f"Page {s['page']}: {s['content'][:150]}...")

#     # Save assistant message
#     st.session_state.messages.append({
#         "role": "assistant",
#         "content": answer
#     })

import streamlit as st
from rag_pipeline import RAGPipeline

st.set_page_config(page_title="RAG Chat", layout="wide")

# ---------- HEADER ----------
st.markdown(
    """
    <h1 style='text-align: center;'>📄 RAG Chat with PDF</h1>
    <p style='text-align: center; color: gray;'>
        Ask questions from any PDF using AI
    </p>
    """,
    unsafe_allow_html=True
)

# ---------- LAYOUT (BENTO STYLE) ----------
col1, col2 = st.columns([1, 2])  # left small, right big

# ---------- LEFT PANEL ----------
with col1:
    st.subheader("📂 Upload Document")

    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

    st.markdown("---")

    st.subheader("📊 Status")

    if "pdf_uploaded" not in st.session_state:
        st.session_state.pdf_uploaded = False

    if st.session_state.pdf_uploaded:
        st.success("✅ PDF Loaded")
    else:
        st.warning("⚠️ No PDF uploaded")

    st.markdown("---")

    st.subheader("💡 Tips")
    st.markdown("""
    - Ask specific questions  
    - Try: *"Summarize this document"*  
    - Use follow-up questions  
    """)

# ---------- PIPELINE ----------
@st.cache_resource
def load_pipeline():
    pipeline = RAGPipeline()
    pipeline.load()
    return pipeline

pipeline = None

# ---------- PROCESS PDF ----------
if uploaded_file is not None:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.read())

    pipeline = load_pipeline()

    with st.spinner("🔄 Processing PDF..."):
        pipeline.ingest("temp.pdf")

    st.session_state.pdf_uploaded = True
    st.success("✅ PDF processed! Start chatting →")

# ---------- RIGHT PANEL (CHAT) ----------
with col2:
    st.subheader("💬 Chat")

    # Chat memory
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Show chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    if pipeline is not None and (prompt := st.chat_input("Ask something about your document...")):

        # Save user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        # Assistant response
        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking..."):
                result = pipeline.query(prompt)

                answer = result["answer"]
                sources = result["sources"]

                st.markdown(answer)

                # Sources (clean card style)
                with st.expander("📎 Sources"):
                    for s in sources:
                        st.markdown(
                            f"""
                            <div style="padding:10px; border-radius:10px; background:#f5f5f5; margin-bottom:8px;">
                                <b>Page {s['page']}</b><br>
                                {s['content'][:150]}...
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

        # Save assistant message
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })