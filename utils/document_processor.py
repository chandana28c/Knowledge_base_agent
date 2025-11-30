"""
Document Processor - Handles PDF and TXT file uploads and text extraction
"""

import os
from typing import List
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class DocumentProcessor:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        """
        Initialize document processor
        
        Args:
            chunk_size: Size of text chunks (characters)
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
    
    def load_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
    
    def load_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Error reading TXT: {str(e)}")
    
    def load_document(self, file_path: str) -> str:
        """Load document based on file extension"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            return self.load_pdf(file_path)
        elif file_extension == '.txt':
            return self.load_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    def process_document(self, file_path: str, filename: str) -> List[Document]:
        """
        Process document: load and split into chunks
        
        Args:
            file_path: Path to the document file
            filename: Original filename for metadata
            
        Returns:
            List of Document objects with text chunks and metadata
        """
        # Load document text
        text = self.load_document(file_path)
        
        # Split into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Create Document objects with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "source": filename,
                    "chunk_id": i,
                    "total_chunks": len(chunks)
                }
            )
            documents.append(doc)
        
        return documents
    
    def get_document_stats(self, documents: List[Document]) -> dict:
        """Get statistics about processed documents"""
        total_chunks = len(documents)
        total_chars = sum(len(doc.page_content) for doc in documents)
        sources = list(set(doc.metadata['source'] for doc in documents))
        
        return {
            "total_chunks": total_chunks,
            "total_characters": total_chars,
            "total_documents": len(sources),
            "sources": sources
        }