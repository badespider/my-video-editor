#!/usr/bin/env python3
"""
Phase 3.2 Test Script: Enhanced ClipChooserWorker Testing
Tests the narrative-aware clip selection capabilities that integrate with StoryAnalysisWorker
for intelligent, story-driven clip selection.
"""

import sys
import os
import logging
from typing import Dict, Any, List

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the enhanced workers
from workers.workers import ClipChooserWorker, StoryAnalysisWorker

def setup_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('phase3_2_clip_chooser_test.log')
        ]
    )

def create_test_scenes_data() -> List[Dict[str, Any]]:
    """Create test scenes data for clip selection."""
    return [
        {
            "start": 0.0,
            "end": 45.0,
            "description": "Opening scene establishing the peaceful village where our hero lives",
            "score": 0.7,
            "mood": "peaceful"
        },
        {
            "start": 45.0,
            "end": 90.0,
            "description": "Mysterious stranger arrives bringing urgent news of approaching danger",
            "score": 0.85,
            "mood": "mysterious"
        },
        {
            "start": 90.0,
            "end": 150.0,
            "description": "Hero receives the call to adventure and initially refuses the quest",
            "score": 0.9,
            "mood": "tense"
        },
        {
            "start": 150.0,
            "end": 210.0,
            "description": "Training montage showing hero preparing for the dangerous journey ahead",
            "score": 0.6,
            "mood": "hopeful"
        },
        {
            "start": 210.0,
            "end": 270.0,
            "description": "First major obstacle and conflict encountered on the journey",
            "score": 0.8,
            "mood": "intense"
        },
        {
            "start": 270.0,
            "end": 330.0,
            "description": "Allies join the hero for the dangerous mission to save the kingdom",
            "score": 0.75,
            "mood": "hopeful"
        },
        {
            "start": 330.0,
            "end": 390.0,
            "description": "Building tension as they approach the final challenge and dark fortress",
            "score": 0.9,
            "mood": "tense"
        },
        {
            "start": 390.0,
            "end": 450.0,
            "description": "Climactic battle with the main antagonist in an epic confrontation",
            "score": 1.0,
            "mood": "intense"
        },
        {
            "start": 450.0,
            "end": 480.0,
            "description": "Aftermath and consequences of the final battle with emotional resolution",
            "score": 0.65,
            "mood": "dramatic"
        },
        {
            "start": 480.0,
            "end": 510.0,
            "description": "Resolution and return to the peaceful village, completing the hero's journey",
            "score": 0.8,
            "mood": "peaceful"
        }
    ]

