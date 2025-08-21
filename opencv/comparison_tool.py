"""
Comparison utility for OpenCV vs AI-based image quality analysis results.

This script helps validate the OpenCV implementation by comparing its results
with the original AI-based analysis results.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple
import statistics

try:
    from .opencv_image_quality_analyzer import OpenCVImageQualityAnalyzer
except ImportError:
    from opencv_image_quality_analyzer import OpenCVImageQualityAnalyzer


class ResultsComparator:
    """Compare OpenCV analysis results with AI-based results."""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.output_dir = self.base_path / "output"
        self.images_dir = self.base_path / "images"
        
    def load_ai_results(self, ai_results_file: str) -> List[Dict]:
        """
        Load AI analysis results from JSON file.
        
        Args:
            ai_results_file: Path to AI results JSON file
            
        Returns:
            List of AI analysis results
        """
        try:
            with open(ai_results_file, 'r') as f:
                data = json.load(f)
                
            # Handle different file formats
            if isinstance(data, list):
                # Direct list of results
                return data
            elif isinstance(data, dict) and 'results' in data:
                # Structured format with metadata
                return data['results']
            else:
                # Try to extract from messages format
                messages = data if isinstance(data, list) else data.get('messages', [])
                results = []
                for msg in messages:
                    if msg.get('role') == 'assistant':
                        try:
                            content = msg.get('content', '')
                            if content.strip().startswith('{'):
                                result = json.loads(content)
                                results.append(result)
                        except json.JSONDecodeError:
                            continue
                return results
                
        except Exception as e:
            print(f"Error loading AI results: {e}")
            return []
    
    def run_opencv_analysis(self, profile: str = 'general') -> List[Dict]:
        """
        Run OpenCV analysis on the same images.
        
        Args:
            profile: Analysis profile to use
            
        Returns:
            List of OpenCV analysis results
        """
        analyzer = OpenCVImageQualityAnalyzer(profile=profile)
        return analyzer.analyze_batch(str(self.images_dir))
    
    def match_results(self, ai_results: List[Dict], opencv_results: List[Dict]) -> List[Tuple[Dict, Dict]]:
        """
        Match AI and OpenCV results by filename.
        
        Args:
            ai_results: List of AI analysis results
            opencv_results: List of OpenCV analysis results
            
        Returns:
            List of tuples (ai_result, opencv_result) for matched files
        """
        matches = []
        
        # Create lookup dict for OpenCV results
        opencv_lookup = {}
        for result in opencv_results:
            if 'file_name' in result:
                key = result['file_name'].lower()
                opencv_lookup[key] = result
        
        # Match with AI results
        for ai_result in ai_results:
            if 'file_name' in ai_result:
                ai_filename = ai_result['file_name'].lower()
                
                # Try exact match first
                if ai_filename in opencv_lookup:
                    matches.append((ai_result, opencv_lookup[ai_filename]))
                else:
                    # Try partial matches (in case of extension differences)
                    for opencv_key, opencv_result in opencv_lookup.items():
                        if ai_filename in opencv_key or opencv_key in ai_filename:
                            matches.append((ai_result, opencv_result))
                            break
        
        return matches
    
    def compare_scores(self, matches: List[Tuple[Dict, Dict]]) -> Dict:
        """
        Compare overall scores between AI and OpenCV results.
        
        Args:
            matches: List of matched result pairs
            
        Returns:
            Comparison statistics
        """
        if not matches:
            return {"error": "No matches found for comparison"}
        
        ai_scores = []
        opencv_scores = []
        score_differences = []
        decision_agreements = 0
        
        for ai_result, opencv_result in matches:
            ai_score = ai_result.get('Overall_Score', 0)
            opencv_score = opencv_result.get('Overall_Score', 0)
            
            if isinstance(ai_score, (int, float)) and isinstance(opencv_score, (int, float)):
                ai_scores.append(ai_score)
                opencv_scores.append(opencv_score)
                score_differences.append(abs(ai_score - opencv_score))
                
                # Check decision agreement
                ai_decision = ai_result.get('Decision', '').lower()
                opencv_decision = opencv_result.get('Decision', '').lower()
                if ai_decision == opencv_decision:
                    decision_agreements += 1
        
        if not ai_scores:
            return {"error": "No valid scores found for comparison"}
        
        return {
            "total_matches": len(matches),
            "valid_comparisons": len(ai_scores),
            "ai_stats": {
                "mean": round(statistics.mean(ai_scores), 2),
                "median": round(statistics.median(ai_scores), 2),
                "stdev": round(statistics.stdev(ai_scores) if len(ai_scores) > 1 else 0, 2),
                "min": round(min(ai_scores), 2),
                "max": round(max(ai_scores), 2)
            },
            "opencv_stats": {
                "mean": round(statistics.mean(opencv_scores), 2),
                "median": round(statistics.median(opencv_scores), 2),
                "stdev": round(statistics.stdev(opencv_scores) if len(opencv_scores) > 1 else 0, 2),
                "min": round(min(opencv_scores), 2),
                "max": round(max(opencv_scores), 2)
            },
            "difference_stats": {
                "mean_abs_difference": round(statistics.mean(score_differences), 2),
                "median_abs_difference": round(statistics.median(score_differences), 2),
                "max_difference": round(max(score_differences), 2),
                "min_difference": round(min(score_differences), 2)
            },
            "decision_agreement": {
                "agreements": decision_agreements,
                "total": len(matches),
                "percentage": round((decision_agreements / len(matches)) * 100, 1)
            }
        }
    
    def generate_detailed_comparison(self, matches: List[Tuple[Dict, Dict]]) -> str:
        """
        Generate a detailed comparison report.
        
        Args:
            matches: List of matched result pairs
            
        Returns:
            Formatted comparison report
        """
        if not matches:
            return "No matched results available for comparison."
        
        report = []
        report.append("=" * 80)
        report.append("DETAILED COMPARISON: AI vs OpenCV Image Quality Analysis")
        report.append("=" * 80)
        report.append("")
        
        # Individual comparisons
        report.append("INDIVIDUAL FILE COMPARISONS:")
        report.append("-" * 40)
        report.append(f"{'Filename':<30} {'AI Score':<10} {'OpenCV Score':<12} {'Difference':<12} {'Agreement'}")
        report.append("-" * 80)
        
        large_differences = []
        disagreements = []
        
        for ai_result, opencv_result in matches:
            filename = ai_result.get('file_name', 'Unknown')
            ai_score = ai_result.get('Overall_Score', 0)
            opencv_score = opencv_result.get('Overall_Score', 0)
            
            if isinstance(ai_score, (int, float)) and isinstance(opencv_score, (int, float)):
                difference = abs(ai_score - opencv_score)
                ai_decision = ai_result.get('Decision', '').lower()
                opencv_decision = opencv_result.get('Decision', '').lower()
                agreement = "✓" if ai_decision == opencv_decision else "✗"
                
                report.append(f"{filename:<30} {ai_score:<10.1f} {opencv_score:<12.1f} {difference:<12.1f} {agreement}")
                
                # Track significant differences
                if difference > 2.0:
                    large_differences.append((filename, ai_score, opencv_score, difference))
                
                if ai_decision != opencv_decision:
                    disagreements.append((filename, ai_decision, opencv_decision, ai_score, opencv_score))
        
        # Highlight issues
        if large_differences:
            report.append("")
            report.append("LARGE SCORE DIFFERENCES (>2.0):")
            report.append("-" * 40)
            for filename, ai_score, opencv_score, diff in large_differences:
                report.append(f"{filename}: AI={ai_score:.1f}, OpenCV={opencv_score:.1f}, Diff={diff:.1f}")
        
        if disagreements:
            report.append("")
            report.append("DECISION DISAGREEMENTS:")
            report.append("-" * 40)
            for filename, ai_dec, opencv_dec, ai_score, opencv_score in disagreements:
                report.append(f"{filename}: AI={ai_dec}({ai_score:.1f}), OpenCV={opencv_dec}({opencv_score:.1f})")
        
        return "\n".join(report)
    
    def run_comparison(self, ai_results_file: str, opencv_profile: str = 'general') -> Dict:
        """
        Run complete comparison between AI and OpenCV results.
        
        Args:
            ai_results_file: Path to AI results file
            opencv_profile: OpenCV analysis profile to use
            
        Returns:
            Complete comparison results
        """
        print("Loading AI results...")
        ai_results = self.load_ai_results(ai_results_file)
        
        if not ai_results:
            return {"error": "Could not load AI results"}
        
        print(f"Loaded {len(ai_results)} AI results")
        
        print("Running OpenCV analysis...")
        opencv_results = self.run_opencv_analysis(opencv_profile)
        
        if not opencv_results:
            return {"error": "OpenCV analysis failed"}
        
        print(f"Generated {len(opencv_results)} OpenCV results")
        
        print("Matching results...")
        matches = self.match_results(ai_results, opencv_results)
        
        if not matches:
            return {"error": "No matching files found between AI and OpenCV results"}
        
        print(f"Found {len(matches)} matching files")
        
        # Generate comparison statistics
        comparison_stats = self.compare_scores(matches)
        
        # Generate detailed report
        detailed_report = self.generate_detailed_comparison(matches)
        
        return {
            "ai_results_count": len(ai_results),
            "opencv_results_count": len(opencv_results),
            "matched_files": len(matches),
            "statistics": comparison_stats,
            "detailed_report": detailed_report,
            "matches": matches
        }
    
    def save_comparison_results(self, comparison_results: Dict, output_filename: str = None) -> str:
        """
        Save comparison results to file.
        
        Args:
            comparison_results: Results from run_comparison
            output_filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        if output_filename is None:
            timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d %H-%M-%S')
            output_filename = f"{timestamp} AI vs OpenCV Comparison.json"
        
        output_path = self.output_dir / output_filename
        
        try:
            # Create a clean version for saving (remove large data)
            save_data = comparison_results.copy()
            if 'matches' in save_data:
                # Save only summary of matches to avoid huge files
                save_data['sample_matches'] = save_data['matches'][:5]  # First 5 for reference
                del save_data['matches']
            
            with open(output_path, 'w') as f:
                json.dump(save_data, f, indent=4)
            
            print(f"Comparison results saved to: {output_path}")
            
            # Also save the detailed report as text
            if 'detailed_report' in comparison_results:
                report_path = output_path.with_suffix('.txt')
                with open(report_path, 'w') as f:
                    f.write(comparison_results['detailed_report'])
                print(f"Detailed report saved to: {report_path}")
            
            return str(output_path)
            
        except Exception as e:
            print(f"Error saving comparison results: {e}")
            return ""


