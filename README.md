<p align="left">
   <img src="https://github.com/user-attachments/assets/90fd3e8c-0fff-4849-a11b-a47cca08983b" alt="AECtech-Conference-flat" width="200"/>

</p>

# Grasshopper inside AI: Run Grasshopper definitions from AI assistants with MCP and Rhino.Compute

This is repository with materials for the AECTech NYC 2026 workshop run by KPF and McNeel.

“Hey AI, could you run this Grasshopper definition for me?”

Rhino.Compute enables us to run Grasshopper definitions remotely—without opening Rhino or Grasshopper. Model Context Protocol (MCP) allows us to connect AI applications to our custom tools. Both are cutting-edge technologies: Rhino.Compute represents a paradigm shift in computational design by enabling cloud-based geometry processing, while MCP is an emerging open standard that bridges the gap between AI assistants and domain-specific tools—making this workshop one of the first explorations of their combined potential in the AEC industry.

In this workshop, you'll learn how to use both. We’ll begin with an introduction to Rhino.Compute, followed by an overview of MCP. Then, we’ll walk through how to build an MCP server that interacts with Rhino.Compute.

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
cd UI
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

### MCP_RhinoCompute - Rhino.Compute MCP Server

#### 1. Navigate to the MCP_RhinoCompute directory

```bash
cd MCP_RhinoCompute
```

#### 2. Create and activate a virtual environment

**Windows (PowerShell):**

```bash
python -m venv .venv-rhinocompute
.venv-rhinocompute\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python -m venv .venv-rhinocompute
source .venv-rhinocompute/bin/activate
```

#### 3. Install dependencies

```bash
pip install -r requirements.txt
```

#### 4. Ensure Rhino.Compute is running

The server connects to Rhino.Compute at `http://localhost:6500/`. Make sure Rhino.Compute is running before starting the MCP server.

#### 5. Run the MCP server

```bash
python server.py
```

The server will start on port **8001**.

---

## Testing with MCP Inspector

To test the MCP server using the MCP Inspector, open a new Terminal window, make sure you are in the same directory as your MCP server and run this command:

**For MCP1 (Weather server on port 8000):**

```bash
npx @modelcontextprotocol/inspector http://0.0.0.0:8000/mcp
```

**For MCP_RhinoCompute (Rhino.Compute server on port 8001):**

```bash
npx @modelcontextprotocol/inspector http://0.0.0.0:8001/mcp
```

---


## Project Structure

```
├── UI/
│   ├── app.py              # Streamlit app with MCP
│   └── requirements.txt
├── MCP1/
│   ├── server.py           # Weather MCP server
│   └── requirements.txt
├── MCP_RhinoCompute/
│   ├── server.py           # MCP server for Rhino.Compute
│   ├── requirements.txt
│   ├── assets/             # Grasshopper files (.gh), sample 3dm, and IO jsons
│   ├── helpers/            # Helper functions for Rhino/Grasshopper
│   ├── outputs/            # Generated output .3dm files
│   └── final/              # Completed reference code
└── README.md
```

---

