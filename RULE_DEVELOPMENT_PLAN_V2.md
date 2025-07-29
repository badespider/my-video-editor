# AI Video Editor - Rule Development Plan V2
## 10-Day Implementation Roadmap

---

## Phase 1: Planning and Setup (Days 1-2)

### Rule 1.1: Clean Outputs and Parsing
**Requirement:** Eliminate escaped JSON in narration outputs and standardize all JSON responses across the system.

#### Implementation Steps:
1. Update `_validate_narration` and similar methods to strip escapes and validate structure
2. Add a global `_clean_json_output` helper in `utils.py` for all workers
3. Apply cleaning post-execution in coordinator workflow

#### Code Example (utils.py - New Helper):
```python
import re

def _clean_json_output(text: str) -> str:
    """Strip escaped JSON and common artifacts from AI responses"""
    # Remove escapes and newlines
    text = re.sub(r'\\n|\\', '', text)
    
    # Clean outer braces if needed
    text = re.sub(r'^\{.*\}$', lambda m: m.group(0).strip(), text)
    
    # Remove extra quotes around JSON strings
    text = re.sub(r'^"(.*)"$', r'\1', text)
    
    return text.strip()
```

#### Testing:
- Assert cleaned narration has no `"\n"` (e.g., from 21-word test); 100% clean in 10 sample outputs
- Unittest with mocked escaped JSON; integration in `test_phase3_integration.py`

#### Mitigation:
- Fallback to original if cleaning fails; log "Output cleaned" for auditing

---

### Rule 1.2: Refine Prompts and Editing Preparation
**Requirement:** Enhance prompt parsing to handle advanced commands (e.g., "speed:1.5x") and implement basic effects.

#### Implementation Steps:
1. Expand `_parse_edit_prompt` to support new params (speed, effects); validate ranges (speed 0.5-2.0)
2. Prep `_apply_effects` with MoviePy for fade/speed
3. Add comprehensive parameter validation

#### Code Example (workers.py - Update Parse):
```python
def _parse_edit_prompt(self, prompt):
    """Enhanced prompt parsing with validation"""
    response = call_model(
        f"Parse edit params: {prompt}. JSON: {{type:str, params:dict}}.", 
        "gpt-4"
    )
    params = json.loads(response).get("params", {})
    
    # Validate speed (0.5x to 2.0x range)
    if 'speed' in params:
        speed_val = float(params['speed'])
        params['speed'] = max(0.5, min(2.0, speed_val))
        
    # Validate effects
    valid_effects = ['fade_in', 'fade_out', 'blur', 'contrast']
    if 'effects' in params:
        params['effects'] = [e for e in params['effects'] if e in valid_effects]
    
    return params
```

#### Testing:
- Assert "speed:3.0" clamps to 2.0; effects like "fade" parsed correctly
- Unittest with GPT mocks; end-to-end in `test_phase4_integration.py`

#### Mitigation:
- Default values if invalid (e.g., speed=1.0); log parsed vs original prompt

---

### Rule 1.3: Performance Boost Setup
**Requirement:** Implement FFmpeg for faster extraction and RESOURCE_LIMIT checks.

#### Implementation Steps:
1. Add FFmpeg toggle/subprocess in `extract_clip`; check `os.cpu_count()` for workers
2. Add memory monitoring in `chunk_video`
3. Implement resource management and fallbacks

#### Code Example (utils.py - FFmpeg Update):
```python
import subprocess
import psutil
import os

def extract_clip(video_path: str, start_time: float, end_time: float, output_path: str):
    """Enhanced clip extraction with FFmpeg support and resource monitoring"""
    
    # Check system resources
    if psutil.virtual_memory().available < config.MEMORY_LIMIT:
        raise MemoryError("Insufficient memory for video processing")
    
    if config.ENABLE_FFMPEG and _check_ffmpeg_available():
        try:
            # FFmpeg extraction (faster)
            cmd = [
                'ffmpeg', '-i', video_path, 
                '-ss', str(start_time), 
                '-to', str(end_time),
                '-c', 'copy',  # Stream copy for speed
                '-avoid_negative_ts', 'make_zero',
                output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                logger.info(f"FFmpeg extraction successful: {output_path}")
                return output_path
            else:
                logger.warning(f"FFmpeg failed, falling back to MoviePy: {result.stderr}")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"FFmpeg error: {e}, falling back to MoviePy")
    
    # Fallback to MoviePy
    return _extract_clip_moviepy(video_path, start_time, end_time, output_path)

def _check_ffmpeg_available() -> bool:
    """Check if FFmpeg is available on system"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
```

