# EAC Workshop

## Prerequisites

- **Python 3.11 or higher**
- **Node.js** (^22.7.5) for MCP Inspector

### Verify Python Installation

```bash
python -V
pip --version
```

---

## Setup Instructions

### UI - Chatbot

#### 1. Navigate to the UI directory

```bash
cd ./EACWorkshop/UI
```

#### 2. Create and activate a virtual environment

**Windows (PowerShell):**
```bash
python -m venv .venv-ui
.venv-ui\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python -m venv .venv-ui
source .venv-ui/bin/activate
```

#### 3. Verify pip version

```bash
pip -V
```

_Make sure it points to the Python 3.11 environment_

#### 4. Install dependencies

```bash
pip install -r requirements.txt
```

#### 5. Create .env file

- Copy-paste sample.env file
- Rename it to ".env"
- Depending which model you are going to use, enter your model provider api key either next to OPENAI_API_KEY or GOOGLE_API_KEY.
- Save the file

#### 6. Run the application

```bash
streamlit run app.py --server.port 8088
```

---

### MCP1 - Weather MCP Server

#### 1. Navigate to the MCP1 directory

```bash
cd MCP1
```

#### 2. Create and activate a virtual environment

**Windows (PowerShell):**
```bash
python -m venv .venvmcp1
.venv-mcp1\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python -m venv .venv-mcp1
source .venv-mcp1/bin/activate
```

#### 3. Install dependencies

```bash
pip install -r requirements.txt
```

#### 4. Run the MCP server

```bash
python server.py
```

---

## Testing with MCP Inspector

To test the MCP server using the MCP Inspector, open new Terminal window, make sure you are in the same directory as your MCP server and run this command:

```bash
npx @modelcontextprotocol/inspector http://0.0.0.0:8000/mcp
```

---

## Project Structure

```
EACWorkshop/
├── UI/
│   ├── app.py              # Streamlit app with MCP
│   └── requirements.txt
├── MCP1/
│   ├── server.py           # Weather MCP server
│   └── requirements.txt
└── README.md
```
