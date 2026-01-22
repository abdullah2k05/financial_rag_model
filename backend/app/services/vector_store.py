import os
from typing import List, Dict, Any
from langchain_core.documents import Document
from app.models.transaction import Transaction
from dotenv import load_dotenv

load_dotenv()

class VectorStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.embeddings = None
        self.db = None
        print(f"VectorStore: Initializing with {persist_directory}")

    def _ensure_db(self):
        """Ensures that the Chroma DB and embeddings are initialized."""
        if self.db: return
        
        try:
            from langchain_chroma import Chroma
            from langchain_huggingface import HuggingFaceEmbeddings
            
            if not self.embeddings:
                print("VectorStore: Loading embedding model...")
                self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            
            self.db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
                collection_name="transactions"
            )
        except Exception as e:
            print(f"VectorStore Initialization Error: {e}")
            from langchain_core.embeddings import FakeEmbeddings
            if not self.embeddings:
                self.embeddings = FakeEmbeddings(size=384)
            self.db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
                collection_name="transactions"
            )

    def index_transactions(self, transactions: List[Transaction]):
        self._ensure_db()
        if not self.db: return
        
        documents = []
        for tx in transactions:
            # Enhanced content with amount and type for better semantic search
            tx_type = "received" if tx.type.lower() == "credit" else "spent"
            content = f"Transaction: {tx_type} ${tx.amount:.2f} on {tx.date.strftime('%Y-%m-%d')}. Description: {tx.description}. Category: {tx.category or 'Uncategorized'}. Type: {tx.type}."
            metadata = {
                "id": str(tx.id) if hasattr(tx, 'id') else "",
                "amount": tx.amount,
                "type": tx.type,
                "date": tx.date.isoformat() if hasattr(tx.date, 'isoformat') else str(tx.date),
                "category": tx.category or "",
                "description": tx.description
            }
            documents.append(Document(page_content=content, metadata=metadata))
            
        self.db.add_documents(documents)
        print(f"Indexed {len(documents)} transactions.")

    def search(self, query: str, k: int = 20) -> List[Document]:
        """Search for relevant transactions. Default k=20 for better coverage."""
        self._ensure_db()
        if not self.db: return []
        return self.db.similarity_search(query, k=k)

    def clear(self):
        """Clears the vector store completely for a fresh session."""
        import shutil
        print(f"VectorStore: Clearing data for a fresh session...")
        try:
            # Nullify the DB object so it doesn't try to use a deleted collection
            self.db = None
            
            # Physically remove the data directory for a true reset
            if os.path.exists(self.persist_directory):
                try:
                    shutil.rmtree(self.persist_directory)
                    print(f"VectorStore: Cleaned up {self.persist_directory}")
                except Exception as re:
                    print(f"VectorStore: Warning - could not remove directory: {re}")
            
            # Re-initialize an empty store (embeddings are kept if already loaded)
            self._ensure_db()
        except Exception as e:
            print(f"VectorStore Clear Error: {e}")

# Singleton instance
vector_store = VectorStore()
