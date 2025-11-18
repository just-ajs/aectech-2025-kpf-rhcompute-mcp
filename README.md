<p align="left">
   <img src="https://github.com/user-attachments/assets/90fd3e8c-0fff-4849-a11b-a47cca08983b" alt="AECtech-Conference-flat" width="200"/>

</p>

# Grasshopper inside AI: Run Grasshopper definitions from AI assistants with MCP and Rhino.Compute 
This is repository with materials for the AECTech NYC 2026 workshop run by KPF and McNeel. 

“Hey AI, could you run this Grasshopper definition for me?”

Rhino.Compute enables us to run Grasshopper definitions remotely—without opening Rhino or Grasshopper. Model Context Protocol (MCP) allows us to connect AI applications to our custom tools.

In this workshop, you’ll learn how to use both. We’ll begin with an introduction to Rhino.Compute, followed by an overview of MCP. Then, we’ll walk through how to build an MCP server that interacts with Rhino.Compute.

By the end of the session, you’ll be able to run Grasshopper definitions by prompting them from any AI assistant.

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
python -m venv .ven-vmcp1
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
