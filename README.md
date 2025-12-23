# Historical Researcher

AI-powered research assistant for writers creating historically accurate stories.

## Features

- **Hybrid Two-Tier Architecture**
  - **Tier 1**: Fast research with PydanticAI built-in tools (WebSearchTool, WebFetchTool)
  - **Tier 2**: Deep research with Tavily API and custom scraping (optional)
- **LLM Agnostic**: Works with OpenAI, Anthropic, Google Gemini, OpenRouter, or local Ollama
- **Automatic Citations**: MLA or APA format citations
- **Clean Architecture**: Domain, Data, and API layers
- **Web Interface**: Simple HTML/CSS/JS client for easy testing

## Quick Start

### 1. Install Dependencies

```bash
# Install uv if you haven't already
pip install uv

# Install dependencies
uv sync
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

**Minimum required**: One LLM provider API key

```env
# Choose ONE:
OPENAI_API_KEY=sk-your-key-here
# OR
ANTHROPIC_API_KEY=sk-ant-your-key-here
# OR
GOOGLE_API_KEY=your-key-here
# OR run Ollama locally (no key needed)
```

**Optional for Tier 2** (advanced research):

```env
TAVILY_API_KEY=tvly-your-key-here
```

### 3. Run the Server

```bash
uv run python -m researcher.main
```

Or with uvicorn directly:

```bash
uv run uvicorn researcher.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Open the Web Client

Navigate to: http://localhost:8000

## API Usage

### Research Endpoint

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What weapons were used at the Battle of Waterloo?",
    "depth": "auto",
    "output_format": "markdown",
    "citation_format": "MLA"
  }'
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Configuration

See `.env.example` for all configuration options:

- **LLM Settings**: Provider, model, temperature, max tokens
- **Tier Settings**: Enable/disable tiers, max sources
- **Escalation Rules**: Thresholds for Tier 1 → Tier 2
- **Citation Settings**: Format (MLA/APA), include access dates
- **API Settings**: Host, port, CORS origins

## Architecture

The project follows **Clean Architecture** principles:

```
┌─────────────────────────────────────┐
│         Web Client (Browser)         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│       FastAPI Layer (API)            │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     Domain Layer (Business Logic)    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  PydanticAI Agent (Tier 1 & 2)      │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     LiteLLM (Provider Abstraction)   │
└─────────────────────────────────────┘
```

See `AGENTS.md` for detailed architecture documentation.

## Development

### Run Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=src/researcher --cov-report=term-missing

# Specific test file
uv run pytest tests/unit/test_domain.py -v
```

### Code Quality

```bash
# Format code
uv run ruff format src tests

# Lint
uv run ruff check src tests
```

## Project Structure

```
researcher/
├── src/researcher/
│   ├── core/          # Configuration, logging, errors
│   ├── domain/        # Business logic, models, services
│   ├── data/          # LLM client, repositories
│   ├── agent/         # PydanticAI agent implementation
│   ├── api/           # FastAPI routes and models
│   └── main.py        # Application entry point
├── web/               # Web client (HTML/CSS/JS)
├── tests/             # Unit and integration tests
└── AGENTS.md          # Architecture documentation
```

## Tier Comparison

| Feature | Tier 1 (Built-in) | Tier 2 (Advanced) |
|---------|-------------------|-------------------|
| **Speed** | Fast (< 5s) | Slower (10-30s) |
| **Sources** | 5-10 sources | 20+ sources |
| **Quality** | Standard web results | Academic sources |
| **API Keys** | LLM only | LLM + Tavily |
| **Use Case** | Quick facts | Deep research |

## Troubleshooting

### "Tier 2 unavailable"

Make sure you have `TAVILY_API_KEY` set in your `.env` file. Get a free key at https://tavily.com

### "LLM provider error"

Check that your API key is correctly set for your chosen provider. Verify the key works by testing it directly with the provider's API.

### Import errors

Make sure all dependencies are installed:

```bash
uv sync --extra dev
```

## License

MIT

## Contributing

Contributions welcome! Please read AGENTS.md for architecture guidelines.
