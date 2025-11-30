"""
Vector Store Manager - Handles FAISS operations with Ollama embeddings (100% LOCAL & FREE)
"""

import os
from typing import List, Optional
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings

class VectorStoreManager:
    def __init__(self, persist_directory: str = "./data/vectorstore"):
        """
        Initialize vector store manager with FAISS and Ollama embeddings (LOCAL & FREE)
        
        Args:
            persist_directory: Directory to store FAISS data
        """
        self.persist_directory = persist_directory
        self.index_file = os.path.join(persist_directory, "faiss_index")
        self.vectorstore = None
        
        # Use Ollama's LOCAL embeddings (no API needed!)
        print("Initializing Ollama embeddings...")
        self.embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url="http://localhost:11434"
        )
        print("✅ Embeddings ready!")
        
        # Create directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Try to load existing vectorstore
        self.load_vectorstore()
    
    def load_vectorstore(self):
        """Load existing vectorstore if available"""
        try:
            if os.path.exists(f"{self.index_file}.faiss"):
                self.vectorstore = FAISS.load_local(
                    self.index_file,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print(f"✅ Loaded existing vectorstore")
            else:
                print("📝 No existing vectorstore found. Will create new one.")
        except Exception as e:
            print(f"⚠️ Could not load vectorstore: {str(e)}")
            self.vectorstore = None
    
    def add_documents(self, documents: List[Document]) -> bool:
        """
        Add documents to vector store
        
        Args:
            documents: List of Document objects to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Processing {len(documents)} documents...")
            
            if self.vectorstore is None:
                # Create new vectorstore
                print(f"Creating new vectorstore...")
                self.vectorstore = FAISS.from_documents(
                    documents=documents,
                    embedding=self.embeddings
                )
                print(f"✅ Created vectorstore with {len(documents)} document chunks")
            else:
                # Add to existing vectorstore
                print(f"Adding to existing vectorstore...")
                self.vectorstore.add_documents(documents)
                print(f"✅ Added {len(documents)} document chunks")
            
            # Save vectorstore
            self.vectorstore.save_local(self.index_file)
            print(f"✅ Vectorstore saved")
            
            return True
        except Exception as e:
            import traceback
            print(f"❌ Error adding documents: {str(e)}")
            print(f"Full error: {traceback.format_exc()}")
            return False
    
    def search(self, query: str, k: int = 4) -> List[Document]:
        """Search for relevant documents"""
        if self.vectorstore is None:
            print("⚠️ Vectorstore is None, cannot search")
            return []
        
        try:
            results = self.vectorstore.similarity_search(query, k=k)
            return results
        except Exception as e:
            print(f"❌ Error searching: {str(e)}")
            return []
    
    def search_with_score(self, query: str, k: int = 4) -> List[tuple]:
        """Search for relevant documents with relevance scores"""
        if self.vectorstore is None:
            return []
        
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            return results
        except Exception as e:
            print(f"❌ Error searching: {str(e)}")
            return []
    
    def get_retriever(self, k: int = 4):
        """Get a retriever object for use with chains"""
        if self.vectorstore is None:
            print("⚠️ Vectorstore is None, cannot create retriever")
            return None
        
        return self.vectorstore.as_retriever(
            search_kwargs={"k": k}
        )
    
    def clear_vectorstore(self):
        """Clear all documents from vectorstore"""
        try:
            self.vectorstore = None
            
            import shutil
            if os.path.exists(self.persist_directory):
                shutil.rmtree(self.persist_directory)
                os.makedirs(self.persist_directory, exist_ok=True)
            
            print("✅ Vectorstore cleared successfully")
            return True
        except Exception as e:
            print(f"❌ Error clearing vectorstore: {str(e)}")
            return False
    
    def get_stats(self) -> dict:
        """Get vectorstore statistics"""
        if self.vectorstore is None:
            return {"total_documents": 0, "status": "empty"}
        
        try:
            count = self.vectorstore.index.ntotal
            return {"total_documents": count, "status": "active"}
        except Exception as e:
            print(f"Error getting stats: {str(e)}")
            return {"total_documents": 0, "status": "unknown"}