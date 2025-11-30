"""
Knowledge Base Agent - Main Streamlit Application
"""

import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime
import json

# Import our custom modules
from utils.document_processor import DocumentProcessor
from utils.vector_store import VectorStoreManager
from utils.qa_chain import QAChain

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Knowledge Base Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .confidence-high {
        color: #28a745;
        font-weight: bold;
    }
    .confidence-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .confidence-low {
        color: #dc3545;
        font-weight: bold;
    }
    .source-box {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'total_queries' not in st.session_state:
    st.session_state.total_queries = 0

if 'query_log' not in st.session_state:
    st.session_state.query_log = []

if 'vectorstore_manager' not in st.session_state:
    st.session_state.vectorstore_manager = VectorStoreManager()

if 'doc_processor' not in st.session_state:
    st.session_state.doc_processor = DocumentProcessor()

if 'qa_chain' not in st.session_state:
    st.session_state.qa_chain = None

# Helper Functions
def initialize_qa_chain():
    """Initialize QA chain with retriever"""
    retriever = st.session_state.vectorstore_manager.get_retriever(k=4)
    if retriever:
        st.session_state.qa_chain = QAChain(retriever)
        return True
    return False

def save_uploaded_file(uploaded_file):
    """Save uploaded file to disk"""
    upload_dir = "./data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

def log_query(question, answer, confidence):
    """Log query for analytics"""
    st.session_state.query_log.append({
        "question": question,
        "answer": answer[:100] + "..." if len(answer) > 100 else answer,
        "confidence": confidence,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    st.session_state.total_queries += 1

# Main App
def main():
    # Header
    st.markdown('<p class="main-header">🤖 Knowledge Base Agent</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Document Management")
        
        # File Upload
        uploaded_files = st.file_uploader(
            "Upload Documents (PDF or TXT)",
            type=['pdf', 'txt'],
            accept_multiple_files=True,
            help="Upload documents to build your knowledge base"
        )
        
        if uploaded_files:
            if st.button("📤 Process Documents", type="primary"):
                with st.spinner("Processing documents..."):
                    all_documents = []
                    
                    for uploaded_file in uploaded_files:
                        try:
                            # Save file
                            file_path = save_uploaded_file(uploaded_file)
                            
                            # Process document
                            documents = st.session_state.doc_processor.process_document(
                                file_path, 
                                uploaded_file.name
                            )
                            all_documents.extend(documents)
                            
                            st.success(f"✅ {uploaded_file.name} processed!")
                        
                        except Exception as e:
                            st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                    
                    # Add to vector store
                    if all_documents:
                        success = st.session_state.vectorstore_manager.add_documents(all_documents)
                        
                        if success:
                            st.success(f"🎉 Added {len(all_documents)} chunks to knowledge base!")
                            
                            # Initialize QA chain
                            if initialize_qa_chain():
                                st.success("✅ Agent ready to answer questions!")
                        else:
                            st.error("❌ Failed to add documents to knowledge base")
        
        st.markdown("---")
        
        # Vector Store Stats
        st.header("📊 Knowledge Base Stats")
        stats = st.session_state.vectorstore_manager.get_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Chunks", stats['total_documents'])
        with col2:
            st.metric("Total Queries", st.session_state.total_queries)
        
        # Clear Knowledge Base
        st.markdown("---")
        if st.button("🗑️ Clear Knowledge Base", type="secondary"):
            if st.session_state.vectorstore_manager.clear_vectorstore():
                st.session_state.messages = []
                st.session_state.qa_chain = None
                st.success("Knowledge base cleared!")
                st.rerun()
        
        # Analytics
        if st.session_state.query_log:
            st.markdown("---")
            st.header("📈 Recent Queries")
            
            # Show last 5 queries
            for query in st.session_state.query_log[-5:][::-1]:
                with st.expander(f"❓ {query['question'][:50]}..."):
                    st.write(f"**Answer:** {query['answer']}")
                    st.write(f"**Confidence:** {query['confidence']}")
                    st.write(f"**Time:** {query['timestamp']}")
    
    # Main Chat Interface
    st.header("💬 Chat with your Knowledge Base")
    
    # Check if agent is ready
    if st.session_state.qa_chain is None:
        stats = st.session_state.vectorstore_manager.get_stats()
        
        if stats['total_documents'] > 0:
            # Try to initialize QA chain
            if initialize_qa_chain():
                st.success("✅ Agent initialized and ready!")
            else:
                st.warning("⚠️ Could not initialize agent. Please upload documents first.")
        else:
            st.info("👈 Upload documents in the sidebar to get started!")
            st.stop()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            # Display sources if available
            if message["role"] == "assistant" and "sources" in message:
                if message["sources"]:
                    st.markdown("**📚 Sources:**")
                    for source in message["sources"]:
                        with st.expander(f"📄 {source['name']}"):
                            st.write(source['preview'])
                
                # Display confidence
                if "confidence" in message:
                    confidence = message["confidence"]
                    confidence_class = f"confidence-{confidence}"
                    st.markdown(
                        f"**Confidence:** <span class='{confidence_class}'>{confidence.upper()}</span>",
                        unsafe_allow_html=True
                    )
    
    # Chat input
    if question := st.chat_input("Ask a question about your documents..."):
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": question
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(question)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.qa_chain.ask(question)
                
                answer = response['answer']
                sources = response['sources']
                confidence = response['confidence']
                
                # Display answer
                st.write(answer)
                
                # Display sources
                if sources:
                    st.markdown("**📚 Sources:**")
                    for source in sources:
                        with st.expander(f"📄 {source['name']}"):
                            st.write(source['preview'])
                
                # Display confidence
                confidence_class = f"confidence-{confidence}"
                st.markdown(
                    f"**Confidence:** <span class='{confidence_class}'>{confidence.upper()}</span>",
                    unsafe_allow_html=True
                )
                
                # Add assistant message to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "confidence": confidence
                })
                
                # Log query
                log_query(question, answer, confidence)

if __name__ == "__main__":
    # Just run the app - Ollama connection will be tested when needed
    main()