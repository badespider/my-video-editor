# Rule Plan to Improve Video Editing (Focus on Clips and Assembly, Hold Narration/BGM)

## Phase 1: Planning (Immediate)

**Rule 1.1: Audio Preservation Priority**
- Clips must retain original audio during extraction/assembly; no overwriting unless explicitly prompted.
- Mitigation: Config flag `PRESERVE_ORIGINAL_AUDIO = True` (default).

**Rule 1.2: Hold Narration/BGM**
- Disable narration/BGM workers by default; make optional via config (`ENABLE_NARRATION = False`, `ENABLE_BGM = False`).
- Mitigation: Log "On hold" if attempted.

**Rule 1.3: Editing Flexibility**
- `ClipChooser` supports user prompts for custom editing (e.g., "Trim to action scenes").
- Mitigation: Fallback to auto-selection if no prompt.

## Phase 2: Update Clip Extraction (Days 1-2)

**Rule 2.1: Preserve Audio in Extraction**
- Use MoviePy's subclip with `audio=True`; avoid re-encoding if possible.

**Implementation Steps:**
- Update `extract_clip` to copy audio.

**Code Example (utils.py):**
```python
def extract_clip(video_path, start, end, output_path):
    clip = VideoFileClip(video_path).subclip(start, end)
    clip.write_videofile(output_path, codec="libx264", audio_codec="aac")  # Preserve audio codec
    return output_path
```

**Testing:** Assert extracted clip has audio (check duration >0 with get_video_info).
- Mitigation: If audio fails, log and fallback to silent clip.

## Phase 3: Update Assembly for Original Audio (Days 3-4)

**Rule 3.1: Assembly Without Overwrite**
- Concatenate clips preserving their audio; skip narration/BGM if on hold.

**Implementation Steps:**
- Use `concatenate_videoclips` with audio preserved; conditional for held features.

**Code Example (utils.py):**
```python
def assemble_clips(clip_paths, narration=None, bgm=None, output_path="final.mp4"):
    clips = [VideoFileClip(p) for p in clip_paths]  # Keeps original audio
    final = concatenate_videoclips(clips)
    if config.ENABLE_NARRATION and narration:
        narration_clip = AudioFileClip(narration).volumex(0.8)
        final_audio = final.audio.overlay(narration_clip)
        final = final.set_audio(final_audio)
    if config.ENABLE_BGM and bgm:
        bgm_clip = AudioFileClip(bgm).volumex(0.3).set_duration(final.duration)
        final_audio = final.audio.overlay(bgm_clip)
        final = final.set_audio(final_audio)
    final.write_videofile(output_path)
    return output_path
```

**Testing:** Assert assembled video has original clip audios (manual check or audio duration match).
- Mitigation: Config to toggle; fallback to original if overlay fails.

**Rule 3.2: Prompt-Based Editing**
- `ClipChooser` accepts user prompt for selection (e.g., call_model to filter scenes).

**Implementation Steps:**
- Add prompt parameter to run; use for `_select_diverse_scenes`.

**Code Example (workers.py):**
```python
def run(self, analysis, prompt=None):
    scenes = analysis["scenes"]
    if prompt:
        filtered = call_model(f"Select scenes matching: {prompt}", scenes)
        scenes = filtered["scenes"]
    # Proceed with selection/extraction
...
```

**Testing:** Assert clips match prompt (e.g., "action" returns high-motion scenes).
- Mitigation: Default prompt if none.

## Phase 4: Integration (Days 5-6)

**Rule 4.1: Workflow Hold**
- Coordinator skips held workers (Narration/BGM) based on config.

**Implementation Steps:**
- Conditional in `run_with_video`.

**Code Example (coordinator.py):**
```python
def run_with_video(self, path):
    ingestion = IngestionWorker().run(path)
    clips = ClipChooserWorker().run(ingestion)
    if config.ENABLE_NARRATION:
        narration = NarrationWorker().run(clips)
    else:
        narration = None
    # Similar for BGM
    assembly = AssemblyWorker().run(clips, narration, bgm=None)
    return assembly
```

**Testing:** Assert no narration/BGM in output when held.
- Mitigation: Log skips.

**Rule 4.2: Cleanup**
- Ensure `cleanup_mocks` deletes audio temps too.

**Implementation Steps:**
- Expand cleanup_mocks for `.mp3`.

**Testing:** Assert no audio files left.
- Mitigation: Auto-run post-assembly.

## Phase 5: Testing/Expansion (Days 7+)

**Rule 5.1: Full Testing**
- End-to-end with vlog MP4; assert original audio preserved.
- Mitigation: Mock videos for CI.

**Rule 5.2: Model Switch**
- Test with Grok-4 for clip prompts.
- Mitigation: Backup if switch fails.

