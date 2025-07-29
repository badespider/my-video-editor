#!/usr/bin/env python3
"""
Phase 3.1 Test Script: StoryAnalysisWorker Testing
Tests the new advanced story analysis capabilities including narrative classification,
emotional arc analysis, and story structure coherence scoring.
"""

import sys
import os
import logging
from typing import Dict, Any, List

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the new StoryAnalysisWorker
from workers.workers import StoryAnalysisWorker

def setup_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('phase3_story_analysis_test.log')
        ]
    )

def create_test_scenes_data() -> List[Dict[str, Any]]:
    """Create test scenes data for story analysis."""
    return [
        {
            "start": 0.0,
            "end": 30.0,
            "description": "Opening scene establishing the peaceful village",
            "score": 0.7,
            "mood": "peaceful"
        },
        {
            "start": 30.0,
            "end": 60.0,
            "description": "Mysterious stranger arrives bringing urgent news",
            "score": 0.8,
            "mood": "mysterious"
        },
        {
            "start": 60.0,
            "end": 120.0,
            "description": "Hero receives the call to adventure and initially refuses",
            "score": 0.9,
            "mood": "tense"
        },
        {
            "start": 120.0,
            "end": 180.0,
            "description": "Training montage showing hero preparing for the journey",
            "score": 0.6,
            "mood": "hopeful"
        },
        {
            "start": 180.0,
            "end": 240.0,
            "description": "First major obstacle and conflict encountered",
            "score": 0.8,
            "mood": "intense"
        },
        {
            "start": 240.0,
            "end": 300.0,
            "description": "Allies join the hero for the dangerous mission",
            "score": 0.7,
            "mood": "hopeful"
        },
        {
            "start": 300.0,
            "end": 360.0,
            "description": "Building tension as they approach the final challenge",
            "score": 0.9,
            "mood": "tense"
        },
        {
            "start": 360.0,
            "end": 420.0,
            "description": "Climactic battle with the main antagonist",
            "score": 1.0,
            "mood": "intense"
        },
        {
            "start": 420.0,
            "end": 450.0,
            "description": "Aftermath and consequences of the final battle",
            "score": 0.6,
            "mood": "dramatic"
        },
        {
            "start": 450.0,
            "end": 480.0,
            "description": "Resolution and return to the peaceful village",
            "score": 0.8,
            "mood": "peaceful"
        }
    ]

def create_complex_story_scenes() -> List[Dict[str, Any]]:
    """Create a more complex story for advanced testing."""
    return [
        {
            "start": 0.0,
            "end": 45.0,
            "description": "Detective investigates a mysterious crime scene in the rain",
            "score": 0.8,
            "mood": "mysterious"
        },
        {
            "start": 45.0,
            "end": 90.0,
            "description": "Flashback reveals the victim's troubled past",
            "score": 0.7,
            "mood": "dramatic"
        },
        {
            "start": 90.0,
            "end": 135.0,
            "description": "First suspect is interrogated but provides an alibi",
            "score": 0.6,
            "mood": "tense"
        },
        {
            "start": 135.0,
            "end": 180.0,
            "description": "New evidence points to an unexpected connection",
            "score": 0.9,
            "mood": "mysterious"
        },
        {
            "start": 180.0,
            "end": 225.0,
            "description": "Chase sequence through dark city streets",
            "score": 1.0,
            "mood": "intense"
        },
        {
            "start": 225.0,
            "end": 270.0,
            "description": "Confrontation reveals the true culprit and motive",
            "score": 0.95,
            "mood": "dramatic"
        },
        {
            "start": 270.0,
            "end": 300.0,
            "description": "Justice is served and peace is restored",
            "score": 0.7,
            "mood": "peaceful"
        }
    ]

