# Financial Research Assistant

A powerful AI-powered financial analysis system that helps users research stocks, market trends, and economic indicators using multiple specialized tools.

## Features

- **Safety Checking**: Validates user queries for harmful content
- **Metadata Extraction**: Extracts key financial information from user queries
- **Multiple Analysis Tools**:
  - Stock Information Tool: Real-time stock prices and basic information
  - News Tool: Latest financial news articles
  - Company Analyzer: Comprehensive financial analysis of public companies
  - FRED Tool: Economic indicators and market trend analysis

## Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key
- Other API keys (Alpha Vantage, News API, FRED)

### Installation

1. Clone the repository

```bash
git clone https://github.com/yourusername/financial-research-assistant.git
cd financial-research-assistant
```

2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your API keys

```
OPENAI_API_KEY=your_openai_api_key
ALPHA_VANTAGE_API_KEY=your_alphavantage_key
NEWS_API_KEY=your_news_api_key
FRED_API_KEY=your_fred_api_key
```

### Running the Application

To run the application in standalone mode:

```bash
python src/main.py
```

## Usage

Simply enter your financial research query, and the system will:

1. Check for safety and refine the query if needed
2. Extract relevant financial metadata
3. Route your query to the appropriate specialized tools
4. Generate a comprehensive analysis

Example queries:

- "What's the current price of TSLA?"
- "Show me recent news about Amazon's cloud business"
- "Analyze Apple's financial performance over the last year"
- "What's the current unemployment rate and inflation trend?"

## Project Structure

- `src/main.py` - Main entry point and workflow coordination
- `src/flow.py` - Agent workflow implementation
- `src/tools/` - Specialized financial analysis tools
- `src/prompts.py` - System prompts for AI interactions
- `src/logger.py` - Logging utilities
