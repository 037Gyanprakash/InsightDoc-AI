# 💎 InsightDoc AI | Document & Visual Intelligence Suite

InsightDoc AI is a **general-purpose Document & Visual Intelligence Suite** built on a Retrieval-Augmented Generation (RAG) architecture.
It delivers **precise, context-faithful answers** by combining semantic retrieval, entity-aware filtering, and visual (OCR-based) understanding.

---

## 🧠 System Overview

- **Architecture**: Retrieval-Augmented Generation (RAG)
- **LLM**: Meta LLaMA-3 (via Groq)
- **Vector Store**: ChromaDB (persistent, local)
- **Embeddings**: HuggingFace `all-MiniLM-L6-v2`
- **Evaluation**: RAGAS (precision, recall, faithfulness, relevancy)

---

## ✨ Key Features

- **📄 Document Intelligence**
  Understands and answers questions grounded strictly in retrieved document context.

- **👁️ Visual Intelligence**
  OCR-enabled reasoning over visual inputs for text-based understanding.

- **🧠 Entity-Aware Context Isolation**
  Automatically detects the target entity in a query and restricts retrieval to relevant context only.

- **🔍 Hybrid Retrieval Strategy**
  Combines semantic similarity with metadata validation to reduce cross-document leakage.

- **📋 Context-Only Answering**
  Generates answers strictly from retrieved context with clear fallbacks when information is missing.

- **📊 Evaluation-Ready RAG Pipeline**
  Integrated RAGAS evaluation to measure real retrieval and generation quality.

- **🔒 Local & Secure Indexing**
  All embeddings and vectors are stored locally using ChromaDB.

---

## ⚙️ Design Enhancements

- Robust entity extraction with filename fallback
- Entity normalization for reliable filtering
- Third-person answer normalization
- Hybrid metadata + content validation
- Prevents artificially inflated RAG evaluation scores

---

## 🛠 Tech Stack

| Layer      | Tools Used             |
|------------|------------------------|
| Backend    | FastAPI                |
| Frontend   | Streamlit              |
| LLM        | Groq (LLaMA-3)         |
| Embeddings | HuggingFace MiniLM     |
| Vector DB  | ChromaDB               |
| OCR        | Tesseract              |
| Evaluation | RAGAS                  |
| Language   | Python                 |

---

## 🚀 How to Run Locally

### 1️⃣ Clone the repository

```bash
git clone https://github.com/Its-Itachi/InsightDoc-AI.git
cd InsightDoc-AI
```

### 2️⃣ Create a virtual environment

```bash
python -m venv venv
```

### 3️⃣ Activate the virtual environment

**Windows (PowerShell):**
```powershell
venv\Scripts\activate
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

### 4️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
TOKENIZERS_PARALLELISM=false
```

---

## ▶️ Running the Application

### Start Backend (FastAPI)

```bash
uvicorn main:app --reload --port 8000
```

API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Start Frontend (Streamlit)

```bash
streamlit run streamlit_app.py
```

Application UI: [http://localhost:8501](http://localhost:8501)

---

## 📊 RAG Evaluation (RAGAS)

InsightDoc AI includes an evaluation pipeline using **RAGAS** to measure:

- Context Precision
- Context Recall
- Faithfulness
- Answer Relevancy

Run evaluation:

```bash
python evaluation/ragas_eval.py
```

---

## 👤 Author

**Jayesh Dethe**
GitHub: [https://github.com/Its-Itachi](https://github.com/037Gyanprakash)

---

## 📝 Notes

- Designed to reflect **production-grade document intelligence**
- Prevents cross-document and cross-entity hallucination

---

Happy coding! 🚀
