from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import os
import shutil
import traceback

from app.services.parser import UniversalCSVParser
from app.services.pdf_parser import pdf_parser
from app.services.storage import storage
from app.services.categorizer import categorizer
from app.services.vector_store import vector_store
from app.models.transaction import Transaction, StatementMetadata

router = APIRouter()

@router.post("/upload")
async def upload_statement(file: UploadFile = File(...)):
    # Create temp directory for processing if needed (PDF parser might need it)
    os.makedirs("temp", exist_ok=True)
    temp_path = f"temp/{file.filename}"
    
    try:
        if file.filename.endswith('.csv'):
            parser = UniversalCSVParser()
            content = await file.read()
            transactions, metadata = await parser.parse(content, file.filename)
        elif file.filename.endswith('.pdf'):
            # Copy to temp file for PDF reader
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            transactions = pdf_parser.parse(temp_path)
            if not transactions:
                raise ValueError("No transactions extracted from PDF.")

            # Build basic metadata for PDF statements as well
            metadata = StatementMetadata(
                currency=transactions[0].currency,
                date_range_start=min(t.date for t in transactions),
                date_range_end=max(t.date for t in transactions),
            )
        else:
            raise HTTPException(status_code=400, detail="Only CSV and PDF files are supported.")

        # 0. Clear previous session data (User Requirement: Reset on new upload)
        print("Clearing previous data...")
        storage.clear_all()
        vector_store.clear()

        # 1. Categorize
        categorizer.apply_categorization(transactions)
        
        # 2. Save to Persistent DB
        storage.save_transactions(transactions)
        
        # 3. Index in Vector Store for RAG
        try:
            vector_store.index_transactions(transactions)
        except Exception as ve:
            print(f"Vector Indexing Error: {ve}")
            
        return {
            "transactions": transactions,
            "metadata": metadata
        }

    except Exception as e:
        # Print full traceback to the console for debugging
        print("[ERROR] Exception in /api/v1/upload endpoint while processing file:", file.filename)
        print("[ERROR] Exception detail:", repr(e))
        traceback.print_exc()
        raise HTTPException(
            status_code=400,
            detail=f"Processing error: {str(e)}"
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
