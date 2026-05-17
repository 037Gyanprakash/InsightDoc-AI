import os
import shutil
import base64
import uuid
import re
import json
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from io import BytesIO
from PIL import Image
import pytesseract
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from processor import DocumentProcessor


# ENV SETUP

load_dotenv()

UPLOAD_DIR = "storage/uploads"
DB_DIR = "storage/chroma_db"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

app = FastAPI(title="InsightDoc AI – General Purpose RAG")


# INITIALIZATION

processor = DocumentProcessor()

print("Loading embeddings...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vector_db = Chroma(
    persist_directory=DB_DIR,
    embedding_function=embeddings
)

groq_key = os.getenv("GROQ_API_KEY")
if not groq_key:
    raise RuntimeError("GROQ_API_KEY not found in environment")

# LLM
llm = ChatGroq(
    temperature=0,
    model_name="llama-3.3-70b-versatile",
    api_key=groq_key
)


# AI ROUTER (Intent Recognition)

def analyze_query(query: str) -> Dict[str, Any]:
    """
    Uses the LLM to identify WHO or WHAT the user is asking about.
    """
    parser = JsonOutputParser()
    
    router_prompt = PromptTemplate(
        template="""
        Analyze the user's question and extract the 'target_entity'.
        
        Definition of 'target_entity':
        - A specific person (e.g., "Jay"), company (e.g., "Walmart"), or distinct file subject.
        
        Rules:
        1. If the question is about a specific person/entity, return their name as "target_entity".
        2. If the question is generic (e.g., "Summarize all files", "What is the total?"), return null.
        3. Ignore topic keywords like: "resume", "cv", "pdf", "invoice", "receipt", "education", "cgpa", "total", "date".
        
        Examples:
        - "Who is Jay?" -> {{"target_entity": "jay"}}
        - "Show me Jayesh's education" -> {{"target_entity": "jayesh"}}
        - "Compare Jay and Rohan" -> {{"target_entity": ["jay", "rohan"]}}
        - "What is the total amount?" -> {{"target_entity": null}}

        Question: {question}
        
        Return ONLY valid JSON:
        """,
        input_variables=["question"]
    )
    
    chain = router_prompt | llm | parser
    
    try:
        result = chain.invoke({"question": query})
        return result
    except Exception as e:
        print(f"[Router Error] {e}")
        return {"target_entity": None}


# HELPERS

def get_file_icon(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return {
        ".pdf": "📕", ".docx": "📝", ".txt": "📄", 
        ".csv": "📊", ".xlsx": "📊", 
        ".jpg": "🖼️", ".png": "🖼️", ".jpeg": "🖼️"
    }.get(ext, "📁")


# PYDANTIC MODELS

class QueryRequest(BaseModel):
    question: str
    image_base64: Optional[str] = None

class SourceInfo(BaseModel):
    filename: str
    file_type_icon: str
    page_content: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]


# API ROUTES

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    chunks = processor.process_file(file_path, file.content_type, file.filename)

    if not chunks:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="No extractable text found in file.")

    vector_db.add_documents(chunks)

    return {
        "file_id": file_id,
        "filename": file.filename,
        "chunks_indexed": len(chunks),
        "icon": get_file_icon(file.filename)
    }

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    full_query = request.question.strip()

    #  Handle OCR if image provided
    if request.image_base64:
        try:
            img_bytes = base64.b64decode(request.image_base64)
            img = Image.open(BytesIO(img_bytes))
            ocr_text = pytesseract.image_to_string(img)
            if ocr_text.strip():
                full_query += f"\n\n[IMAGE CONTEXT]: {ocr_text}"
        except Exception as e:
            print(f"[OCR Error] {e}")

    
    #  AI ROUTER (Understand Intent)
    
    analysis = analyze_query(full_query)
    target = analysis.get("target_entity")
    
    print(f"DEBUG: User Query: '{full_query}' | Detected Target: '{target}'")

    
    #  HYBRID SEARCH (Metadata + Content)
    
    retriever = vector_db.as_retriever(search_kwargs={"k": 20})
    raw_docs = retriever.invoke(full_query)
    
    final_docs = []

    if target:
        targets = [target] if isinstance(target, str) else target
        targets = [t.lower() for t in targets if t]

        if not targets:
            final_docs = raw_docs
        else:
            for doc in raw_docs:

                doc_entity = doc.metadata.get("entity", "").lower()
                if any(t in doc_entity for t in targets):
                    final_docs.append(doc)
                    continue 


                doc_content = doc.page_content.lower()
                if any(t in doc_content for t in targets):
                    final_docs.append(doc)
    else:
        final_docs = raw_docs

    final_docs = final_docs[:5]

    if not final_docs:
        return {
            "answer": f"I couldn't find any documents matching '{target}' in your uploads.",
            "sources": []
        }

    
    # ANSWER GENERATION (Context Injection)
    
    context_text = "\n\n".join(
        [f"[Source: {d.metadata.get('entity', 'Unknown')}] {d.page_content}" for d in final_docs]
    )

    prompt = PromptTemplate(
        template="""
        You are an intelligent document assistant. Answer the user's question based ONLY on the provided context.

        CRITICAL INSTRUCTIONS:
        1. **Third-Person Objective Mode:** Even if the document uses "I", "Me", or "My", you must convert this to the person's name or "The document". 
           - INCORRECT: "I am a student."
           - CORRECT: "Jayesh is a student." OR "The resume states that he is a student."
        2. **Source Awareness:** The context is tagged with `[Source: Name]`. 
        3. **Target Isolation:** If the user asks about a specific person (e.g., "Jay"), ONLY use information from sources that belong to "Jay". Ignore sources belonging to others (e.g., "Rohan").
        4. **Fallback:** If the specific information is missing, plainly state "I cannot find that information in the documents."

        Context:
        {context}

        Question:
        {question}

        Answer:
        """,
        input_variables=["context", "question"]
    )

    chain = prompt | llm
    response = chain.invoke({
        "context": context_text,
        "question": full_query
    })

    
    # RESPONSE FORMATTING
    
    sources = []
    seen_sources = set()
    
    for d in final_docs:
        src_name = d.metadata.get("source", "unknown")
        if src_name not in seen_sources:
            seen_sources.add(src_name)
            sources.append(SourceInfo(
                filename=src_name, 
                file_type_icon=get_file_icon(src_name), 
                page_content=d.page_content[:200].replace("\n", " ") + "..."
            ))

    return {
        "answer": response.content,
        "sources": sources
    }
