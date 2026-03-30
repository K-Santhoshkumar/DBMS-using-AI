# NLP to SQL Database Management System

A Natural Language Processing (NLP) based interface to query and modify SQL databases using plain English, powered by the **Google Gemini API**.

## Prerequisites
- **Python 3.8+**
- **Node.js 16+** & **npm**

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd "NLP DBMS"
```

### 2. Backend Setup
Navigate to the backend folder and set up a virtual environment:

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

Install the required Python dependencies:
```bash
pip install -r requirements.txt
```

### 3. Database Setup (Crucial)
Generate the sample databases (`sample.db`, `student.db`, `ecommerce.db`) with dummy data:
```bash
python create_sample_db.py
```
*This will create the SQLite database files in the `backend/` directory.*

### 4. Frontend Setup
Open a new terminal, navigate to the frontend folder, and install dependencies:
```bash
cd frontend
npm install
```

## Running the Application

### Start the Backend Server
From the `backend/` directory (with venv activated):
```bash
uvicorn main:app --reload
```
The backend API will run at `http://127.0.0.1:8000`.

### Start the Frontend Client
From the `frontend/` directory:
```bash
npm run dev
```
The application will run at `http://localhost:5173` (or similar).

## Usage
1. Open the frontend URL in your browser.
2. Ensure you have your Google Gemini API Key ready.
3. Select a database context (Employees, Students, or Ecommerce) and input your API Key.
4. Select the Mode (Only Querying vs Data Modification).
5. Type natural language queries like:
   - "Show me all employees in IT department"
   - "List students with grade A in Calculus"
   - "Create a new table called test with id and name"
