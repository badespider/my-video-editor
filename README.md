# Multi-Agent AI Video Creation System

A modular, multi-agent AI system for automated video creation from text scripts. Built following agentic AI design principles with support for easy model switching.

## Architecture

The system follows a multi-agent architecture with:
- **High-Level Planner (HLP)**: Coordinates the entire workflow
- **Low-Level Workers**: Handle specific tasks in the pipeline
- **Central Configuration**: Enables easy model switching

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      CONFIG.PY                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │   MODEL = ...   │    │   API_KEYS      │    │ ENDPOINTS   │ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │   CALL_MODEL    │
                          │   (utils.py)    │
                          └─────────────────┘
                                   │
                                   ▼
           ┌─────────────────────────────────────────────────────┐
           │          HIGH-LEVEL PLANNER (HLP)                  │
           │              VideoAgent Class                      │
           │             (coordinator.py)                       │
           └─────────────────────────────────────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │ STORY ANALYSIS  │  │ CLIP SELECTION  │  │   NARRATION     │
    │     Worker      │  │     Worker      │  │     Worker      │
    │  (workers.py)   │  │  (workers.py)   │  │  (workers.py)   │
    └─────────────────┘  └─────────────────┘  └─────────────────┘
              │                    │                    │
              └────────────────────┼────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │ BGM SELECTION   │  │    ASSEMBLY     │  │ SHARED STATE    │
    │     Worker      │  │     Worker      │  │ get_environment │
    │  (workers.py)   │  │  (workers.py)   │  │   (memory)      │
    └─────────────────┘  └─────────────────┘  └─────────────────┘
              │                    │                    │
              └────────────────────┼────────────────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │ FINAL JSON PLAN │
                          │   {"scenes":... │
                          │ "final_video":  │
                          │    "plan.mp4"}  │
                          └─────────────────┘
```

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

#### Core Dependencies

```bash
pip install game-by-virtuals fastapi uvicorn[standard]
```

#### Optional Video Processing Dependencies

For full video processing capabilities, install FFmpeg and MoviePy:

**FFmpeg Installation:**
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt update && sudo apt install ffmpeg`

**Python Video Libraries:**
```bash
# Essential video processing
pip install moviepy

# Advanced scene detection
pip install scenedetect

# Text-to-speech capabilities
pip install gTTS

# Complete video processing stack
pip install moviepy scenedetect gTTS opencv-python
```

**Note**: The system works without these dependencies using fallback mechanisms (see Fallback Behavior section below).

### CLI Usage

The main entry point supports multiple input methods:

**Demo Mode (uses sample script):**
```bash
python main.py --demo
```

**Script File Input:**
```bash
python main.py --script path/to/your/script.txt
```

**STDIN Input:**
```bash
echo "Your story script here..." | python main.py
```

**Save Output to File:**
```bash
python main.py --demo --output output.json
python main.py --script script.txt --output result.json
```

### Programmatic Usage

```python
from coordinator import VideoAgent

agent = VideoAgent()
script = "Your story script here..."
result = agent.run(script)
print(result)
```

### Model Switching

**Method 1: Environment Variable (Recommended)**

Set the `MODEL` environment variable to switch AI models:

```bash
# Switch to Grok-4
export MODEL=grok-4
python main.py --demo

# Switch to OpenAI
export MODEL=openai
python main.py --demo

# Switch to Anthropic
export MODEL=anthropic
python main.py --demo
```

**Method 2: Configuration File**

Alternatively, update the `MODEL` variable in `config.py`:

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

### Running Tests

Run all unit tests with pytest:

```bash
python -m pytest tests/
```

#### Fallback Behavior

- If `MoviePy` or `FFmpeg` is not installed, tests that require video processing will be skipped gracefully with appropriate warnings.
- Mock implementations will be used to simulate video processing tasks where possible.
- Ensure environment variables `MOCK_FFMPEG` is set to `1` to activate full mocking.
- Preserve test video outputs by setting `KEEP_TEST_VIDS` environment variable to any non-empty value.

