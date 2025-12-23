# Historical Researcher Agent - Architecture & Design

## Overview

The Historical Researcher Agent is an intelligent research assistant designed to help writers create historically accurate stories. It uses a **two-tier hybrid architecture** that balances speed and research depth.

## Agent Architecture

### Core Design Principles

1. **Hybrid Research Strategy**: Two-tier approach with intelligent escalation
2. **LLM Agnostic**: Works with any LLM provider via LiteLLM
3. **Output Format Agnostic**: Supports JSON, Markdown, and structured Pydantic models
4. **Citation-First**: Automatic source citations for research integrity
5. **Clean Architecture**: Clear separation of domain, data, and API layers

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│              Web Client (Browser)                    │
│         HTML/CSS/JS - Depth Selector                 │
│      [Basic] [Auto] [Deep] Research Modes            │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP/REST API
                       ▼
┌─────────────────────────────────────────────────────┐
│                 FastAPI Layer                        │
│  ┌─────────────────────────────────────────────┐   │
│  │  Routes:                                     │   │
│  │  - POST /research (auto-escalate)           │   │
│  │  - POST /research/basic (Tier 1 only)       │   │
│  │  - POST /research/deep (Tier 2 direct)      │   │
│  │  - GET /health (tier availability)          │   │
│  └─────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              Domain Layer (Business Logic)           │
│  ┌─────────────────────────────────────────────┐   │
│  │  Services:                                   │   │
│  │  - ResearchService (orchestration)          │   │
│  │  - EscalationService (tier decisions)       │   │
│  │  - ValidationService (fact checking)        │   │
│  │  - CitationFormatter (MLA/APA)              │   │
│  └─────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│           PydanticAI Agent (Core)                    │
│  ┌──────────────────────┬──────────────────────┐   │
│  │   TIER 1             │   TIER 2              │   │
│  │   (Built-in)         │   (Advanced)          │   │
│  ├──────────────────────┼──────────────────────┤   │
│  │ • WebSearchTool      │ • Tavily Direct API   │   │
│  │ • WebFetchTool       │ • Custom Scraper      │   │
│  │   (citations=True)   │ • Content Extractor   │   │
│  │                      │ • Academic Sources    │   │
│  ├──────────────────────┴──────────────────────┤   │
│  │        Custom Domain Tools                   │   │
│  │  - verify_historical_date                    │   │
│  │  - assess_result_quality                     │   │
│  │  - extract_historical_context                │   │
│  └─────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              LLM Provider (LiteLLM)                  │
│     OpenAI | Gemini | Anthropic | Ollama            │
└─────────────────────────────────────────────────────┘
```

## Two-Tier Research System

### Tier 1: Built-in Tools (Fast & Efficient)

**Technology**: PydanticAI native `WebSearchTool` and `WebFetchTool`

**Characteristics**:
- ⚡ **Speed**: < 5 seconds average
- 📚 **Sources**: 5-10 quality sources
- ✅ **Citations**: Automatic with `enable_citations=True`
- 🔑 **Requirements**: Only LLM API key needed
- 🎯 **Best For**: Quick facts, standard historical queries

**How It Works**:
```python
from pydantic_ai import Agent, WebSearchTool, WebFetchTool

tier1_agent = Agent(
    'openai:gpt-4',
    builtin_tools=[
        WebSearchTool(),
        WebFetchTool(
            enable_citations=True,
            allowed_domains=['wikipedia.org', 'britannica.com', 'history.com'],
            max_uses=10
        )
    ],
    system_prompt="You are a historical research assistant..."
)
```

**Advantages**:
- No extra dependencies
- Officially maintained by PydanticAI
- Automatic citation extraction
- Works out-of-the-box

**Limitations**:
- Limited to standard web search results
- May miss academic/specialized sources
- Fewer total sources

---

### Tier 2: Advanced Research (Deep & Thorough)

**Technology**: Direct Tavily API + Custom BeautifulSoup scraping

**Characteristics**:
- 🕐 **Speed**: 10-30 seconds
- 📚 **Sources**: 20+ sources including academic
- 🎓 **Quality**: Access to JSTOR, Archive.org, academic databases
- 🔑 **Requirements**: LLM key + Tavily API key
- 🎯 **Best For**: Complex research, primary sources, academic citations

**How It Works**:
```python
from researcher.data.tier2 import TavilyClient, WebScraper

# Deep search with Tavily
tavily = TavilyClient(api_key)
results = await tavily.search(
    query="Battle of Waterloo primary sources",
    search_depth="advanced",
    max_results=20,
    include_domains=['jstor.org', 'archive.org']
)

