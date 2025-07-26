"""
Main entry point for multi-agent AI video creation system.
Initializes and executes the workflow.
"""

import argparse
import sys
import json
import os
from coordinator import VideoAgent
import config


def main():
    """
    Main function to run the video creation pipeline.
    """
    parser = argparse.ArgumentParser(description="Multi-Agent AI Video Creation System")
    parser.add_argument('--script', type=str, help='Path to script file to process')
    parser.add_argument('--video', type=str, help='Path to video file to analyze and process')
    parser.add_argument('--demo', action='store_true', help='Run demo with sample script')
    parser.add_argument('--output', type=str, help='Path to save JSON output file (optional)')
    parser.add_argument('--server', action='store_true', help='Start FastAPI server with uvicorn')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind server to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind server to (default: 8000)')
    args = parser.parse_args()

    # Check if server mode was requested
    if args.server:
        try:
            import uvicorn
            print(f"Starting FastAPI server on {args.host}:{args.port}")
            uvicorn.run("backend.api:app", host=args.host, port=args.port, reload=True)
            return 0
        except ImportError:
            print("Error: uvicorn not installed. Install with: pip install uvicorn[standard]")
            return 1
        except Exception as e:
            print(f"Error starting server: {e}")
            return 1

    try:
        # Initialize the agent
        agent = VideoAgent()

        if args.video:
            # Process video file
            if not os.path.exists(args.video):
                print(f"Error: Video file '{args.video}' not found.")
                return 1
            print(f"Processing video file: {args.video}")
            
            # Run the pipeline with video input
            print("\nRunning video analysis pipeline...")
            result = agent.run_with_video(args.video)
            
        elif args.demo:
            # Use sample script file for demo if it exists, otherwise use embedded script
            sample_script_path = 'sample_script.txt'
            if os.path.exists(sample_script_path):
                with open(sample_script_path, 'r', encoding='utf-8') as file:
                    script = file.read()
                print(f"Running demo with sample script from {sample_script_path}")
            else:
                script = """
                A young detective investigates a mysterious case in a foggy city.
                The story unfolds through dark alleyways and bright neon-lit streets.
                """
                print("Running demo with embedded sample script")
            
            # Run the pipeline
            print("\nRunning video creation pipeline...")
            result = agent.run(script)
            
        elif args.script:
            # Read from the provided script file
            if not os.path.exists(args.script):
                print(f"Error: Script file '{args.script}' not found.")
                return 1
            with open(args.script, 'r', encoding='utf-8') as file:
                script = file.read()
            print(f"Processing script from {args.script}")
            
            # Run the pipeline
            print("\nRunning video creation pipeline...")
            result = agent.run(script)
            
        else:
            # Read from standard input
            if sys.stdin.isatty():
                print("Error: No input provided. Use --video, --script, --demo, or pipe input via STDIN.")
                parser.print_help()
                return 1
            script = sys.stdin.read()
            print("Processing script from STDIN")
            
            if not script.strip():
                print("Error: Empty script provided.")
                return 1
            
            # Run the pipeline
            print("\nRunning video creation pipeline...")
            result = agent.run(script)

        # Format output as JSON
        json_output = json.dumps(result, indent=2, ensure_ascii=False)

        # Save to file if output path specified
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as output_file:
                    output_file.write(json_output)
                print(f"\nResults saved to: {args.output}")
            except Exception as e:
                print(f"Error saving to file: {e}")
                return 1

        # Print the result
        print("\nVideo plan generated:")
        print(json_output)
        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
