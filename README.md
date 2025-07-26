# Multi-Agent AI Video Creation System

A modular, multi-agent AI system for automated video creation from text scripts. Built following agentic AI design principles with support for easy model switching.

## Architecture

The system follows a multi-agent architecture with:
- **High-Level Planner (HLP)**: Coordinates the entire workflow
- **Low-Level Workers**: Handle specific tasks in the pipeline
- **Central Configuration**: Enables easy model switching

## Workflow

1. **Story Analysis**: Analyzes input script and extracts scenes
2. **Clip Selection**: Generates video clip descriptions
3. **Narration**: Creates synchronized narration text
4. **BGM Selection**: Suggests background music options
5. **Assembly**: Compiles final video plan

## Project Structure

```
project/
├── config.py           # Configuration and model settings
├── utils.py            # Central call_model wrapper + helpers
├── workers.py          # Individual worker functions
├── coordinator.py      # VideoAgent class (HLP)
├── main.py            # Entry point
├── backend/           # FastAPI backend
│   └── api.py         # REST API endpoints
├── tests/             # Unit tests
│   ├── test_utils.py
│   ├── test_workers.py
│   └── test_coordinator.py
└── README.md
```

## Quick Start

### Installation

```bash
pip install game-by-virtuals fastapi uvicorn[standard]
```

### Basic Usage

```python
from coordinator import VideoAgent

agent = VideoAgent()
script = "Your story script here..."
result = agent.run(script)
print(result)
```

### Model Switching

To switch AI models, simply update the `MODEL` variable in `config.py`:

```python
MODEL = "grok-4"     # or "openai", "anthropic", etc.
```

### Running the API

```bash
cd backend
python api.py
```

The API will be available at `http://localhost:8000`

### API Endpoints

- `POST /create-video`: Create video plan from script
- `GET /health`: Health check
- `GET /`: API information

## Testing

Run unit tests:

```bash
python -m pytest tests/
```

Or run individual test modules:

```bash
python tests/test_utils.py
python tests/test_workers.py
python tests/test_coordinator.py
```

## Configuration

Key configuration options in `config.py`:

- `MODEL`: AI model selection
- `MAX_SCENES`: Limit scenes (default: 20)
- `MAX_CLIP_DURATION`: Max clip length (default: 30s)
- `MAX_NARRATION_WORDS`: Narration limit (default: 200)
- `FAMILY_FRIENDLY`: Content filtering (default: True)

## Development

### Design Principles

1. **Modularity**: Separate concerns with individual workers
2. **Model Agnosticism**: Easy switching between AI models
3. **No Hallucinations**: Ground all outputs in input data
4. **Iterative Development**: Start simple, expand gradually
5. **Comprehensive Testing**: 100% test coverage before integration

### Adding New Models

1. Add API endpoint to `ENDPOINTS` in `config.py`
2. Add API key to `API_KEYS` in `config.py`
3. Update `call_model()` in `utils.py` to handle the new model
4. Test by setting `MODEL` in config and running workflow

### Expansion Phases

- **Phase 1**: Text-based MVP (current)
- **Phase 2**: Real AI model integration
- **Phase 3**: Audio/video generation
- **Phase 4**: Advanced editing features

## License

MIT License
