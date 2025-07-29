#!/usr/bin/env python3
"""
Test script for enhanced narration system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workers.workers import NarrationWorker
import json

def test_enhanced_narration():
    """Test the enhanced narration with sample clips"""
    
    # Create sample clips with rich descriptions
    test_clips = [
        {
            "id": "clip_1",
            "description": "A young anime character with spiky blue hair runs through a bustling marketplace filled with colorful stalls and floating lanterns, dodging merchants and customers while chasing a mysterious hooded figure",
            "start": 0,
            "end": 30,
            "duration": 30,
            "file_path": "test_clip_1.mp4"
        },
        {
            "id": "clip_2", 
            "description": "Inside a dimly lit ancient library, magical books float in the air while a wise old wizard with a long white beard examines glowing runes on stone tablets, his staff pulsing with ethereal energy",
            "start": 45,
            "end": 75,
            "duration": 30,
            "file_path": "test_clip_2.mp4"
        },
        {
            "id": "clip_3",
            "description": "On a windswept mountain peak at sunset, two rival warriors face each other in combat stance, their weapons gleaming as cherry blossom petals swirl around them in the golden light",
            "start": 120,
            "end": 150,
            "duration": 30,
            "file_path": "test_clip_3.mp4"
        }
    ]
    
    print("=== Testing Enhanced Narration System ===\n")
    
    # Initialize narration worker with state
    narration_worker = NarrationWorker(state={})
    
    # Test narration generation for each clip
    for i, clip in enumerate(test_clips, 1):
        print(f"--- Clip {i}: Testing Narration Generation ---")
        print(f"Scene Description: {clip['description'][:100]}...")
        
        # Test visual element extraction
        visual_elements = narration_worker._extract_visual_elements(clip['description'])
        print(f"\nExtracted Visual Elements: {visual_elements}")
        
        # Test AI narration generation (will likely fall back to intelligent fallback)
        try:
            ai_narration = narration_worker._generate_ai_narration_segment(
                clip['description'], clip.get('mood', 'neutral'), clip['duration'], i-1
            )
            print(f"\nAI Narration Attempt: {ai_narration}")
        except Exception as e:
            print(f"\nAI Narration Failed: {e}")
            ai_narration = "[AI Failed]"
        
        # Test intelligent fallback narration
        fallback_narration = narration_worker._generate_intelligent_fallback(
            clip['description'], clip.get('mood', 'neutral')
        )
        print(f"Intelligent Fallback: {fallback_narration}")
        
        # Test generic detection
        is_generic = narration_worker._is_narration_generic(fallback_narration)
        print(f"Is Generic: {is_generic}")
        
        print("-" * 60)
    
    # Test full narration workflow
    print("\n=== Full Narration Workflow Test ===")
    clips_data = {"clips": test_clips}
    narration_result = narration_worker.run(clips_data)
    
    print(f"\nFinal Narration Result:")
    print(f"Narration: {narration_result.get('narration', 'none')[:200]}...")
    print(f"Audio Path: {narration_result.get('audio_path', 'none')}")
    print(f"Word Count: {narration_result.get('word_count', 0)}")
    print(f"Segment Count: {narration_result.get('segment_count', 0)}")
    
    print("\n=== Enhanced Narration Test Complete ===")

if __name__ == "__main__":
    test_enhanced_narration()
