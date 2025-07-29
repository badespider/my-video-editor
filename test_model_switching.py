#!/usr/bin/env python3
"""
Model Switching Test Script for Rule 5.2
Tests the system with different AI models (GPT-4, Grok-4, Mock)
"""

import sys
import os
import json
import time
from coordinator import VideoAgent
import config
from utils import call_model

def test_model_switching():
    """
    Test Rule 5.2: Model Switch Testing
    Tests workflow with different models and verifies output formats
    """
    print("=== Rule 5.2: Model Switch Testing ===\n")
    
    # Models to test
    models_to_test = [
        ("gpt-4", "OpenAI GPT-4"),
        ("gpt-3.5-turbo", "OpenAI GPT-3.5 Turbo"), 
        ("grok-4", "Grok-4"),
        ("mock", "Mock Model")
    ]
    
    test_script = "A young detective investigates a mysterious case in a foggy city."
    results = {}
    
    print("Testing model switching with sample script...")
    print(f"Script: {test_script}\n")
    
    for model_id, model_name in models_to_test:
        print(f"🔄 Testing {model_name} ({model_id})...")
        
        try:
            # Test individual model call first
            start_time = time.time()
            response = call_model("Test prompt for model validation", model=model_id)
            call_time = time.time() - start_time
            
            # Test full workflow with this model
            agent = VideoAgent(model=model_id)
            workflow_start = time.time()
            result = agent.run(test_script)
            workflow_time = time.time() - workflow_start
            
            # Verify output format consistency
            expected_keys = ["clips", "narrations", "bgms", "timeline", "total_duration"]
            missing_keys = [key for key in expected_keys if key not in result]
            
            results[model_id] = {
                "status": "success",
                "model_name": model_name,
                "call_time": round(call_time, 2),
                "workflow_time": round(workflow_time, 2),
                "response_preview": response[:100] + "..." if len(response) > 100 else response,
                "output_keys": list(result.keys()),
                "missing_keys": missing_keys,
                "total_duration": result.get("total_duration", 0)
            }
            
            print(f"✅ {model_name}: Success")
            print(f"   Call time: {call_time:.2f}s, Workflow time: {workflow_time:.2f}s")
            if missing_keys:
                print(f"   ⚠️  Missing keys: {missing_keys}")
            print()
            
        except Exception as e:
            results[model_id] = {
                "status": "failed",
                "model_name": model_name,
                "error": str(e),
                "error_type": type(e).__name__
            }
            print(f"❌ {model_name}: Failed - {e}")
            print()
    
    return results

def test_config_switching():
    """
    Test configuration-based model switching
    """
    print("=== Testing Configuration-Based Model Switching ===\n")
    
    # Store original config
    original_model = config.MODEL
    original_backup = config.MODEL_BACKUP
    
    try:
        # Test config updates
        test_configs = [
            ("gpt-4", "gpt-3.5-turbo"),
            ("mock", "gpt-4"),
            ("grok-4", "mock")
        ]
        
        for primary, backup in test_configs:
            print(f"🔧 Testing config: PRIMARY={primary}, BACKUP={backup}")
            
            # Update config
            config.MODEL = primary
            config.MODEL_BACKUP = backup
            
            # Create agent (should use new config)
            agent = VideoAgent()
            
            # Verify agent picked up new config
            assert agent.model == primary, f"Agent model {agent.model} != config {primary}"
            
            print(f"✅ Config update successful: {primary} -> {backup}")
            print()
    
    finally:
        # Restore original config
        config.MODEL = original_model
        config.MODEL_BACKUP = original_backup

def generate_test_report(results):
    """
    Generate a comprehensive test report
    """
    print("=== MODEL SWITCHING TEST REPORT ===\n")
    
    successful_models = [r for r in results.values() if r["status"] == "success"]
    failed_models = [r for r in results.values() if r["status"] == "failed"]
    
    print(f"✅ Successful models: {len(successful_models)}/{len(results)}")
    print(f"❌ Failed models: {len(failed_models)}/{len(results)}")
    print()
    
    if successful_models:
        print("SUCCESSFUL MODELS:")
        for result in successful_models:
            print(f"  • {result['model_name']}")
            print(f"    - Call time: {result['call_time']}s")
            print(f"    - Workflow time: {result['workflow_time']}s")
            print(f"    - Output keys: {len(result['output_keys'])}")
            if result['missing_keys']:
                print(f"    - Missing keys: {result['missing_keys']}")
        print()
    
    if failed_models:
        print("FAILED MODELS:")
        for result in failed_models:
            print(f"  • {result['model_name']}: {result['error_type']}")
            print(f"    - Error: {result['error']}")
        print()
    
    # Output consistency check
    if len(successful_models) > 1:
        print("OUTPUT CONSISTENCY CHECK:")
        first_keys = set(successful_models[0]['output_keys'])
        all_consistent = True
        
        for result in successful_models[1:]:
            current_keys = set(result['output_keys'])
            if current_keys != first_keys:
                all_consistent = False
                print(f"  ⚠️  {result['model_name']} output keys differ from baseline")
                print(f"     Missing: {first_keys - current_keys}")
                print(f"     Extra: {current_keys - first_keys}")
        
        if all_consistent:
            print("  ✅ All successful models have consistent output formats")
        print()
    
    # Performance comparison
    if successful_models:
        print("PERFORMANCE COMPARISON:")
        sorted_by_speed = sorted(successful_models, key=lambda x: x['workflow_time'])
        print("  Fastest to slowest:")
        for i, result in enumerate(sorted_by_speed, 1):
            print(f"    {i}. {result['model_name']}: {result['workflow_time']}s")
        print()

def main():
    """
    Main test execution
    """
    print("Multi-Agent AI Video Creation System")
    print("Model Switching Test Suite (Rule 5.2)")
    print("=" * 50)
    print()
    
    # Test 1: Model switching functionality
    results = test_model_switching()
    
    # Test 2: Configuration switching
    test_config_switching()
    
    # Test 3: Generate comprehensive report
    generate_test_report(results)
    
    # Save results to file
    output_file = "model_switching_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"📊 Detailed results saved to: {output_file}")
    print()
    
    # Summary
    successful_count = sum(1 for r in results.values() if r["status"] == "success")
    total_count = len(results)
    
    print("=== SUMMARY ===")
    print(f"Models tested: {total_count}")
    print(f"Successful: {successful_count}")
    print(f"Success rate: {successful_count/total_count*100:.1f}%")
    
    if successful_count == total_count:
        print("🎉 All models working correctly!")
        return 0
    elif successful_count > 0:
        print("⚠️  Some models failed, but system is partially functional")
        return 0
    else:
        print("❌ All models failed - system needs attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())