#### Testing:
- Benchmark: FFmpeg 2x faster than MoviePy; assert MemoryError on low RAM sim
- Stress test: 1hr video with chunks

#### Mitigation:
- Fallback to MoviePy; reduce chunks if low memory

---

### Rule 1.4: Testing and Docs Expansion Prep
**Requirement:** Plan legacy updates and new sections.

#### Implementation Steps:
1. List outdated tests; draft "Editing Guide" with examples
2. Add Memories.ai docs placeholder
3. Set up comprehensive test coverage tracking

#### Testing:
- Baseline coverage >95%
- Review drafts

#### Mitigation:
- Incremental commits

---

## Phase 2: Implementation - Cleaning & Refinements (Days 3-5)

### Rule 2.1: Implement Output Cleaning
**Requirement:** Apply `_clean_json_output` to all worker results.

#### Implementation Steps:
1. Call in `_execute_with_retry` post-execution
2. Update all worker output processing
3. Add validation for cleaned outputs

#### Code Example (coordinator.py):
```python
def _execute_with_retry(self, worker_method, input_data, worker_name, max_retries=3):
    """Execute worker with retry logic and output cleaning"""
    for attempt in range(max_retries):
        try:
            # Execute worker
            output = worker_method(input_data)
            
            # Clean JSON output if it's a string response
            if isinstance(output, str):
                cleaned_output = _clean_json_output(output)
                try:
                    # Validate it's proper JSON
                    output = json.loads(cleaned_output)
                    logger.info(f"Output cleaned for {worker_name}")
                except json.JSONDecodeError:
                    logger.warning(f"Cleaning failed for {worker_name}, using original")
            
            return output
            
        except Exception as e:
            logger.warning(f"{worker_name} attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
    
    return None
```

#### Testing:
- Assert no escapes in narration; consistent JSON across tests
- Integration: Check results JSONs clean

#### Mitigation:
- If cleaning alters data, log diff; fallback to raw

---

### Rule 2.2: Refine Prompts and Add Effects
**Requirement:** Implement speed/fade in `_apply_effects`; call in assembly.

#### Implementation Steps:
1. Use MoviePy fx.speedx/fadein; apply if in params
2. Integrate effects pipeline into clip processing
3. Add audio preservation during effects

#### Code Example (workers.py):
```python
from moviepy.video.fx.all import speedx, fadein, fadeout

def _apply_effects(self, clip_path: str, params: dict) -> str:
    """Apply visual effects to video clips"""
    if not params:
        return clip_path
    
    try:
        clip = VideoFileClip(clip_path)
        original_audio = clip.audio
        effects_applied = []
        
        # Apply speed effect
        if 'speed' in params and params['speed'] != 1.0:
            clip = clip.fx(speedx, params['speed'])
            effects_applied.append(f"speed:{params['speed']}")
        
        # Apply fade effects
        if 'fade_in' in params.get('effects', []):
            clip = clip.fx(fadein, 2)  # 2 second fade in
            effects_applied.append("fade_in")
            
        if 'fade_out' in params.get('effects', []):
            clip = clip.fx(fadeout, 2)  # 2 second fade out
            effects_applied.append("fade_out")
        
        # Preserve audio if not speed-affected
        if 'speed' not in params and original_audio:
            clip = clip.with_audio(original_audio)
        
        # Write enhanced clip
        if effects_applied:
            enhanced_path = clip_path.replace('.mp4', '_enhanced.mp4')
            clip.write_videofile(enhanced_path, verbose=False, logger=None)
            clip.close()
            logger.info(f"Effects applied: {', '.join(effects_applied)}")
            return enhanced_path
        
        clip.close()
        return clip_path
        
    except Exception as e:
        logger.error(f"Effects application failed: {e}")
        return clip_path
```

#### Testing:
- Assert speed 1.5 halves duration; fade doesn't change length
- Prompt: "speed:1.5, fade" applies both

#### Mitigation:
- Skip if params invalid; preserve audio in fx

---

## Phase 3: Implementation - Performance & Integration (Days 6-7)

### Rule 3.1: Boost Extraction & Monitoring
**Requirement:** Integrate FFmpeg and memory checks in core ops.

#### Implementation Steps:
1. Toggle in config; add to `motion_score`/`chunk_video`
2. Implement parallel processing where safe
3. Add performance metrics collection

