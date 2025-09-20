# 🏭 Industrial Safety Q&A System

A **Django-based Question-Answering service** specialized in **industrial and machine safety documentation**.  
This system processes **PDF documents**, creates **searchable chunks**, and provides **intelligent answers with citations** for trustworthy results.  

---

## 🌟 Features  

✅ **Document Processing** – Extracts text from PDFs and splits into manageable chunks  
✅ **Intelligent Search** – Semantic similarity search with **Sentence Transformers**  
✅ **Hybrid Reranking** – Combines **vector similarity + BM25 keyword scoring**  
✅ **Beautiful UI** – Responsive **Bootstrap interface** with suggested questions  
✅ **Citation Support** – Every answer includes references to source documents  
✅ **Diagnostic Tools** – Built-in troubleshooting & PDF validation utilities  

---

## 🛠️ Tech Stack  

### 🔙 Backend Framework  
- **Django 4.2.7** – High-level Python web framework for rapid development  
- **Django ORM** – Database abstraction and management  
- **SQLite** – Lightweight database for development and testing  

### 🧠 Natural Language Processing  
- **Sentence Transformers** – State-of-the-art embeddings (`all-MiniLM-L6-v2`)  
- **Chromadb 0.4.15** – Vector database for embeddings & retrieval  
- **Rank-BM25 0.2.2** – Keyword-based relevance scoring  
- **Scikit-learn 1.3.0** – Machine learning utilities  

### 📑 Document Processing  
- **PyPDF2 3.0.1** – PDF text extraction & parsing  
- **Python Standard Library** – File handling, JSON processing, utilities  

### 🎨 Frontend & UI  
- **Bootstrap 5.1.3** – Responsive CSS framework  
- **Font Awesome 6.0.0** – Modern icon library  
- **JavaScript** – Dynamic interactions & API calls  
- **HTML5/CSS3** – Web standards for UI  

### 🔗 API & Data Exchange  
- **RESTful API** – JSON-based endpoints for external use  
- **JSON** – Configuration & response format  

### ⚙️ Development & Deployment  
- **Python 3.8+** – Core programming language  
- **Virtual Environment** – Dependency isolation  
- **Pip** – Package management  

---

## 📸 Preview  

### 🔍 Web UI  
<div align="center">
  <img src="https://github.com/Harsha-032/IndustrialSafety_QA_serveice/blob/main/industrial_safety_qa/screenshots/dashboard.png">
</div>

### 🔍 Initialization 
<div align="center">
  <img src="https://github.com/Harsha-032/IndustrialSafety_QA_serveice/blob/main/industrial_safety_qa/screenshots/Initialize.png">
</div>

### 🔍 Ask Industrial Questions
<div align="center">
  <img src="https://github.com/Harsha-032/IndustrialSafety_QA_serveice/blob/main/industrial_safety_qa/screenshots/ask_questions.png">
</div>

### 🔍 Result
<div align="center">
  <img src="https://github.com/Harsha-032/IndustrialSafety_QA_serveice/blob/main/industrial_safety_qa/screenshots/result.png">
</div>

### 🔍 Details
<div align="center">
  <img src="https://github.com/Harsha-032/IndustrialSafety_QA_serveice/blob/main/industrial_safety_qa/screenshots/check_details.png">
</div>


---

## 📋 Prerequisites  

- Python **3.8+**  
- Industrial safety PDFs inside `data/pdfs/`  
- Internet connection (first-time model download)  

---

## 🚀 Installation  

```bash
# Clone repository
git clone https://github.com/Harsha-032/IndustrialSafety_QA_serveice
cd industrial-safety-qa

# Create virtual environment
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py makemigrations
python manage.py migrate

# Runserver
python manage.py runserver

```

📂 **Add PDF Files**  
- Place your **industrial safety PDFs** inside `data/pdfs/`  
- Ensure filenames match titles in `data/sources.json`  

---

## 📁 Project Structure  

```
industrial-safety-qa/
├── data/
│   ├── pdfs/                 # PDF documents folder
│   ├── sources.json          # Document metadata
│   └── questions.json        # Predefined questions
├── industrial_safety_qa/     # Django project settings
├── qa_app/                   # Main application
│   ├── templates/            # HTML templates
│   ├── utils.py              # PDF processing utilities
│   ├── embeddings.py         # Vector embedding functions
│   └── reranker.py           # Search result reranking
├── manage.py
└── requirements.txt
```