# Custom scraping for full content
scraper = WebScraper()
content = await scraper.scrape(url, extract_metadata=True)
```

**Advantages**:
- Access to academic sources
- More comprehensive results
- Custom content extraction
- Better metadata (authors, dates, publishers)

**Limitations**:
- Slower response time
- Requires additional API key
- More complex error handling

---

### Escalation Strategy

The agent **intelligently decides** when to escalate from Tier 1 to Tier 2.

#### Escalation Triggers

1. **Insufficient Results**
   - Tier 1 returns < 3 quality sources
   - Low diversity in source types

2. **Low Confidence**
   - Agent reports confidence < 70%
   - Conflicting information found

3. **User Explicit Request**
   - User selects "Deep Research" mode
   - User asks for "more sources" or "academic sources"

4. **Complex Query Detection**
   - Multi-faceted historical questions
   - Need for primary sources
   - Obscure historical events

5. **Missing Critical Information**
   - Key dates unverified
   - Important context missing
   - Citations needed for specific claims

#### Escalation Decision Flow

```
User Query
    ↓
[Tier 1: WebSearchTool + WebFetchTool]
    ↓
Quality Assessment
    ↓
    ├─→ [Sufficient Results] → Return to User
    │   (≥3 sources, confidence ≥70%)
    │
    └─→ [Insufficient Results] → Escalate
        ↓
        [Tier 2: Tavily + Custom Scraping]
        ↓
        Merge Results (Tier 1 + Tier 2)
        ↓
        Return Enhanced Results to User
```

#### Implementation Example

```python
async def comprehensive_research(query: str) -> ResearchResult:
    """Auto-escalating research workflow"""
    
    # Step 1: Try Tier 1 first
    tier1_result = await tier1_agent.run(query)
    
    # Step 2: Assess quality
    quality_score = assess_result_quality(tier1_result)
    
    if quality_score >= ESCALATION_THRESHOLD:
        return tier1_result  # Good enough!
    
    # Step 3: Escalate to Tier 2
    logger.info(f"Escalating to Tier 2 - quality score: {quality_score}")
    tier2_result = await tier2_deep_search(query)
    
    # Step 4: Merge results
    return merge_research_results(tier1_result, tier2_result)
```

---

## Agent Instructions & System Prompts

### System Prompt (Tier 1)

```
You are a historical research assistant helping writers create historically accurate stories.

Your role:
1. Search for factual historical information
2. Verify dates, events, and figures
3. Provide citations for all claims
4. Identify gaps in information
5. Assess your confidence in findings

When researching:
- Prioritize reliable sources (Wikipedia, Britannica, .edu domains)
- Always include citations
- Note any conflicting information
- Indicate confidence levels (high/medium/low)
- Flag when you need more sources

Output format:
- Main findings with citations
- List of sources
- Confidence assessment
- Gaps or uncertainties
```

### System Prompt (Tier 2 - Advanced)

```
You are an advanced historical research assistant with access to academic databases and primary sources.

Your enhanced role:
1. Deep search across academic sources (JSTOR, Archive.org)
2. Find primary historical documents
3. Cross-reference multiple academic sources
4. Extract quotes with proper attribution
5. Provide comprehensive bibliographies

When conducting deep research:
- Prioritize primary sources when available
- Include academic journal articles
- Extract relevant quotes from sources
- Verify facts across multiple sources
- Provide detailed metadata (authors, dates, publishers)