#### Code Example (utils.py - Performance Monitoring):
```python
import time
from concurrent.futures import ThreadPoolExecutor
import threading

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
        self.lock = threading.Lock()
    
    def start_timer(self, operation: str):
        with self.lock:
            self.metrics[operation] = {'start': time.time()}
    
    def end_timer(self, operation: str):
        with self.lock:
            if operation in self.metrics:
                self.metrics[operation]['duration'] = time.time() - self.metrics[operation]['start']
                self.metrics[operation]['memory'] = psutil.virtual_memory().used

def chunk_video_parallel(video_path: str, chunk_duration: int = 30):
    """Parallel video chunking with performance monitoring"""
    monitor = PerformanceMonitor()
    monitor.start_timer('chunk_video')
    
    # Check resources
    available_cores = os.cpu_count()
    max_workers = min(4, available_cores)  # Limit concurrent processes
    
    video_info = get_video_info(video_path)
    duration = video_info['duration']
    chunks = []
    
    # Create chunk tasks
    chunk_tasks = []
    for i in range(0, int(duration), chunk_duration):
        end_time = min(i + chunk_duration, duration)
        chunk_tasks.append((i, end_time))
    
    # Process chunks in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for start, end in chunk_tasks:
            future = executor.submit(extract_clip, video_path, start, end, 
                                   f"temp/chunk_{start}_{end}.mp4")
            futures.append(future)
        
        for future in futures:
            chunk_path = future.result()
            if chunk_path:
                chunks.append(chunk_path)
    
    monitor.end_timer('chunk_video')
    logger.info(f"Chunking completed: {len(chunks)} chunks in {monitor.metrics['chunk_video']['duration']:.2f}s")
    
    return chunks
```

#### Testing:
- Assert faster extraction (>50% time save); MemoryError handled
- Load test: No crashes on large files

#### Mitigation:
- Disable FFmpeg for low-spec; reduce quality

---

### Rule 3.2: Integrate Changes
**Requirement:** Update workflows to use new features; validate in tests.

#### Implementation Steps:
1. Call `_apply_effects` in ClipChooser if prompted; clean outputs in coordinator
2. Update assembly pipeline to use enhanced clips
3. Add comprehensive logging and metrics

#### Testing:
- End-to-end: Real video with advanced prompt yields clean, edited JSON
- Coverage >95%

#### Mitigation:
- Log performance metrics per run

---

## Phase 4: Expansion - Tests & Docs (Days 8-9)

### Rule 4.1: Update Legacy Tests
**Requirement:** Rewrite outdated tests for current code.

#### Implementation Steps:
1. Update `test_utils_lines_73_74.py` etc., to match new lines
2. Add comprehensive integration tests
3. Create performance benchmarks

#### Code Example (tests/test_enhanced_features.py):
```python
import pytest
from unittest.mock import patch, MagicMock
from utils.utils import _clean_json_output, extract_clip
from workers.workers import ClipChooserWorker

class TestEnhancedFeatures:
    
    def test_json_cleaning(self):
        """Test JSON output cleaning"""
        escaped_json = '"{\"narration\": \"This is a\\ntest story\"}"'
        cleaned = _clean_json_output(escaped_json)
        assert '\\n' not in cleaned
        assert cleaned.startswith('{')
        
    def test_prompt_parsing_advanced(self):
        """Test advanced prompt parsing with effects"""
        worker = ClipChooserWorker()
        
        with patch('utils.utils.call_model') as mock_call:
            mock_call.return_value = '{"type": "edit", "params": {"speed": 1.5, "effects": ["fade_in"]}}'
            
            params = worker._parse_edit_prompt("Make it faster with fade in")
            
            assert params['speed'] == 1.5
            assert 'fade_in' in params['effects']
    
    @patch('subprocess.run')
    def test_ffmpeg_extraction(self, mock_subprocess):
        """Test FFmpeg extraction path"""
        mock_subprocess.return_value = MagicMock(returncode=0)
        
        with patch('config.ENABLE_FFMPEG', True):
            result = extract_clip('test.mp4', 0, 10, 'output.mp4')
            
            mock_subprocess.assert_called_once()
            assert 'ffmpeg' in mock_subprocess.call_args[0][0][0]
```

#### Testing:
- All pass; add Memories.ai sim tests (mock API → GPT)

#### Mitigation:
- CI for legacy migration

---

### Rule 4.2: Enhance Documentation
**Requirement:** Add detailed sections with examples.

#### Implementation Steps:
1. Expand README: "Editing Guide" (prompt examples); "Memories.ai" (placeholder)
2. Create API documentation
3. Add troubleshooting guide