Run individual test modules:

```bash
python tests/test_utils.py
python tests/test_workers.py
python tests/test_coordinator.py
```

### Test Coverage

Generate test coverage report:

```bash
pip install coverage
coverage run -m pytest tests/
coverage report -m
coverage html  # Generates HTML coverage report
```

### Testing Model Switching

Test switching between models:

```bash
# Test with mock model (default)
python main.py --demo

# Test environment variable switching
export MODEL=grok-4
python main.py --demo

# Test fallback behavior
export MODEL=invalid-model
python main.py --demo  # Should fallback to mock
```

### Integration Testing

Test the full workflow:

```bash
# Test CLI with different inputs
echo "Once upon a time..." | python main.py --output test_output.json
python main.py --script samples/test_script.txt --output integration_test.json

# Test API endpoints
cd backend
python api.py &
curl -X POST http://localhost:8000/create-video \
  -H "Content-Type: application/json" \
  -d '{"script": "Your test script here..."}'
curl http://localhost:8000/health
```

### Performance Testing

Benchmark the system with larger scripts:

```bash
# Time execution
time python main.py --script large_script.txt

# Memory profiling (requires memory_profiler)
pip install memory_profiler
python -m memory_profiler main.py --demo
```

## Configuration

Key configuration options in `config.py`:

- `MODEL`: AI model selection
- `MAX_SCENES`: Limit scenes (default: 20)
- `MAX_CLIP_DURATION`: Max clip length (default: 30s)
- `MAX_NARRATION_WORDS`: Narration limit (default: 200)
- `FAMILY_FRIENDLY`: Content filtering (default: True)

### Environment Variables

The system recognizes several environment variables for customizing behavior:

#### Testing and Development
- `MOCK_FFMPEG=1`: Enable mock video processing for testing environments where FFmpeg/MoviePy are unavailable
- `KEEP_TEST_VIDS=1`: Preserve generated test video files instead of cleaning them up automatically
- `LOG_LEVEL=DEBUG`: Set logging verbosity (DEBUG, INFO, WARNING, ERROR)

#### Video Processing Fallbacks
- `ENABLE_FFMPEG=1`: Enable FFmpeg-based video processing (requires FFmpeg binary in PATH)
- `ENABLE_MEMORIES_AI=1`: Enable Memories.ai integration (when API key is available)
- `VIDEO_OUTPUT_DIR=./output`: Override default video output directory
- `UPLOAD_DIR=./uploads`: Override default upload directory

#### Model Configuration
- `MODEL=grok-4`: Override model selection from config.py
- `GROK_API_KEY=your_key`: API key for Grok model access
- `OPENAI_API_KEY=your_key`: API key for OpenAI model access
- `ANTHROPIC_API_KEY=your_key`: API key for Anthropic model access

#### Example Usage
```bash
# Run tests with full mocking enabled
MOCK_FFMPEG=1 KEEP_TEST_VIDS=1 python -m pytest tests/

# Run with specific model and debug logging
MODEL=grok-4 LOG_LEVEL=DEBUG python main.py --demo

# Production setup with real video processing
ENABLE_FFMPEG=1 VIDEO_OUTPUT_DIR=/var/videos python backend/api.py
```

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

### Git Branching Strategy

We follow a simplified Git flow with feature branches:

#### Branch Structure

```
main                  # Production-ready code
├── develop          # Integration branch for features
├── feature/xyz      # Feature development branches
├── bugfix/abc       # Bug fixes
├── hotfix/urgent    # Critical production fixes
└── release/v1.x     # Release preparation branches
```

#### Workflow