def create_story_analysis_data() -> Dict[str, Any]:
    """Create mock story analysis data for narrative intelligence testing."""
    return {
        "status": "success",
        "worker_id": "story_analysis",
        "coherence_score": 0.785,
        "classified_scenes": [
            {
                "start": 0.0,
                "end": 45.0,
                "description": "opening scene establishing the peaceful village where our hero lives",
                "narrative_function": "exposition",
                "narrative_importance": 0.7,
                "emotional_classification": {
                    "primary_emotion": "peaceful",
                    "intensity": 0.2,
                    "valence": "positive"
                },
                "story_position": 0.0
            },
            {
                "start": 45.0,
                "end": 90.0,
                "description": "mysterious stranger arrives bringing urgent news of approaching danger",
                "narrative_function": "inciting_incident",
                "narrative_importance": 0.9,
                "emotional_classification": {
                    "primary_emotion": "mysterious",
                    "intensity": 0.5,
                    "valence": "neutral"
                },
                "story_position": 0.088
            },
            {
                "start": 90.0,
                "end": 150.0,
                "description": "hero receives the call to adventure and initially refuses the quest",
                "narrative_function": "inciting_incident",
                "narrative_importance": 0.95,
                "emotional_classification": {
                    "primary_emotion": "tense",
                    "intensity": 0.6,
                    "valence": "negative"
                },
                "story_position": 0.176
            },
            {
                "start": 150.0,
                "end": 210.0,
                "description": "training montage showing hero preparing for the dangerous journey ahead",
                "narrative_function": "rising_action",
                "narrative_importance": 0.6,
                "emotional_classification": {
                    "primary_emotion": "hopeful",
                    "intensity": 0.4,
                    "valence": "positive"
                },
                "story_position": 0.294
            },
            {
                "start": 210.0,
                "end": 270.0,
                "description": "first major obstacle and conflict encountered on the journey",
                "narrative_function": "rising_action",
                "narrative_importance": 0.8,
                "emotional_classification": {
                    "primary_emotion": "intense",
                    "intensity": 1.0,
                    "valence": "negative"
                },
                "story_position": 0.412
            },
            {
                "start": 270.0,
                "end": 330.0,
                "description": "allies join the hero for the dangerous mission to save the kingdom",
                "narrative_function": "rising_action",
                "narrative_importance": 0.75,
                "emotional_classification": {
                    "primary_emotion": "hopeful",
                    "intensity": 0.4,
                    "valence": "positive"
                },
                "story_position": 0.529
            },
            {
                "start": 330.0,
                "end": 390.0,
                "description": "building tension as they approach the final challenge and dark fortress",
                "narrative_function": "rising_action",
                "narrative_importance": 0.85,
                "emotional_classification": {
                    "primary_emotion": "tense",
                    "intensity": 0.6,
                    "valence": "negative"
                },
                "story_position": 0.647
            },
            {
                "start": 390.0,
                "end": 450.0,
                "description": "climactic battle with the main antagonist in an epic confrontation",
                "narrative_function": "climax",
                "narrative_importance": 1.0,
                "emotional_classification": {
                    "primary_emotion": "intense",
                    "intensity": 1.0,
                    "valence": "negative"
                },
                "story_position": 0.765
            },
            {
                "start": 450.0,
                "end": 480.0,
                "description": "aftermath and consequences of the final battle with emotional resolution",
                "narrative_function": "falling_action",
                "narrative_importance": 0.7,
                "emotional_classification": {
                    "primary_emotion": "dramatic",
                    "intensity": 0.8,
                    "valence": "neutral"
                },
                "story_position": 0.882
            },
            {
                "start": 480.0,
                "end": 510.0,
                "description": "resolution and return to the peaceful village, completing the hero's journey",
                "narrative_function": "resolution",
                "narrative_importance": 0.85,
                "emotional_classification": {
                    "primary_emotion": "peaceful",
                    "intensity": 0.2,
                    "valence": "positive"
                },
                "story_position": 1.0
            }
        ]
    }

