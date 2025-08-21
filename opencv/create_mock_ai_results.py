#!/usr/bin/env python3
"""
Create mock AI results with matching filenames for comparison demo.
"""

import json
import random
from datetime import datetime
from pathlib import Path

def create_mock_ai_results():
    """Create mock AI results that match the actual image filenames."""
    
    # Get the actual image filenames
    images_dir = Path(__file__).parent.parent / "images"
    image_files = [f for f in images_dir.glob("*") if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']]
    
    print(f"Found {len(image_files)} image files to create mock AI results for:")
    for img in image_files:
        print(f"  - {img.name}")
    
    # Create mock AI results with some variation from OpenCV scores
    mock_results = []
    
    for img_file in image_files:
        # Generate scores that are somewhat realistic but different from OpenCV
        base_score = random.uniform(6.0, 9.0)
        variation = random.uniform(-1.0, 1.0)
        
        lighting = round(base_score + random.uniform(-0.5, 0.5), 1)
        composition = round(base_score + random.uniform(-0.5, 0.5), 1)
        clarity = round(base_score + random.uniform(-0.5, 0.5), 1)
        detail = round(base_score + random.uniform(-0.5, 0.5), 1)
        background = round(base_score + random.uniform(-0.5, 0.5), 1)
        overall = round((lighting + composition + clarity + detail + background) / 5, 1)
        
        # Ensure scores are in valid range
        lighting = max(0, min(10, lighting))
        composition = max(0, min(10, composition))
        clarity = max(0, min(10, clarity))
        detail = max(0, min(10, detail))
        background = max(0, min(10, background))
        overall = max(0, min(10, overall))
        
        result = {
            "file_name": img_file.stem,  # filename without extension
            "file_extension": img_file.suffix,
            "Lighting_and_Exposure": lighting,
            "Angle_and_Composition": composition,
            "Clarity_and_Resolution": clarity,
            "Detail_Visibility": detail,
            "Background_and_Distractions": background,
            "Overall_Score": overall,
            "Decision": "Keep" if overall > 7.0 else "Retake"
        }
        
        mock_results.append(result)
    
    # Create the session messages format that the comparison tool expects
    session_messages = [
        {
            "role": "system",
            "content": "Return a JSON object with: file_name, file_extension, Lighting_and_Exposure, Angle_and_Composition, Clarity_and_Resolution, Detail_Visibility, Background_and_Distractions, Overall_Score (all decimals), and Decision ('Keep' if Overall_Score > 7.0, else 'Retake'). No explanations."
        }
    ]
    
    # Add each result as an assistant message
    for result in mock_results:
        session_messages.append({
            "role": "assistant",
            "content": f"```json\n{json.dumps(result, indent=2)}\n```"
        })
    
    # Save to output directory
    output_dir = Path(__file__).parent.parent / "output"
    timestamp = datetime.now().strftime('%Y%m%d %H-%M-%S')
    output_file = output_dir / f"{timestamp} Mock AI Session Messages.json"
    
    with open(output_file, 'w') as f:
        json.dump(session_messages, f, indent=2)
    
    print(f"\n✅ Created mock AI results file: {output_file.name}")
    print(f"📊 Generated {len(mock_results)} AI results with matching filenames")
    print("🔄 Now you can run the comparison tool!")
    
    return str(output_file)

if __name__ == "__main__":
    create_mock_ai_results()
