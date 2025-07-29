#!/usr/bin/env python3
"""
Full Multi-Agent Video Creation Pipeline
Creates a complete video from raw footage using all workers.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Import all workers
from workers.workers import (
    IngestionWorker, 
    ClipChooserWorker, 
    NarrationWorker, 
    BGMWorker, 
    AssemblyWorker,
    StoryAnalysisWorker
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('video_creation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class VideoAgent:
    """Main orchestrator for the multi-agent video creation system."""
    
    def __init__(self):
        self.state = {}
        self.results = {}
        
    def run_with_video(self, video_path: str, prompt: str = None) -> dict:
        """
        Run the complete video creation pipeline.
        
        Args:
            video_path: Path to input video file
            prompt: Optional editing prompt for customization
            
        Returns:
            Dictionary with final video and all intermediate results
        """
        logger.info("🎬 Starting Multi-Agent Video Creation Pipeline")
        logger.info(f"📹 Input Video: {video_path}")
        logger.info(f"📝 Prompt: {prompt or 'None'}")
        
        try:
            # Phase 1: Video Ingestion
            logger.info("\n=== Phase 1: Video Ingestion ===")
            ingestion_worker = IngestionWorker(self.state)
            ingestion_result = ingestion_worker.run(video_path)
            self.results['ingestion'] = ingestion_result
            
            logger.info(f"✅ Ingested video: {ingestion_result['scene_count']} scenes, "
                       f"{ingestion_result['coverage_percentage']:.1%} coverage")
            
            # Phase 2: Story Analysis (Optional Enhancement)
            logger.info("\n=== Phase 2: Story Analysis ===")
            story_analysis_result = None
            try:
                story_worker = StoryAnalysisWorker()
                # Use scenes from ingestion for analysis
                story_analysis_result = story_worker.run(ingestion_result['scenes'])
                self.results['story_analysis'] = story_analysis_result
                
                logger.info(f"✅ Story analysis: {story_analysis_result.get('coherence_score', 0):.3f} coherence score")
            except Exception as e:
                logger.warning(f"Story analysis failed: {e}, continuing without narrative enhancement")
                story_analysis_result = None
            
            # Phase 3: Intelligent Clip Selection
            logger.info("\n=== Phase 3: Intelligent Clip Selection ===")
            clip_worker = ClipChooserWorker(self.state)
            clip_result = clip_worker.run(
                ingestion_result, 
                prompt=prompt,
                story_analysis=story_analysis_result
            )
            self.results['clips'] = clip_result
            
            logger.info(f"✅ Selected {len(clip_result['clips'])} clips for video")
            
            # Phase 4: AI Narration Generation
            logger.info("\n=== Phase 4: AI Narration Generation ===")
            narration_worker = NarrationWorker(self.state)
            narration_result = narration_worker.run(clip_result)
            self.results['narration'] = narration_result
            
            logger.info(f"✅ Generated narration: {narration_result.get('word_count', 0)} words, "
                       f"{narration_result.get('segment_count', 0)} segments")
            
            # Phase 5: Background Music Selection
            logger.info("\n=== Phase 5: Background Music Selection ===")
            bgm_worker = BGMWorker(self.state)
            bgm_result = bgm_worker.run(clip_result)
            self.results['bgm'] = bgm_result
            
            logger.info(f"✅ Generated BGM: {len(bgm_result.get('bgm_options', []))} options")
            
            # Phase 6: Final Video Assembly
            logger.info("\n=== Phase 6: Final Video Assembly ===")
            assembly_worker = AssemblyWorker(self.state)
            final_result = assembly_worker.run(clip_result, narration_result, bgm_result)
            self.results['final'] = final_result
            
            logger.info(f"✅ Final video created: {final_result.get('final_video', 'Unknown')}")
            logger.info(f"📊 Total duration: {final_result.get('total_duration', 0):.1f}s")
            
            # Summary Report
            self._generate_summary_report()
            
            logger.info("\n🎉 VIDEO CREATION COMPLETE! 🎉")
            return final_result
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _generate_summary_report(self):
        """Generate a comprehensive summary report."""
        logger.info("\n" + "="*60)
        logger.info("📊 VIDEO CREATION SUMMARY REPORT")
        logger.info("="*60)
        
        # Ingestion Summary
        ingestion = self.results.get('ingestion', {})
        logger.info(f"📹 Input Analysis:")
        logger.info(f"   • Total Duration: {ingestion.get('total_duration', 0):.1f}s")
        logger.info(f"   • Scenes Detected: {ingestion.get('scene_count', 0)}")
        logger.info(f"   • Coverage: {ingestion.get('coverage_percentage', 0):.1%}")
        
        # Story Analysis Summary
        story = self.results.get('story_analysis', {})
        if story and story.get('status') == 'success':
            logger.info(f"📖 Story Analysis:")
            logger.info(f"   • Coherence Score: {story.get('coherence_score', 0):.3f}")
            logger.info(f"   • Emotional Arc: {story.get('emotional_arc', {}).get('arc_type', 'unknown')}")
            logger.info(f"   • Total Scenes Analyzed: {story.get('total_scenes', 0)}")
        
        # Clip Selection Summary
        clips = self.results.get('clips', {})
        logger.info(f"🎬 Clip Selection:")
        logger.info(f"   • Clips Selected: {len(clips.get('clips', []))}")
        for i, clip in enumerate(clips.get('clips', [])[:3]):  # Show first 3
            logger.info(f"   • Clip {i+1}: {clip.get('description', 'Unknown')[:40]}... "
                       f"({clip.get('duration', 0):.1f}s)")
        
        # Narration Summary
        narration = self.results.get('narration', {})
        logger.info(f"🎙️ Narration:")
        logger.info(f"   • Word Count: {narration.get('word_count', 0)}")
        logger.info(f"   • Segments: {narration.get('segment_count', 0)}")
        logger.info(f"   • Audio File: {narration.get('audio_path', 'None')}")
        
        # BGM Summary
        bgm = self.results.get('bgm', {})
        logger.info(f"🎵 Background Music:")
        logger.info(f"   • Options Generated: {len(bgm.get('bgm_options', []))}")
        logger.info(f"   • Mood Analysis: {bgm.get('mood_analysis', {})}")
        
        # Final Video Summary
        final = self.results.get('final', {})
        logger.info(f"🎥 Final Video:")
        logger.info(f"   • Output File: {final.get('final_video', 'Unknown')}")
        logger.info(f"   • Total Duration: {final.get('total_duration', 0):.1f}s")
        logger.info(f"   • Timeline Events: {len(final.get('timeline', []))}")
        
        logger.info("="*60)


def main():
    """Main execution function."""
    # Configuration
    video_path = r"C:\Users\dimit\Videos\anime\1mp4.mp4"
    prompt = None  # Use None to avoid prompt parsing issues and just select clips based on scores
    
    # Verify video exists
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
    
    # Create video agent and run pipeline
    agent = VideoAgent()
    
    try:
        final_result = agent.run_with_video(video_path, prompt)
        
        # Save results for reference
        results_file = f"video_creation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            # Convert to JSON-serializable format
            serializable_results = {}
            for key, value in agent.results.items():
                try:
                    json.dumps(value)  # Test if serializable
                    serializable_results[key] = value
                except TypeError:
                    serializable_results[key] = str(value)  # Convert to string if not serializable
            
            json.dump(serializable_results, f, indent=2)
        
        print(f"\n📁 Results saved to: {results_file}")
        print(f"🎬 Final video: {final_result.get('final_video', 'Unknown')}")
        
        # Move final video to anime folder if it exists
        final_video_path = final_result.get('final_video')
        if final_video_path and os.path.exists(final_video_path):
            import shutil
            anime_folder = r"C:\Users\dimit\Videos\anime"
            final_filename = os.path.basename(final_video_path)
            anime_final_path = os.path.join(anime_folder, final_filename)
            
            try:
                shutil.move(final_video_path, anime_final_path)
                print(f"📁 Final video moved to: {anime_final_path}")
            except Exception as e:
                print(f"⚠️ Could not move video to anime folder: {e}")
        
    except Exception as e:
        print(f"❌ Video creation failed: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")


if __name__ == "__main__":
    main()