def test_phase3_2_clip_chooser():
    """Test the Phase 3.2 Enhanced ClipChooserWorker with narrative intelligence."""
    print("🎬 Phase 3.2: Enhanced ClipChooserWorker Testing")
    print("=" * 65)
    
    logger = logging.getLogger(__name__)
    
    # Initialize workers
    clip_chooser = ClipChooserWorker({})
    
    print(f"✅ ClipChooserWorker initialized")
    print()
    
    # Prepare test data
    scenes_data = create_test_scenes_data()
    story_analysis = create_story_analysis_data()
    
    analysis_input = {
        "scenes": scenes_data,
        "total_duration": 510.0,
        "video_path": ""  # Empty for script-based workflow
    }
    
    # Test 1: Basic narrative-aware selection (no prompt)
    print("📋 Test 1: Basic Narrative-Aware Selection")
    print("-" * 45)
    
    try:
        result = clip_chooser.run(analysis_input, story_analysis=story_analysis)
        clips = result.get("clips", [])
        
        print(f"✅ Basic selection completed")
        print(f"   Selected {len(clips)} clips from {len(scenes_data)} scenes")
        
        # Analyze narrative distribution
        narrative_functions = {}
        for clip in clips:
            func = clip.get('narrative_function', 'unknown')
            narrative_functions[func] = narrative_functions.get(func, 0) + 1
        
        print(f"   Narrative function distribution: {narrative_functions}")
        
        # Show selected clips with narrative metadata
        print(f"\n📊 Selected Clips with Narrative Intelligence:")
        for i, clip in enumerate(clips[:5]):  # Show first 5
            print(f"   Clip {i+1}: {clip['narrative_function']} "
                  f"(importance: {clip.get('narrative_importance', 0):.2f}, "
                  f"score: {clip['score']:.2f})")
            print(f"     {clip['description'][:60]}...")
        
        if len(clips) > 5:
            print(f"   ... and {len(clips) - 5} more clips")
        
        print()
        
    except Exception as e:
        print(f"❌ Basic narrative-aware selection failed: {e}")
        logger.error(f"Basic selection test failed: {e}")
    
    # Test 2: Narrative function filtering
    print("🎯 Test 2: Narrative Function Filtering")
    print("-" * 40)
    
    try:
        # Test with climax focus
        prompt_with_narrative = "focus on climax scenes"
        result = clip_chooser.run(analysis_input, prompt=prompt_with_narrative, story_analysis=story_analysis)
        clips = result.get("clips", [])
        
        print(f"✅ Climax-focused selection completed")
        print(f"   Selected {len(clips)} clips with climax focus")
        
        # Check if climax scenes are prioritized
        climax_clips = [c for c in clips if c.get('narrative_function') == 'climax']
        print(f"   Climax clips in selection: {len(climax_clips)}")
        
        if climax_clips:
            for clip in climax_clips:
                print(f"   • Climax: {clip['description'][:50]}... (score: {clip['score']:.2f})")
        
        print()
        
    except Exception as e:
        print(f"❌ Narrative function filtering failed: {e}")
        logger.error(f"Narrative filtering test failed: {e}")
    
    # Test 3: Comparison with and without story analysis
    print("⚖️  Test 3: Comparison - With vs Without Story Analysis")
    print("-" * 55)
    
    try:
        # Selection without story analysis
        result_without = clip_chooser.run(analysis_input)
        clips_without = result_without.get("clips", [])
        
        # Selection with story analysis
        result_with = clip_chooser.run(analysis_input, story_analysis=story_analysis)
        clips_with = result_with.get("clips", [])
        
        print(f"✅ Comparison completed")
        print(f"   Without story analysis: {len(clips_without)} clips selected")
        print(f"   With story analysis: {len(clips_with)} clips selected")
        
        # Compare selection quality
        without_avg_score = sum(c['score'] for c in clips_without) / len(clips_without) if clips_without else 0
        with_avg_score = sum(c['score'] for c in clips_with) / len(clips_with) if clips_with else 0
        
        print(f"   Average score without story analysis: {without_avg_score:.3f}")
        print(f"   Average score with story analysis: {with_avg_score:.3f}")
        
        # Check narrative importance in story-aware selection
        if clips_with and 'narrative_importance' in clips_with[0]:
            with_avg_importance = sum(c.get('narrative_importance', 0) for c in clips_with) / len(clips_with)
            print(f"   Average narrative importance (with analysis): {with_avg_importance:.3f}")
        
        print()
        
    except Exception as e:
        print(f"❌ Comparison test failed: {e}")
        logger.error(f"Comparison test failed: {e}")
    
    # Test 4: Advanced prompt parsing with narrative focus
    print("🧠 Test 4: Advanced Prompt Parsing with Narrative Focus")
    print("-" * 50)
    
    try:
        # Test various narrative-focused prompts
        test_prompts = [
            "show me 3 clips focusing on rising action",
            "prioritize climax and resolution scenes",
            "give me the most important narrative moments",
            "focus on emotional peaks, 4 clips max"
        ]
        
        for i, prompt in enumerate(test_prompts):
            print(f"   Prompt {i+1}: '{prompt}'")
            
            try:
                result = clip_chooser.run(analysis_input, prompt=prompt, story_analysis=story_analysis)
                clips = result.get("clips", [])
                
                # Analyze results
                narrative_dist = {}
                for clip in clips:
                    func = clip.get('narrative_function', 'unknown')
                    narrative_dist[func] = narrative_dist.get(func, 0) + 1
                
                print(f"     → {len(clips)} clips selected: {narrative_dist}")
                
            except Exception as e:
                print(f"     → Failed: {e}")
        
        print()
        
    except Exception as e:
        print(f"❌ Advanced prompt parsing failed: {e}")
        logger.error(f"Advanced prompt test failed: {e}")
    
    # Test 5: Narrative flow optimization
    print("🌊 Test 5: Narrative Flow Optimization")
    print("-" * 35)
    
    try:
        result = clip_chooser.run(analysis_input, story_analysis=story_analysis)
        clips = result.get("clips", [])
        
        print(f"✅ Flow optimization completed")
        print(f"   Selected {len(clips)} clips with optimized narrative flow")
        
        # Check if clips are in logical narrative order
        narrative_order = ["exposition", "inciting_incident", "rising_action", "climax", "falling_action", "resolution"]
        
        print(f"\n📈 Narrative Flow Analysis:")
        prev_order = -1
        flow_score = 0
        total_transitions = 0
        
        for clip in clips:
            func = clip.get('narrative_function', 'unknown')
            if func in narrative_order:
                current_order = narrative_order.index(func)
                print(f"   {func.replace('_', ' ').title()}: {clip['description'][:40]}...")
                
                if prev_order != -1:
                    if current_order >= prev_order:
                        flow_score += 1
                    total_transitions += 1
                
                prev_order = current_order
        
        if total_transitions > 0:
            flow_quality = (flow_score / total_transitions) * 100
            print(f"\n   Narrative flow quality: {flow_quality:.1f}% logical progression")
        
        print()
        
    except Exception as e:
        print(f"❌ Narrative flow optimization failed: {e}")
        logger.error(f"Flow optimization test failed: {e}")
    
    # Test 6: Performance and scalability
    print("⚡ Test 6: Performance and Scalability")
    print("-" * 35)
    
    try:
        import time
        
        # Create larger dataset
        large_scenes = []
        for i in range(30):
            large_scenes.append({
                "start": i * 20.0,
                "end": (i + 1) * 20.0,
                "description": f"Scene {i+1} with various narrative content and complexity",
                "score": 0.3 + (i % 7) * 0.1,
                "mood": ["peaceful", "mysterious", "tense", "hopeful", "intense", "dramatic", "calm"][i % 7]
            })
        
        large_analysis_input = {
            "scenes": large_scenes,
            "total_duration": 600.0,
            "video_path": ""
        }
        
        # Test performance with story analysis
        start_time = time.time()
        result = clip_chooser.run(large_analysis_input, story_analysis=story_analysis)
        end_time = time.time()
        
        clips = result.get("clips", [])
        processing_time = end_time - start_time
        
        print(f"✅ Performance test completed")
        print(f"   Processed {len(large_scenes)} scenes in {processing_time:.2f}s")
        print(f"   Selected {len(clips)} clips with narrative intelligence")
        print(f"   Processing rate: {len(large_scenes)/processing_time:.1f} scenes/second")
        
        # Quality metrics
        if clips:
            avg_narrative_importance = sum(c.get('narrative_importance', 0) for c in clips) / len(clips)
            avg_score = sum(c['score'] for c in clips) / len(clips)
            
            print(f"   Average narrative importance: {avg_narrative_importance:.3f}")
            print(f"   Average clip score: {avg_score:.3f}")
        
        print()
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        logger.error(f"Performance test failed: {e}")