Output format:
- Comprehensive findings with academic citations
- Primary source quotes
- Cross-referenced facts
- Full bibliography (MLA/APA format)
- Research methodology notes
```

---

## Key Terminology

### Domain Terms

**Research Query**: User's question or topic requiring historical research
- Contains: topic, time period (optional), depth preference
- Example: "What weapons were used at the Battle of Waterloo?"

**Research Tier**: Level of research depth
- `Tier1`: Fast, built-in tools (WebSearch, WebFetch)
- `Tier2`: Advanced, custom tools (Tavily, scraping)

**Escalation Decision**: Automated choice to move from Tier 1 to Tier 2
- Based on result quality, confidence, and user preference
- Logged for analytics and improvement

**Historical Period**: Specific timeframe being researched
- Format: start_year, end_year, era_name
- Example: `HistoricalPeriod(1815, 1815, "Napoleonic Wars")`

**Source**: Reference to original information
- Contains: URL, title, author, date_accessed, credibility_score
- Used for citations and verification

**Research Result**: Structured output of research
- Contains: findings, sources, confidence, tier_used, citations

**Story Context**: Historical context formatted for writers
- Extracted from research results
- Includes: setting, key figures, events, atmosphere, details

### Technical Terms

**LiteLLM**: Universal abstraction layer for LLM APIs
- Allows switching between OpenAI, Gemini, Anthropic, etc.
- Single interface: `completion(model="openai:gpt-4", messages=[...])`

**PydanticAI**: Agent framework with structured outputs
- Built-in tools (WebSearchTool, WebFetchTool)
- Type-safe with Pydantic models
- Dependency injection for tools

**WebSearchTool**: Built-in PydanticAI tool for web search
- Provider-agnostic (works with OpenAI, Anthropic, Google, Groq)
- Returns structured search results

**WebFetchTool**: Built-in PydanticAI tool for fetching URLs
- `enable_citations=True` for automatic citation extraction
- Content parsing and cleaning
- Domain filtering with `allowed_domains`

**Tavily**: AI-optimized search API for Tier 2
- Designed for agent/LLM consumption
- Advanced search with more results
- Academic source prioritization

**Clean Architecture**: Separation of concerns in layers
- **Domain**: Business logic (tier-agnostic)
- **Data**: External integrations (Tier 1 & 2 tools)
- **API**: FastAPI endpoints and web client

**Output Adapter**: Format converter for research results
- JSON, Markdown, Structured (Pydantic)
- Handles citation formatting
- Customizable per writer's needs

---

## Research Workflows

### 1. Basic Research (Tier 1 Only)

**Use Case**: Quick fact-checking, simple questions

**Flow**:
```
User Query → Tier 1 Agent → WebSearchTool → WebFetchTool → Result
```

**Example**:
```python
result = await basic_research("When was Napoleon born?")
# Uses only built-in tools
# Returns: "Napoleon Bonaparte was born on August 15, 1769 [1][2]"
```

**API Endpoint**: `POST /research/basic`

---

### 2. Comprehensive Research (Auto-Escalate)

**Use Case**: Default mode, intelligent depth selection

**Flow**:
```
User Query 
    → Tier 1 Agent
    → Quality Assessment
    → [If needed] Tier 2 Agent
    → Merged Result
```

**Example**:
```python
result = await comprehensive_research(
    "What were the key strategic decisions at Waterloo?"
)
# Tries Tier 1 first
# Escalates to Tier 2 if needed
# Returns combined results
```

**API Endpoint**: `POST /research`

---

### 3. Deep Research (Tier 2 Direct)

**Use Case**: Academic research, primary sources needed

**Flow**:
```
User Query → Tier 2 Agent → Tavily + Scraping → Enhanced Result
```

**Example**:
```python
result = await deep_research(
    "Find primary source accounts of the Battle of Waterloo"
)
# Skips Tier 1
# Uses Tavily + custom scraping
# Returns academic sources with quotes
```

**API Endpoint**: `POST /research/deep`

---

## Configuration

### Environment Variables

```bash
# Required: LLM Provider (choose one)
OPENAI_API_KEY=sk-...              # OpenAI
GOOGLE_API_KEY=...                  # Gemini
ANTHROPIC_API_KEY=sk-ant-...       # Claude
OPENROUTER_API_KEY=sk-or-...       # OpenRouter
# Or run Ollama locally (no key needed)

# Optional: Tier 2 Advanced Research
TAVILY_API_KEY=tvly-...            # Enables Tier 2

# Agent Configuration
LLM_PROVIDER=openai                # Provider name
LLM_MODEL=gpt-4                    # Model name
MAX_TOKENS=2000                    # Response length
TEMPERATURE=0.1                    # Lower = more factual

# Escalation Settings
ESCALATION_THRESHOLD=0.7           # Quality score 0-1
MIN_SOURCES_TIER1=3                # Minimum Tier 1 sources
ENABLE_AUTO_ESCALATION=true        # Allow auto-escalation

# Citation Settings
CITATION_FORMAT=MLA                # MLA or APA
INCLUDE_ACCESS_DATES=true          # Add "Accessed: ..." to citations
```

### Agent Configuration Object

```python
from pydantic import BaseModel

class AgentConfig(BaseModel):
    # LLM Settings
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    temperature: float = 0.1
    max_tokens: int = 2000
    
    # Tier 1 Settings
    tier1_enabled: bool = True
    tier1_max_sources: int = 10
    tier1_allowed_domains: list[str] = [
        "wikipedia.org",
        "britannica.com", 
        "history.com"
    ]
    
    # Tier 2 Settings
    tier2_enabled: bool = False  # Requires Tavily key
    tier2_max_sources: int = 20
    tier2_search_depth: str = "advanced"
    
    # Escalation Rules
    enable_auto_escalation: bool = True
    escalation_threshold: float = 0.7
    min_sources_tier1: int = 3
    min_confidence_tier1: float = 0.7
    
    # Output Settings
    citation_format: str = "MLA"
    include_access_dates: bool = True
    output_format: str = "json"  # json, markdown, structured
