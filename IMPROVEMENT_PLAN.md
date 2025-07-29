# Improvement Plan: Fixing Narration and Audio Issues

## Current Problems Identified

The latest codebase (from the Repomix merged document) shows good progress on the core workflow and model flexibility, but I notice a few problems:

1. **Narration Generation**: The NarrationWorker uses a rule-based approach with generic prefixes (e.g., "In a dramatic turn of events"), leading to repetitive, non-content-specific narration that doesn't truly "narrate the content" (e.g., it doesn't reference specific scene details like "the detective enters the foggy alley").

2. **Audio Handling in Assembly**: The AssemblyWorker overwrites original audio when adding narration/BGM, effectively "deleting the original video sound." It also doesn't add new sound reliably in mocks, resulting in silent or incomplete outputs.

3. **BGM Integration**: BGM is suggested but not actually added to the audio mix in assembly, especially in mocks—it's text-only.

These issues make the final video feel generic and silent. To fix, we'll use a rule plan to enhance NarrationWorker for content-aware scripts, update AssemblyWorker to preserve/mix original audio, and ensure BGM/narration audio is generated/added. We'll use gTTS for TTS narration and mock/stock BGM, keeping modularity for model switches.

## Rule Plan to Fix Narration and Audio Issues

### Phase 1: Planning (Days 1-2)

**Rule 1.1: Content-Specific Narration**: Narration must be generated from scene descriptions/moods, not generic prefixes. Rule: Use call_model to prompt "Generate narration for this scene: [description], mood: [mood]", ensuring uniqueness.

**Rule 1.2: Audio Preservation**: Assembly must preserve original clip audio by mixing (narration over original, BGM under). Rule: Volume levels: Original 1.0, Narration 0.8, BGM 0.3.

**Rule 1.3: Real Audio Generation**: Use gTTS for narration audio; mock BGM with silence or stock. Rule: If no gTTS, fallback to text-only.

*Mitigation*: Config flag USE_REAL_AUDIO = False for mocks; test with short clips.

### Phase 2: Update NarrationWorker (Days 3-4)

**Rule 2.1: Dynamic Narration**: Generate per-clip, concatenate.

*Implementation Steps*: Update run to loop clips, call_model for segments.

*Code Example (workers.py)*:
```python
def run(self, clips_data: dict) -> dict:
    clips = clips_data["clips"]
    narration_parts = []
    for clip in clips:
        prompt = f"Generate narration for clip: {clip['description']}, mood: {clip['mood']}"
        segment = call_model(prompt, task_type="narration")
        narration_parts.append(segment)
    full_narration = " ".join(narration_parts)
    audio_path = generate_narration_audio(full_narration)
    return {"narration": full_narration, "audio_path": audio_path}
```

*Testing*: Unittest segments match descriptions; assert audio file created.

*Mitigation*: Fallback to generic if call_model fails.

### Phase 3: Update AssemblyWorker for Audio Mix (Days 5-6)

**Rule 3.1: Audio Mixing**: Overlay narration/BGM on original clip audio.

*Implementation Steps*: In assemble_clips, use MoviePy to mix (original + narration + BGM).

*Code Example (utils.py)*:
```python
def assemble_clips(clip_paths, narration_audio, bgm_path, output_path):
    clips = [VideoFileClip(p) for p in clip_paths]
    final = concatenate_videoclips(clips, method="compose")  # Preserve original audio
    if narration_audio:
        narration = AudioFileClip(narration_audio).volumex(0.8)
        final_audio = final.audio.overlay(narration)
        final = final.set_audio(final_audio)
    if bgm_path:
        bgm = AudioFileClip(bgm_path).volumex(0.3).set_duration(final.duration)
        final_audio = final.audio.overlay(bgm)
        final = final.set_audio(final_audio)
    final.write_videofile(output_path)
    return output_path
```

*Testing*: Assert original sound preserved in output MP4 (manual listen or wave comparison).

*Mitigation*: Config AUDIO_PRESERVE = True; fallback to mute if mix fails.

**Rule 3.2: BGM Addition**: Generate BGM audio mocks or use stock files.

*Implementation Steps*: Add create_bgm_mock in utils.py for placeholders.

*Testing*: Assert BGM added without overriding.

*Mitigation*: Silence if no BGM.

### Phase 4: Integration and Testing (Days 7-8)

**Rule 4.1: Workflow Updates**: Coordinator calls updated workers; validate audio in final plan.

*Implementation Steps*: Update run_with_video to include audio paths.

*Testing*: End-to-end with vlog MP4; assert narration content-specific and audio mixed.

*Mitigation*: Log if audio missing.

**Rule 4.2: Cleanup**: Delete temp audio/clips post-run.

*Implementation Steps*: Call cleanup_mocks in main.py.

*Testing*: Assert no temp files left.

*Mitigation*: Dev only.

### Phase 5: Expansion (Days 9+)

**Rule 5.1: Model Switch**: Test with gpt4.0 for narration prompts.

*Implementation Steps*: Update config; test.

*Testing*: Assert same quality.

*Mitigation*: Backup model.

## Implementation Priority

1. **High Priority**: Fix narration generation to be content-specific
2. **High Priority**: Preserve original audio during assembly
3. **Medium Priority**: Add real BGM mixing capabilities
4. **Low Priority**: Advanced model switching for narration quality

## Expected Outcomes

After implementing these improvements:
- Narration will describe actual scene content instead of generic phrases
- Final videos will preserve original audio while adding narration and music
- BGM will be properly mixed at appropriate volume levels
- Overall video quality will be significantly improved
