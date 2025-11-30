"""
QA Chain - Question Answering using Ollama (100% LOCAL & FREE)
"""

from typing import Dict, List
from langchain_community.llms import Ollama
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_core.prompts import PromptTemplate

class QAChain:
    def __init__(self, retriever, model_name: str = "llama3.2", temperature: float = 0):
        """
        Initialize QA Chain with Ollama (LOCAL & FREE)
        
        Args:
            retriever: Vector store retriever
            model_name: Ollama model to use
            temperature: Model temperature
        """
        self.retriever = retriever
        # Use Ollama running locally
        self.llm = Ollama(
            model=model_name,
            temperature=temperature,
            base_url="http://localhost:11434"
        )
        
        self.prompt_template = """You are a helpful AI assistant answering questions based on company documents.

Use the following pieces of context to answer the question at the end. 
If you don't know the answer or if the information is not in the context, just say "I don't have enough information to answer this question based on the provided documents." Don't try to make up an answer.

Always cite the source document when providing an answer.

Context:
{context}

Question: {question}

Answer:"""

        self.PROMPT = PromptTemplate(
            template=self.prompt_template,
            input_variables=["context", "question"]
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.PROMPT}
        )
    
    def ask(self, question: str) -> Dict:
        """Ask a question and get answer with sources"""
        try:
            response = self.qa_chain.invoke({"query": question})
            
            answer = response['result']
            source_documents = response['source_documents']
            confidence = self._calculate_confidence(source_documents)
            sources = self._format_sources(source_documents)
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "source_documents": source_documents
            }
        except Exception as e:
            return {
                "answer": f"Error processing question: {str(e)}",
                "sources": [],
                "confidence": "low",
                "source_documents": []
            }
    
    def _calculate_confidence(self, source_documents: List) -> str:
        """Calculate confidence level"""
        num_sources = len(source_documents)
        if num_sources >= 3:
            return "high"
        elif num_sources >= 2:
            return "medium"
        else:
            return "low"
    
    def _format_sources(self, source_documents: List) -> List[Dict]:
        """Format source documents for display"""
        sources = []
        seen_sources = set()
        
        for doc in source_documents:
            source_name = doc.metadata.get('source', 'Unknown')
            
            if source_name not in seen_sources:
                sources.append({
                    "name": source_name,
                    "chunk_id": doc.metadata.get('chunk_id', 0),
                    "preview": doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                })
                seen_sources.add(source_name)
        
        return sources
    
    def generate_followup_questions(self, question: str, answer: str) -> List[str]:
        """Generate follow-up questions"""
        try:
            prompt = f"""Based on this Q&A, suggest 2-3 relevant follow-up questions:

Question: {question}
Answer: {answer}

Generate 2-3 concise follow-up questions (one per line, no numbering):"""

            response = self.llm.invoke(prompt)
            followups = [q.strip() for q in response.strip().split('\n') if q.strip()]
            return followups[:3]
        except Exception as e:
            print(f"Error generating follow-up questions: {str(e)}")
            return []