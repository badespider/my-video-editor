#!/usr/bin/env python3

from coordinator import VideoAgent

# Read the sample script
with open('sample_script.txt', 'r', encoding='utf-8') as f:
    script = f.read()

print("Testing full pipeline with OpenAI...")
print(f"Script length: {len(script)} characters")

# Initialize the agent
agent = VideoAgent()

# Test individual workers
print("\n=== Testing Story Analyzer ===")
try:
    from workers import story_analyzer
    scenes_result = story_analyzer(script)
    print("Story analyzer result:", scenes_result[:200])
except Exception as e:
    print("Story analyzer error:", e)

print("\n=== Testing Clip Chooser ===")
try: 
    from workers import clip_chooser
    clips_result = clip_chooser(script)
    print("Clip chooser result:", clips_result[:200])
except Exception as e:
    print("Clip chooser error:", e)

print("\n=== Testing Full Agent ===")
try:
    result = agent.run(script)
    print("Full agent result keys:", list(result.keys()) if isinstance(result, dict) else type(result))
except Exception as e:
    print("Full agent error:", e)