#### Code Example (README_EDITING_GUIDE.md):
```markdown
# Video Editing Guide

## Advanced Prompts

### Speed Control
- `"Make the action scenes 1.5x faster"` → Applies speed:1.5 to high-motion clips
- `"Slow down the dialogue to 0.8x"` → Applies speed:0.8 to conversation scenes

### Visual Effects
- `"Add fade transitions between scenes"` → Applies fade_in/fade_out effects
- `"Enhance the dramatic moments with slow motion"` → Combines speed:0.5 + fade effects

### Combined Commands
- `"Speed up action by 1.2x and add fade effects"` → Multiple parameters parsed

## Memories.ai Integration

**Current Status:** Placeholder mode using GPT-4 for visual analysis.

**Enable Real API:** Set `MEMORIES_API_KEY` in environment when available.

**Current Functionality:**
- Object detection simulation
- Mood analysis via GPT prompts
- Scene classification enhancement

**Future Features:**
- Real-time visual memory queries
- Advanced object tracking
- Emotion detection in faces
```

#### Testing:
- Validate examples run; links work

#### Mitigation:
- Version docs

---

## Phase 5: Memories.ai Placeholder & Final Testing (Day 10)

### Rule 5.1: Activate Memories.ai Placeholder
**Requirement:** Use GPT for analysis now; prep real switch.

#### Implementation Steps:
1. In analysis funcs, call placeholder (GPT prompt: "Analyze for objects")
2. Create seamless API switching mechanism
3. Add comprehensive visual analysis features

#### Code Example (utils.py):
```python
def analyze_scene_enhanced(video_path: str, timestamp: float = None):
    """Enhanced scene analysis with Memories.ai placeholder"""
    
    if config.MEMORIES_API_KEY and config.ENABLE_MEMORIES_AI:
        # Future: Real Memories.ai API call
        return _call_memories_api(video_path, timestamp)
    else:
        # Current: GPT-powered visual analysis
        return call_memories_placeholder(video_path, timestamp)

def call_memories_placeholder(video_path: str, timestamp: float = None):
    """GPT-powered visual analysis simulating Memories.ai capabilities"""
    
    # Extract frame for analysis (if timestamp provided)
    frame_context = ""
    if timestamp:
        frame_context = f" at timestamp {timestamp}s"
    
    analysis_prompt = f"""
    Analyze this video{frame_context} and provide detailed visual information:
    
    1. Objects and entities present
    2. Emotional mood and atmosphere
    3. Visual style and cinematography
    4. Key actions or movements
    5. Lighting and color palette
    6. Architectural or environmental details
    
    Return as JSON with keys: objects, mood, style, actions, lighting, environment
    """
    
    try:
        response = call_model(analysis_prompt, task_type="visual_analysis")
        analysis = json.loads(response)
        
        # Enhance with additional context
        analysis['source'] = 'gpt_placeholder'
        analysis['timestamp'] = timestamp
        analysis['confidence'] = 0.8  # Simulated confidence
        
        logger.info(f"Visual analysis completed for {video_path}{frame_context}")
        return analysis
        
    except Exception as e:
        logger.error(f"Visual analysis failed: {e}")
        return {
            'objects': ['unknown'],
            'mood': 'neutral',
            'style': 'standard',
            'actions': ['static'],
            'lighting': 'normal',
            'environment': 'indoor',
            'source': 'fallback',
            'error': str(e)
        }
```

#### Testing:
- Assert enhances scenes (e.g., add "objects: car"); toggle works

#### Mitigation:
- Config disable; log mode

---

### Rule 5.2: Comprehensive Testing
**Requirement:** Full e2e with new features.

#### Implementation Steps:
1. Run all tests; benchmark improvements
2. Create comprehensive integration scenarios
3. Performance validation and optimization

