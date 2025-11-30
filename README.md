# 🧠 Knowledge Base Agent — Full Local RAG AI  
**Category:** Business Operations — Knowledge Base Assistant  
**Project Type:** Offline Local AI with Document Intelligence  
**LLM:** Llama 3.2 (via Ollama)  
**Challenge:** AI Agent Development Challenge — 48 Hours  
**Organization:** Rooman Technologies  

---

## 👤 Developer Information
**Student Name:** _Chandana L R_  
**College:** Adichunchanagiri Institute of Technology, Chikkamagaluru  
**Department:** Computer Science and Engineering  
**Submission Date:** _30 Nov 2025_

---

## 📌 Overview

The **Knowledge Base Agent** allows organizations to upload multiple documents (PDF, DOCX, TXT) related to:

✔ HR Policies  
✔ Employee Handbook  
✔ SOP Guidelines  
✔ IT Support Manuals  
✔ Project Documentation  

The agent then answers queries **based only on the uploaded data** using **RAG (Retrieval-Augmented Generation)**.  
This ensures:

| Benefit | Reason |
|--------|--------|
| Highly Accurate Answers | Grounded in real company documents |
| No Hallucination | Provides source references |
| Fully Offline | No cloud or API dependency |
| Secure & Private | Suitable for internal enterprise data |



### 1. Cloud Demo (Deployed)
- **Live URL:** [https://your-app.streamlit.app](your-url)
- **File:** `simple_app.py`
- **Speed:** Instant responses (2-3 seconds)
- **Deployment:** Streamlit Cloud
- **Best for:** Quick testing without any setup



## 🧠 AI Architecture


flowchart TD
    User[User Query] --> UI[Streamlit Chat Interface]
    UI --> Retriever[Vector Store Retrieval]
    Retriever --> Evidence[Relevant Knowledge Chunks]
    Evidence --> LLM[Llama 3.2 (Local via Ollama)]
    LLM --> Response[Answer + Source References]
    Response --> UI
    Docs[Uploaded Documents] --> Embedding[Embeddings Generator] --> VectorStore[ChromaDB/FAISS]
    VectorStore --> Retriever
