#!/usr/bin/env python3
"""
Debug filename matching in comparison tool.
"""

import json
from pathlib import Path
from comparison_tool import ResultsComparator

def debug_filename_matching():
    """Debug why filenames aren't matching."""
    
    print("🔍 Debugging filename matching...")
    
    comparator = ResultsComparator()
    
    # Load the mock AI results
    ai_file = Path(__file__).parent.parent / "output" / "20250820 22-31-47 Mock AI Session Messages.json"
    ai_results = comparator.load_ai_results(str(ai_file))
    
    print(f"\n📊 AI Results ({len(ai_results)} files):")
    for i, result in enumerate(ai_results):
        filename = result.get('file_name', 'Unknown')
        extension = result.get('file_extension', '')
        print(f"  {i+1}. '{filename}' (ext: '{extension}')")
    
    # Run OpenCV analysis
    opencv_results = comparator.run_opencv_analysis('general')
    
    print(f"\n🔧 OpenCV Results ({len(opencv_results)} files):")
    for i, result in enumerate(opencv_results):
        filename = result.get('file_name', 'Unknown')
        print(f"  {i+1}. '{filename}'")
    
    # Test matching logic manually
    print(f"\n🔗 Testing filename matching:")
    
    # Create lookup dict for OpenCV results (same as in comparison_tool)
    opencv_lookup = {}
    for result in opencv_results:
        if 'file_name' in result:
            key = result['file_name'].lower()
            opencv_lookup[key] = result
            print(f"  OpenCV key: '{key}'")
    
    # Try to match AI results
    matches = []
    for ai_result in ai_results:
        if 'file_name' in ai_result:
            ai_filename = ai_result['file_name'].lower()
            print(f"\n  Trying to match AI: '{ai_filename}'")
            
            # Try exact match first
            if ai_filename in opencv_lookup:
                print(f"    ✅ Exact match found!")
                matches.append((ai_result, opencv_lookup[ai_filename]))
            else:
                print(f"    ❌ No exact match")
                # Try partial matches
                found_partial = False
                for opencv_key, opencv_result in opencv_lookup.items():
                    if ai_filename in opencv_key or opencv_key in ai_filename:
                        print(f"    ✅ Partial match found: '{opencv_key}'")
                        matches.append((ai_result, opencv_result))
                        found_partial = True
                        break
                
                if not found_partial:
                    print(f"    ❌ No partial match found")
    
    print(f"\n📊 Final matching results: {len(matches)} matches found")
    
    if len(matches) > 0:
        print("✅ Matches found! Running comparison...")
        # Test the comparison
        comparison_stats = comparator.compare_scores(matches)
        print(f"Decision agreement: {comparison_stats.get('decision_agreement', {}).get('percentage', 0)}%")
    else:
        print("❌ No matches found. Filename formats don't align.")

if __name__ == "__main__":
    debug_filename_matching()