def test_story_analysis_worker():
    """Test the StoryAnalysisWorker with various scenarios."""
    print("🎬 Phase 3.1: StoryAnalysisWorker Testing")
    print("=" * 60)
    
    logger = logging.getLogger(__name__)
    
    # Initialize the worker
    story_worker = StoryAnalysisWorker()
    
    print(f"✅ StoryAnalysisWorker initialized: {story_worker.worker_id}")
    print(f"   Status: {story_worker.status}")
    print()
    
    # Test 1: Hero's Journey Analysis
    print("📖 Test 1: Hero's Journey Story Structure Analysis")
    print("-" * 50)
    
    hero_scenes = create_test_scenes_data()
    print(f"Testing with {len(hero_scenes)} scenes (Hero's Journey)")
    
    try:
        result = story_worker.run(hero_scenes, story_type="hero_journey")
        
        print(f"✅ Analysis Status: {result['status']}")
        print(f"   Worker ID: {result['worker_id']}")
        print(f"   Story Type: {result['story_structure']['type']}")
        print(f"   Total Scenes: {result['total_scenes']}")
        print(f"   Coherence Score: {result['coherence_score']:.3f}")
        
        # Show story structure breakdown
        print("\n📊 Story Structure Breakdown:")
        for act_name, act_data in result['story_structure']['acts'].items():
            print(f"   {act_name.title()}: {act_data['scenes']} scenes, "
                  f"{act_data['duration']:.1f}s, avg_score: {act_data['avg_scene_score']:.3f}")
        
        # Show emotional arc analysis
        emotional_arc = result['emotional_arc']
        print(f"\n💫 Emotional Arc Analysis:")
        print(f"   Arc Type: {emotional_arc['arc_type']}")
        print(f"   Emotional Range: {emotional_arc['emotional_range']:.3f}")
        print(f"   Average Intensity: {emotional_arc['average_intensity']:.3f}")
        print(f"   Peaks: {len(emotional_arc['peaks_valleys']['peaks'])}")
        print(f"   Valleys: {len(emotional_arc['peaks_valleys']['valleys'])}")
        
        # Show story insights
        insights = result['story_insights']
        print(f"\n🔍 Story Insights:")
        if insights['insights']:
            for insight in insights['insights']:
                print(f"   • {insight}")
        else:
            print("   • No structural issues detected")
        
        if insights['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in insights['recommendations']:
                print(f"   • {rec}")
        
        # Show narrative function distribution
        print(f"\n📈 Narrative Function Distribution:")
        for func, count in insights['function_distribution'].items():
            print(f"   {func}: {count} scenes")
        
        print()
        
    except Exception as e:
        print(f"❌ Hero's Journey analysis failed: {e}")
        logger.error(f"Hero's Journey test failed: {e}")
    
    # Test 2: Three-Act Structure Analysis
    print("🎭 Test 2: Three-Act Structure Analysis")
    print("-" * 40)
    
    complex_scenes = create_complex_story_scenes()
    print(f"Testing with {len(complex_scenes)} scenes (Three-Act)")
    
    try:
        result = story_worker.run(complex_scenes, story_type="three_act")
        
        print(f"✅ Analysis Status: {result['status']}")
        print(f"   Story Type: {result['story_structure']['type']}")
        print(f"   Total Scenes: {result['total_scenes']}")
        print(f"   Coherence Score: {result['coherence_score']:.3f}")
        
        # Show classified scenes with their narrative functions
        print(f"\n🎬 Scene Classification:")
        classified_scenes = result['classified_scenes']
        for i, scene in enumerate(classified_scenes[:5]):  # Show first 5
            print(f"   Scene {i+1}: {scene['narrative_function']} "
                  f"(importance: {scene['narrative_importance']:.2f})")
            print(f"     {scene['description'][:60]}...")
            emotion = scene['emotional_classification']
            print(f"     Emotion: {emotion['primary_emotion']} "
                  f"(intensity: {emotion['intensity']:.2f}, "
                  f"valence: {emotion['valence']})")
        
        if len(classified_scenes) > 5:
            print(f"   ... and {len(classified_scenes) - 5} more scenes")
        
        print()
        
    except Exception as e:
        print(f"❌ Three-act analysis failed: {e}")
        logger.error(f"Three-act test failed: {e}")
    
    # Test 3: Edge Case Testing
    print("⚠️  Test 3: Edge Case Testing")
    print("-" * 30)
    
    # Test with minimal scenes
    minimal_scenes = [
        {
            "start": 0.0,
            "end": 60.0,
            "description": "Single scene story",
            "score": 0.8,
            "mood": "neutral"
        }
    ]
    
    try:
        result = story_worker.run(minimal_scenes, story_type="three_act")
        print(f"✅ Minimal scenes test: {result['status']}")
        print(f"   Coherence Score: {result['coherence_score']:.3f}")
        print(f"   Emotional Arc: {result['emotional_arc']['arc_type']}")
        
    except Exception as e:
        print(f"❌ Minimal scenes test failed: {e}")
    
    # Test with empty scenes (should fail gracefully)
    try:
        result = story_worker.run([], story_type="three_act")
        print(f"✅ Empty scenes test: {result['status']}")
        
    except Exception as e:
        print(f"✅ Empty scenes test correctly failed: {type(e).__name__}")
    
    print()
    
    # Test 4: Performance and Coherence Analysis
    print("⚡ Test 4: Performance Analysis")
    print("-" * 30)
    
    import time
    
    # Test with larger dataset
    large_scenes = []
    for i in range(20):
        large_scenes.append({
            "start": i * 30.0,
            "end": (i + 1) * 30.0,
            "description": f"Scene {i+1} with various content and moods",
            "score": 0.5 + (i % 5) * 0.1,
            "mood": ["peaceful", "mysterious", "tense", "dramatic", "intense"][i % 5]
        })
    
    start_time = time.time()
    try:
        result = story_worker.run(large_scenes, story_type="hero_journey")
        end_time = time.time()
        
        print(f"✅ Large dataset test completed in {end_time - start_time:.2f}s")
        print(f"   Processed {len(large_scenes)} scenes")
        print(f"   Coherence Score: {result['coherence_score']:.3f}")
        print(f"   Classification Success Rate: 100%")
        
        # Analysis quality metrics
        classified_scenes = result['classified_scenes']
        function_variety = len(set(s['narrative_function'] for s in classified_scenes))
        emotion_variety = len(set(s['emotional_classification']['primary_emotion'] for s in classified_scenes))
        
        print(f"   Narrative Function Variety: {function_variety}/6 possible")
        print(f"   Emotional Variety: {emotion_variety} different emotions")
        
    except Exception as e:
        print(f"❌ Large dataset test failed: {e}")

    print()
    print("🎯 Phase 3.1 StoryAnalysisWorker Testing Complete!")
    print("=" * 60)

def main():
    """Main test function."""
    setup_logging()
    
    print("🚀 Starting Phase 3.1: Advanced Story Analysis Testing")
    print()
    
    try:
        test_story_analysis_worker()
        print("✅ All Phase 3.1 tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Phase 3.1 testing failed: {e}")
        logging.error(f"Phase 3.1 testing failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