1. **Feature Development**:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/add-grok4-support
   
   # Make your changes and commits
   git add .
   git commit -m "Add Grok-4 model support with API integration"
   
   # Push and create PR
   git push origin feature/add-grok4-support
   ```

2. **Bug Fixes**:
   ```bash
   git checkout develop
   git checkout -b bugfix/fix-narration-sync
   
   # Fix the bug and test
   git commit -m "Fix narration synchronization with clips"
   git push origin bugfix/fix-narration-sync
   ```

3. **Hotfixes** (critical production issues):
   ```bash
   git checkout main
   git checkout -b hotfix/security-patch
   
   # Apply critical fix
   git commit -m "Security: patch API key exposure vulnerability"
   git push origin hotfix/security-patch
   ```

#### Branch Naming Conventions

- `feature/description`: New features or enhancements
- `bugfix/description`: Bug fixes
- `hotfix/description`: Critical production fixes
- `release/v1.x`: Release preparation
- `docs/description`: Documentation updates
- `test/description`: Test improvements

#### Merge Requirements

- All tests must pass: `python -m pytest tests/`
- Code coverage must be ≥95%
- Peer review required for all PRs
- No direct pushes to `main` or `develop`

### Contributing Guidelines

#### Before You Start

1. **Check existing issues** and PRs to avoid duplication
2. **Fork the repository** if you're an external contributor
3. **Set up your development environment**:
   ```bash
   git clone https://github.com/your-org/multi-agent-ai-video.git
   cd multi-agent-ai-video
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Testing dependencies
   ```

#### Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout develop
   git checkout -b feature/your-feature-name
   ```

2. **Follow coding standards**:
   - Use Python 3.12+ features
   - Follow PEP 8 style guidelines
   - Add type hints where possible
   - Document functions with docstrings
   - Keep functions focused and testable

3. **Write comprehensive tests**:
   ```bash
   # Test your changes
   python -m pytest tests/test_your_module.py -v
   
   # Check coverage
   coverage run -m pytest tests/
   coverage report -m
   ```

4. **Lint and format code**:
   ```bash
   # Install development tools
   pip install black flake8 mypy
   
   # Format code
   black .
   
   # Check linting
   flake8 .
   
   # Type checking
   mypy .
   ```

5. **Test with different models**:
   ```bash
   # Test with mock (default)
   python main.py --demo
   
   # Test model switching
   export MODEL=grok-4
   python main.py --demo
   ```

#### Pull Request Guidelines

1. **PR Title Format**: `[TYPE] Brief description`
   - `[FEATURE]` - New functionality
   - `[BUGFIX]` - Bug fixes
   - `[DOCS]` - Documentation updates
   - `[TEST]` - Test improvements
   - `[REFACTOR]` - Code refactoring

2. **PR Description Template**:
   ```markdown
   ## Summary
   Brief description of changes
   
   ## Changes Made
   - List of specific changes
   - Include any breaking changes
   
   ## Testing
   - [ ] All existing tests pass
   - [ ] New tests added for new functionality
   - [ ] Manual testing completed
   - [ ] Model switching tested
   
   ## Checklist
   - [ ] Code follows project style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated if needed
   - [ ] No breaking changes (or clearly documented)
   ```

3. **Review Process**:
   - Assign appropriate reviewers
   - Address all review comments
   - Keep PR scope focused and small
   - Squash commits before merging

#### Code Quality Standards

- **Test Coverage**: Minimum 95% coverage required
- **Documentation**: All public functions must have docstrings
- **Error Handling**: Comprehensive try/catch blocks with logging
- **Model Agnosticism**: All AI calls must go through `call_model()`
- **Configuration**: Use `config.py` for all settings
- **Backwards Compatibility**: Maintain API compatibility when possible

#### Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Create a GitHub Issue with reproduction steps
- **Feature Requests**: Open an Issue with detailed requirements
- **Security Issues**: Email maintainers directly

#### Recognition

Contributors are acknowledged in:
- `CONTRIBUTORS.md` file
- Release notes for significant contributions
- GitHub contributor graphs

## License

MIT License