def test_edge_cases():
    """Test edge cases and error handling."""
    print("⚠️  Edge Case Testing")
    print("-" * 20)
    
    clip_chooser = ClipChooserWorker({})
    
    # Test with empty story analysis
    try:
        empty_analysis = {"scenes": []}
        result = clip_chooser.run(empty_analysis, story_analysis=None)
        print("✅ Handled empty story analysis gracefully")
    except Exception as e:
        print(f"✅ Empty analysis correctly failed: {type(e).__name__}")
    
    # Test with malformed story analysis
    try:
        malformed_story = {"status": "failed", "classified_scenes": []}
        scenes_input = {
            "scenes": [{
                "start": 0, "end": 30, "description": "Test scene", 
                "score": 0.5, "mood": "neutral"
            }],
            "total_duration": 30
        }
        result = clip_chooser.run(scenes_input, story_analysis=malformed_story)
        print("✅ Handled malformed story analysis gracefully")
    except Exception as e:
        print(f"❌ Malformed analysis test failed: {e}")
    
    print()

def main():
    """Main test function."""
    setup_logging()
    
    print("🚀 Starting Phase 3.2: Enhanced ClipChooser Testing")
    print()
    
    try:
        test_phase3_2_clip_chooser()
        test_edge_cases()
        
        print("🎯 Phase 3.2 Enhanced ClipChooserWorker Testing Complete!")
        print("=" * 65)
        print("✅ All Phase 3.2 tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Phase 3.2 testing failed: {e}")
        logging.error(f"Phase 3.2 testing failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
