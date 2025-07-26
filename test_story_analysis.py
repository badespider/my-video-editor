#!/usr/bin/env python3

from workers import StoryAnalysisWorker

# Read the sample script
with open('sample_script.txt', 'r', encoding='utf-8') as f:
    script = f.read()

print("Testing StoryAnalysisWorker with real OpenAI...")
print(f"Script length: {len(script)} characters")

# Test the story analysis worker
worker = StoryAnalysisWorker({})

try:
    result = worker.run(script)
    print("Story analysis result:")
    print(result)
except Exception as e:
    print(f"Story analysis error: {e}")
    import traceback
    traceback.print_exc()