---

## 🛠️ Setup Process  

1. **Prepare PDF Files**  
   - Add PDFs to `data/pdfs/`  
   - Run PDF check: [http://localhost:8000/check-pdfs/](http://localhost:8000/check-pdfs/)  

2. **Initialize the System**  
   - Visit [http://localhost:8000/initialize/](http://localhost:8000/initialize/)  
   - Click **"Initialize System"** → Extracts text, creates chunks & embeddings  

3. **Verify Setup**  
   - Open [http://localhost:8000/diagnostic/](http://localhost:8000/diagnostic/)  
   - Ensure all components show ✅ green  

---

## 💡 Usage  

### 🌐 Web Interface  
- Visit: [http://localhost:8000/](http://localhost:8000/)  
- Choose suggested questions or type your own  
- Select **Baseline** or **Reranked** search  
- View answers with **citations**  

### 🔗 API Endpoint  

```bash
# Simple Question
curl -X POST http://localhost:8000/api/ask/   -H "Content-Type: application/json"   -d '{"q": "What are the basic safety precautions for operating machinery?", "k": 5, "mode": "reranked"}'

# Complex Question
curl -X POST http://localhost:8000/api/ask/   -H "Content-Type: application/json"   -d '{"q": "How should safety protocols be adapted for high-temperature equipment in confined spaces?", "k": 5, "mode": "reranked"}'
```

---

## ❓ Example Questions  

🔹 **Machinery Regulations** – EU Machinery Regulation requirements  
🔹 **Machine Safeguarding** – OSHA guard types  
🔹 **Safety Standards** – EN ISO 13849-1, IEC 62061  
🔹 **Risk Assessment** – SISTEMA tool & performance levels  
🔹 **Implementation** – Pneumatic safety solutions & best practices  

---

## 🔧 Technical Details  

### 📑 Document Processing Pipeline  
- **Extraction**: PyPDF2  
- **Chunking**: 300-word chunks, 50-word overlap  
- **Embedding**: `all-MiniLM-L6-v2` model  
- **Indexing**: Stored in **ChromaDB**  

### 🔍 Search Architecture  
- **Baseline**: Cosine similarity (embeddings only)  
- **Reranked**: Hybrid scoring  
  - Vector similarity (60%)  
  - BM25 keyword scoring (30%)  
  - Title matching (5%)  
  - Content length scoring (5%)  

⚠️ **Confidence Threshold**: Answers shown only if **score > 0.3** (avoids misinformation)  

---

## 🐛 Troubleshooting  

- **No chunks created** → Check `data/pdfs/` + verify `sources.json`  
- **Low-quality answers** → Use reranked mode, increase `k`, rephrase query  
- **Scanned PDFs issue** → Ensure PDFs are **text-based** (not image-only)  
- **Diagnostics** →  
  - [System Diagnostic](http://localhost:8000/diagnostic/)  
  - [PDF File Check](http://localhost:8000/check-pdfs/)  
  - [Reinitialize System](http://localhost:8000/initialize/)  

---

## 📊 Performance  

- **Baseline Search** – Pure vector similarity  
- **Reranked Search** – **30% better relevance** on test queries  
- **Hybrid Approach** – Balances **semantic + keyword** matching  

---

## 🎯 Key Learnings  

- 📑 **PDF Processing** requires robust error handling  
- ⚡ **Hybrid Search** outperforms single-method approaches  
- 📦 **Chunking with overlap** preserves context for accurate retrieval  
- 🔒 **Confidence thresholding** improves trustworthiness  
- 🛠 **Diagnostics** ensure reliability & easy debugging  

---

## 📝 License  

This project is for **educational & demonstration purposes**.  
Ensure you have rights to process any PDF documents you use.  

---

## 🤝 Contributing  

1. Fork the repository  
2. Create a feature branch  
3. Make your changes  
4. Add tests if needed  
5. Submit a pull request 🚀  

---

## 📞 Support  

- ✅ Check diagnostics page  
- ✅ Verify PDF file names & structure  
- ✅ Ensure dependencies are installed  

## 📬 Contact

**Harsha C**  
📧 harshac032@gmail.com  


