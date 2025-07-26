"""
Main entry point for multi-agent AI video creation system.
Initializes and executes the workflow.
"""

from coordinator import VideoAgent


def main():
    """
    Main function to run the video creation pipeline.
    """
    # Initialize the agent
    agent = VideoAgent()
    
    # Sample script for testing
    sample_script = """
    A young detective investigates a mysterious case in a foggy city.
    The story unfolds through dark alleyways and bright neon-lit streets.
    """
    
    # Run the pipeline
    result = agent.run(sample_script)
    
    print("Video plan generated:")
    print(result)


if __name__ == "__main__":
    main()