```

---

## Testing Strategy

### Unit Tests

**Domain Layer**:
- Test escalation decision logic
- Test quality assessment algorithms
- Test citation formatting

**Tier 1 Tools**:
- Mock PydanticAI built-in responses
- Test tool configuration
- Verify citation extraction

**Tier 2 Tools**:
- Mock Tavily API responses
- Test HTML scraping with fixtures
- Verify metadata extraction

### Integration Tests

**Escalation Scenarios**:
```python
async def test_auto_escalation():
    """Test Tier 1 → Tier 2 escalation"""
    # Setup: Mock Tier 1 with poor results
    # Action: Run comprehensive_research
    # Assert: Tier 2 was called
    # Assert: Results merged correctly
```

**End-to-End Workflows**:
```python
async def test_comprehensive_research_flow():
    """Test full research workflow"""
    result = await comprehensive_research("Battle of Waterloo")
    assert result.sources >= 3
    assert result.confidence >= 0.7
    assert len(result.citations) > 0
```

---

## API Reference

### Endpoints

#### `POST /research`
Auto-escalating research (recommended).

**Request**:
```json
{
  "query": "What caused the fall of the Roman Empire?",
  "output_format": "markdown",
  "llm_provider": "openai",
  "llm_model": "gpt-4"
}
```

**Response**:
```json
{
  "findings": "The fall of the Roman Empire...",
  "sources": [
    {
      "url": "https://britannica.com/...",
      "title": "Fall of Rome",
      "accessed": "2025-12-23"
    }
  ],
  "tier_used": "tier1",
  "confidence": 0.85,
  "citations": ["[1] Britannica..."],
  "execution_time_ms": 3500
}
```

#### `POST /research/basic`
Force Tier 1 only (fast mode).

#### `POST /research/deep`
Force Tier 2 only (requires Tavily key).

#### `GET /health`
System health and tier availability.

**Response**:
```json
{
  "status": "healthy",
  "tier1_available": true,
  "tier2_available": true,
  "llm_provider": "openai"
}
```

---

## Best Practices for Writers

### When to Use Each Mode

**Basic Mode** (`/research/basic`):
- ✅ Quick fact-checking (dates, names, places)
- ✅ General historical context
- ✅ Common knowledge verification
- ❌ Complex analysis
- ❌ Primary source research

**Auto Mode** (`/research`) - **Recommended**:
- ✅ Most queries - let the agent decide
- ✅ Balanced speed and depth
- ✅ Automatic quality optimization

**Deep Mode** (`/research/deep`):
- ✅ Academic-level research
- ✅ Primary source documents needed
- ✅ Complex historical analysis
- ✅ Multiple perspectives required
- ❌ When speed is critical

### Citation Usage

The agent provides citations in MLA or APA format:

**MLA Example**:
```
"Battle of Waterloo." Britannica, www.britannica.com/event/Battle-of-Waterloo. 
Accessed 23 Dec. 2025.
```

**In Your Story**:
- Use citations for fact-checking during writing
- Include bibliography in story notes
- Verify quotes before using in dialogue
- Check multiple sources for controversial points

---

## Future Enhancements

### Potential Tier 3: Specialized Sources

- Library of Congress API
- Historical newspaper archives
- University digital collections
- Museum databases

### Advanced Features

- Multi-lingual research (translate sources)
- Timeline generation from research
- Character research (historical figures)
- Location research (historical geography)
- Comparative historical analysis

---

## Glossary

**Agent**: AI-powered assistant that executes research tasks  
**Built-in Tools**: Native PydanticAI tools (WebSearch, WebFetch)  
**Citation**: Reference to source material with access information  
**Confidence Score**: Agent's certainty in findings (0.0-1.0)  
**Escalation**: Moving from Tier 1 to Tier 2 research  
**LLM**: Large Language Model (GPT-4, Claude, Gemini)  
**Primary Source**: Original historical document or artifact  
**Research Depth**: Level of thoroughness (basic/auto/deep)  
**Secondary Source**: Analysis of historical events  
**System Prompt**: Instructions guiding agent behavior  
**Tier**: Level of research capability (1=basic, 2=advanced)  
**Tool**: Function the agent can call (search, fetch, scrape)  
**Workflow**: Multi-step research process with logic  

---

*This document is the authoritative guide for the Historical Researcher Agent architecture and should be updated as the system evolves.*