def main():
    """Main function for running comparisons."""
    comparator = ResultsComparator()
    
    # Look for AI results files in output directory
    ai_files = list(comparator.output_dir.glob("*Session Messages.json"))
    
    if not ai_files:
        print("No AI results files found in output directory.")
        print("Please run the original AI analyzer first to generate comparison data.")
        return
    
    print("Available AI results files:")
    for i, file_path in enumerate(ai_files):
        print(f"  {i+1}. {file_path.name}")
    
    try:
        choice = input(f"\nSelect file to compare (1-{len(ai_files)}) or 'q' to quit: ").strip()
        
        if choice.lower() == 'q':
            return
        
        file_index = int(choice) - 1
        if 0 <= file_index < len(ai_files):
            selected_file = ai_files[file_index]
            
            print(f"\nRunning comparison with: {selected_file.name}")
            
            # Run comparison
            results = comparator.run_comparison(str(selected_file))
            
            if 'error' in results:
                print(f"Comparison failed: {results['error']}")
                return
            
            # Display results
            print("\n" + "="*60)
            print("COMPARISON SUMMARY")
            print("="*60)
            
            stats = results.get('statistics', {})
            if 'error' not in stats:
                print(f"Files compared: {stats['valid_comparisons']}")
                print(f"AI average score: {stats['ai_stats']['mean']}")
                print(f"OpenCV average score: {stats['opencv_stats']['mean']}")
                print(f"Mean absolute difference: {stats['difference_stats']['mean_abs_difference']}")
                print(f"Decision agreement: {stats['decision_agreement']['percentage']}%")
            
            # Show detailed report
            if 'detailed_report' in results:
                print("\n" + results['detailed_report'])
            
            # Save results
            saved_file = comparator.save_comparison_results(results)
            if saved_file:
                print(f"\nComparison saved to: {saved_file}")
        
        else:
            print("Invalid selection.")
            
    except (ValueError, KeyboardInterrupt):
        print("Invalid input or operation cancelled.")


if __name__ == "__main__":
    main()
