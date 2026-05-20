# PitchPal

PitchPal is an interactive command-line assistant for football (soccer) data, powered by LLMs and LangGraph. It supports streaming responses, classification, and integrates with various football data tools.

## Features
- Interactive QA loop for football-related queries
- Streaming LLM responses
- Arize Phoenix tracing and logging support
- Modular tool integration for football statistics, fixtures, odds, and more

## Requirements
- Python 3.13+
- [Phoenix](https://github.com/Arize-ai/phoenix) (optional, for tracing)

Install dependencies with [uv](https://docs.astral.sh/uv/):
```bash
uv sync --frozen
```

Activate the virtual environment:
```bash
source .venv/bin/activate
```

Make sure to have the following environment variables set in your shell or in a `.env` file:
```bash
export FOOTBALL_API_KEY=your_football_api_key # required
export OPENAI_API_KEY=your_openai_api_key # OpenAI model
export GOOGLE_API_KEY=your_google_api_key #Google model
```

**Alternative**: build with docker:
```bash
docker build -t pitchpal .
docker run -it --rm -e FOOTBALL_API_KEY=your_football_api_key -e OPENAI_API_KEY=your_openai_api_key -e GOOGLE_API_KEY=your_google_api_key pitchpal
```

You can also set the environment variables in a `.env` file in the root directory and run docker with:
```bash
docker run -it --rm --env-file .env pitchpal
```

## Usage
Run the main script:
```bash
python main.py [--phoenix-endpoint URL] [--debug] [--log] [--model google|openai] [--show-classification]
```

### Arguments
- `--phoenix-endpoint`   Phoenix endpoint URL (optional)
- `--debug`              Enable debug logging
- `--log`                Enable logging (critical level if off, info/debug if on)
- `--model`              Choose the model to use (`google` or `openai`, default: `openai`)
- `--show-classification` Show guardrailing node outputs in yellow

Type your football-related questions at the prompt. Type `exit` or `quit` to leave.

## Project Structure
- `main.py`         – Main entry point and CLI
- `agent/`          – Agent logic and configuration
- `tools/`          – Football data tools
- `utils/`          – Utility functions
- `test/`           – Tests
- `cache/`          – Cached data

## License
GPLv3
