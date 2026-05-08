# Legal Document Auto-Generator

AI-powered intelligent legal document generation platform

## Features

- 📄 Batch PDF file upload support
- 📦 ZIP archive support (containing multiple PDFs)
- 🤖 AI-powered automatic case information extraction
- 📊 Automatic Excel element generation
- 📝 Batch legal document generation (complaints, evidence lists, applications, etc.)
- 🎨 Clean and modern Web interface

## Quick Start

### Option 1: One-click Launch (Recommended)

1. Double-click `start.bat`
2. Configure API Key when prompted on first run
3. Dependencies will be installed automatically and services started
4. Browser will automatically open the frontend interface

### Option 2: Manual Launch

**1. Configure API Key**

Edit `backend/.env` file:
```
DEEPSEEK_API_KEY=your_deepseek_api_key
```

Get API Key: https://platform.deepseek.com

**2. Install Backend Dependencies**

```bash
cd backend
pip install -r requirements.txt
```

**3. Install Frontend Dependencies**

```bash
cd frontend
npm install
```

**4. Start Services**

```bash
# Terminal 1: Start backend
cd backend
python main.py

# Terminal 2: Start frontend
cd frontend
npm run dev
```

**5. Access**

Open browser and visit: http://localhost:3000

## Usage

1. **Upload Files** - Upload PDF files or ZIP archives
2. **View Cases** - AI automatically parses each PDF into a case card
3. **Edit Information** - Modify/supplement case information
4. **Generate Documents** - Select document type and generate with one click
5. **Download Results** - Download generated Excel and Word files

## System Requirements

- Python 3.8+
- Node.js 18+
- Windows 7/8/10/11

## Tech Stack

**Backend**
- FastAPI - Web Framework
- LangChain - AI Agent Framework
- DeepSeek - Large Language Model
- PyMuPDF - PDF Parsing
- OpenPyXL - Excel Generation
- python-docx - Word Generation

**Frontend**
- Vue 3 - Frontend Framework
- Vite - Build Tool
- Axios - HTTP Client

## Directory Structure

```
legal-document-generator/
├── backend/
│   ├── app/
│   │   ├── api/routes.py      # API routes
│   │   ├── core/agent.py      # AI Agent
│   │   └── services/          # Service modules
│   ├── main.py                # Entry point
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment config
├── frontend/
│   ├── src/
│   │   ├── App.vue            # Main component
│   │   └── api.js             # API calls
│   ├── vite.config.js         # Vite config
│   └── package.json           # Node dependencies
├── start.bat                  # One-click launch script
└── README.md                  # Documentation
```

## Notes

- API Key is stored locally in .env file only, never uploaded
- Generated files are saved in backend/outputs directory
- Uploaded PDF files are saved in backend/uploads directory

## License

MIT License
