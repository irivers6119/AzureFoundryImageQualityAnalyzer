# 🔧 How to Run `comparison_tool.py`

The `comparison_tool.py` script compares results between the original AI-based image quality analyzer and the new OpenCV implementation. This helps validate that the OpenCV replacement provides similar analysis quality.

## 📋 **Quick Start**

### **Method 1: Interactive Mode (Recommended)**
```bash
cd /path/to/imagequalityanalyzer/opencv
python3 comparison_tool.py
```

The tool will:
1. Show available AI results files
2. Let you select which file to compare
3. Run OpenCV analysis on the same images
4. Display comparison statistics and detailed report

### **Method 2: Using Docker**
```bash
cd /path/to/imagequalityanalyzer/opencv
./docker-build.sh
docker run --rm -v "$(pwd)/../images:/app/images" \
  -v "$(pwd)/../output:/app/output" \
  opencv-image-analyzer python3 comparison_tool.py
```

## 📊 **What the Tool Analyzes**

### **Score Comparisons**
- **Overall Score differences** between AI and OpenCV
- **Statistical analysis**: mean, median, standard deviation
- **Individual metrics**: brightness, contrast, sharpness, etc.

### **Decision Agreement**
- **Keep vs Retake decisions** for each image
- **Agreement percentage** between AI and OpenCV
- **Files with decision conflicts**

### **Detailed Reports**
- **File-by-file comparison** with scores and decisions
- **Large differences** highlighting (>2.0 score difference)
- **Decision disagreements** with explanations

## 🎯 **Prerequisites**

### **1. AI Results File**
You need an existing AI analysis results file in the `output/` directory with format:
```
YYYYMMDD HH-MM-SS Session Messages.json
```

### **2. Matching Image Files**
- AI results must contain **actual image filenames** (not generic names)
- Images must be in the `../images/` directory
- Filenames in AI results must match the actual image files

### **3. Required Format**
AI results should be in session messages format:
```json
[
  {
    "role": "system",
    "content": "..."
  },
  {
    "role": "assistant", 
    "content": "```json\n{\n  \"file_name\": \"actual_filename\",\n  \"Overall_Score\": 8.5,\n  \"Decision\": \"Keep\"\n}\n```"
  }
]
```

## 📝 **Sample Output**

```
Available AI results files:
  1. 20250820 22-31-47 Mock AI Session Messages.json
  2. 20250807 15-39-27 Session Messages.json

Select file to compare (1-2) or 'q' to quit: 1

Running comparison with: 20250820 22-31-47 Mock AI Session Messages.json
Loading AI results...
Loaded 10 AI results
Running OpenCV analysis...
Generated 10 OpenCV results
Matching results...
Found 10 matching files

============================================================
COMPARISON SUMMARY
============================================================
Files compared: 10
AI average score: 7.4
OpenCV average score: 6.5
Mean absolute difference: 1.4
Decision agreement: 60.0%

DETAILED COMPARISON: AI vs OpenCV Image Quality Analysis
============================================================

INDIVIDUAL FILE COMPARISONS:
----------------------------------------
Filename                     AI Score   OpenCV Score   Difference   Agreement
--------------------------------------------------------------------------------
download                     7.5        8.7            1.2          ✓
pexels-mikebirdy-244206      7.0        7.7            0.7          ✗
pexels-albinberlin-919073    7.1        2.9            4.2          ✗

LARGE SCORE DIFFERENCES (>2.0):
----------------------------------------
pexels-albinberlin-919073: AI=7.1, OpenCV=2.9, Diff=4.2
pexels-alexgtacar-745150: AI=8.0, OpenCV=4.8, Diff=3.2

DECISION DISAGREEMENTS:
----------------------------------------
pexels-mikebirdy-244206: AI=Retake(7.0), OpenCV=Keep(7.7)
pexels-albinberlin-919073: AI=Keep(7.1), OpenCV=Retake(2.9)

Comparison saved to: /output/20250820 22-31-47 AI vs OpenCV Comparison.json
Detailed report saved to: /output/20250820 22-31-47 AI vs OpenCV Comparison.txt
```

## 🛠️ **Troubleshooting**

### **"No matching files found"**
- **Problem**: AI results use generic names like "car_image", "photo1"
- **Solution**: AI results must use actual image filenames
- **Fix**: Re-run AI analyzer with proper filename handling

### **"No AI results files found"**
- **Problem**: No AI session files in `/output/` directory
- **Solution**: Run the original AI analyzer first
- **Files needed**: `*Session Messages.json` files

### **"Could not load AI results"**
- **Problem**: Invalid JSON format in AI results file
- **Solution**: Check AI results file format and structure
- **Fix**: Ensure JSON is properly formatted in assistant messages

### **Import errors**
- **Problem**: Missing dependencies or incorrect Python path
- **Solution**: Install required packages:
```bash
pip install opencv-python numpy matplotlib scikit-image pillow
```

## 🔄 **Creating Test Data**

### **Generate Mock AI Results** (for demonstration)
```bash
cd /path/to/imagequalityanalyzer/opencv
python3 create_mock_ai_results.py
```

This creates mock AI results with matching filenames for testing the comparison tool.

### **Run Working Demo**
```bash
cd /path/to/imagequalityanalyzer/opencv
python3 demo_working_comparison.py
```

Shows how the comparison tool works with properly formatted data.

## 📁 **File Structure**

```
imagequalityanalyzer/
├── opencv/
│   ├── comparison_tool.py          # Main comparison tool
│   ├── demo_working_comparison.py  # Working demonstration
│   ├── create_mock_ai_results.py   # Mock data generator
│   └── debug_matching.py           # Debugging tool
├── images/                         # Source images
└── output/                         # Results directory
    ├── *Session Messages.json      # AI results (required)
    └── *Comparison.json            # Generated comparisons
```

## 🎯 **Best Practices**

### **1. Consistent Naming**
- Use actual image filenames in AI results
- Maintain consistent file extensions
- Avoid generic or placeholder names

### **2. Proper Validation**
- Run comparison on representative image sets
- Review large score differences manually
- Investigate decision disagreements

### **3. Documentation**
- Save comparison results for future reference
- Document any significant findings
- Track changes between AI and OpenCV approaches

## 🚀 **Advanced Usage**

### **Programmatic Usage**
```python
from comparison_tool import ResultsComparator

comparator = ResultsComparator()
results = comparator.run_comparison('path/to/ai_results.json', 'general')

if 'error' not in results:
    print(f"Agreement: {results['statistics']['decision_agreement']['percentage']}%")
    comparator.save_comparison_results(results)
```

### **Different Analysis Profiles**
```python
# Compare with different OpenCV profiles
results_general = comparator.run_comparison(ai_file, 'general')
results_document = comparator.run_comparison(ai_file, 'document') 
results_portrait = comparator.run_comparison(ai_file, 'portrait')
```

### **Custom Output**
```python
# Save with custom filename
output_file = comparator.save_comparison_results(
    results, 
    "custom_comparison_report.json"
)
```

The comparison tool is essential for validating that your OpenCV implementation provides equivalent quality analysis to the original AI-based system! 🎯