#### Code Example (tests/test_complete_pipeline.py):
```python
class TestCompletePipeline:
    
    def test_end_to_end_with_enhancements(self):
        """Complete pipeline test with all new features"""
        
        # Setup test video and script
        test_video = "test_data/sample_video.mp4"
        test_script = """
        Scene 1: Action sequence with fast-paced combat
        Scene 2: Emotional dialogue between characters  
        Scene 3: Scenic landscape with slow camera movement
        """
        
        # Configure for enhanced processing
        with patch.multiple(config, 
                          ENABLE_FFMPEG=True,
                          ENABLE_MEMORIES_AI=True,
                          PRESERVE_ORIGINAL_AUDIO=True):
            
            # Run complete pipeline
            agent = VideoAgent()
            result = agent.run_with_video(test_script, test_video)
            
            # Validate enhancements
            assert 'enhanced_clips' in result
            assert 'visual_analysis' in result
            assert len(result['clips']) > 0
            
            # Check for applied effects
            for clip in result['clips']:
                if 'action' in clip['description'].lower():
                    assert clip.get('speed', 1.0) > 1.0  # Action scenes sped up
                elif 'dialogue' in clip['description'].lower():
                    assert clip.get('effects') is None  # Dialogue preserved
            
            # Validate clean JSON outputs
            for narration in result['narrations']:
                assert '\\n' not in str(narration)
                assert isinstance(narration, dict)
    
    def test_performance_benchmarks(self):
        """Validate performance improvements"""
        
        large_video = "test_data/large_video.mp4"  # 10+ minutes
        
        start_time = time.time()
        
        # Test with FFmpeg enabled
        with patch('config.ENABLE_FFMPEG', True):
            clips = chunk_video_parallel(large_video, chunk_duration=60)
        
        ffmpeg_time = time.time() - start_time
        
        start_time = time.time()
        
        # Test with MoviePy only
        with patch('config.ENABLE_FFMPEG', False):
            clips_moviepy = chunk_video(large_video, chunk_duration=60)
        
        moviepy_time = time.time() - start_time
        
        # Assert significant performance improvement
        assert ffmpeg_time < moviepy_time * 0.7  # At least 30% faster
        assert len(clips) == len(clips_moviepy)  # Same output quality
```

#### Testing:
- 100% pass; prompts in guide work
- Performance benchmarks meet targets

#### Mitigation:
- Fix any failures before close

---

## Configuration Updates Required

### config.py Additions:
```python
# Performance Settings
ENABLE_FFMPEG = os.getenv('ENABLE_FFMPEG', 'false').lower() == 'true'
MEMORY_LIMIT = int(os.getenv('MEMORY_LIMIT', '2147483648'))  # 2GB default
MAX_PARALLEL_WORKERS = int(os.getenv('MAX_PARALLEL_WORKERS', '4'))

# Memories.ai Integration
MEMORIES_API_KEY = os.getenv('MEMORIES_API_KEY', '')
ENABLE_MEMORIES_AI = bool(MEMORIES_API_KEY) and os.getenv('ENABLE_MEMORIES_AI', 'false').lower() == 'true'

# Output Cleaning
ENABLE_JSON_CLEANING = os.getenv('ENABLE_JSON_CLEANING', 'true').lower() == 'true'
STRICT_JSON_VALIDATION = os.getenv('STRICT_JSON_VALIDATION', 'false').lower() == 'true'

# Advanced Features
ENABLE_ADVANCED_EFFECTS = os.getenv('ENABLE_ADVANCED_EFFECTS', 'true').lower() == 'true'
DEFAULT_FADE_DURATION = float(os.getenv('DEFAULT_FADE_DURATION', '2.0'))
SPEED_LIMIT_MIN = float(os.getenv('SPEED_LIMIT_MIN', '0.5'))
SPEED_LIMIT_MAX = float(os.getenv('SPEED_LIMIT_MAX', '2.0'))
```

---

## Success Metrics

### Phase 1-2 (Days 1-5):
- [ ] 100% JSON outputs free of escape characters
- [ ] Advanced prompt parsing with 95% accuracy
- [ ] FFmpeg integration with 50%+ speed improvement
- [ ] All legacy tests updated and passing

### Phase 3-4 (Days 6-9):
- [ ] Performance monitoring and resource management active
- [ ] Effects pipeline integrated and tested
- [ ] Comprehensive documentation with working examples
- [ ] Test coverage maintained above 95%

### Phase 5 (Day 10):
- [ ] Memories.ai placeholder fully functional
- [ ] Complete pipeline passing all integration tests
- [ ] Performance benchmarks meeting targets
- [ ] System ready for production deployment

---

## Risk Mitigation

### Technical Risks:
- **FFmpeg availability**: Automatic fallback to MoviePy
- **Memory constraints**: Dynamic resource management and chunking
- **API failures**: Robust retry logic and fallbacks
- **Performance degradation**: Continuous monitoring and optimization

### Integration Risks:
- **Breaking changes**: Comprehensive testing before deployment
- **Data corruption**: Validation and backup mechanisms
- **Legacy compatibility**: Gradual migration with parallel support

---

*This plan provides a structured approach to implementing advanced features while maintaining system stability and performance. Each phase builds upon previous work and includes comprehensive testing and validation.*
