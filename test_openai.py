#!/usr/bin/env python3

import utils
import os

print("Testing OpenAI integration...")
print(f"OPENAI_API_KEY set: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
print(f"Has OpenAI module: {utils.HAS_OPENAI}")

# Test basic call
result = utils.call_model("Hello, respond with JSON: {\"message\": \"Hello World\"}", model="openai")
print("Result:", result[:200])
