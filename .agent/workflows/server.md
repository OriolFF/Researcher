---
description: How to start and stop the Historical Researcher server and web client
---

This workflow provides instructions for managing the lifecycle of the research agent server.

### 1. Starting the Server

The server handles both the API and the web client.

To start the server with auto-reload (recommended for development):

```bash
uv run uvicorn researcher.main:app --reload --host 0.0.0.0 --port 8000
```

- **API URL**: `http://localhost:8000`
- **Web Client**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/health`

### 2. Stopping the Server

To stop the server, go to the terminal where it is running and press:

`Ctrl + C`

### 3. Accessing the Web Client

Once the server is running, simply open your browser and navigate to:

`http://localhost:8000`

### 4. Troubleshooting Startup

If the server fails to start:
1. Ensure your virtual environment is active (`.venv`).
2. Verify all dependencies are installed with `uv sync`.
3. Check that your `.env` file exists and has valid configuration.
