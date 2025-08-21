"""
OpenCV Image Quality Analysis Session

This module provides a session-based interface that maintains compatibility 
with the original AI-based image quality analyzer while using OpenCV algorithms.
"""

import os
import json
import datetime
from pathlib import Path
from typing import List, Dict, Optional

try:
    from .opencv_image_quality_analyzer import OpenCVImageQualityAnalyzer
except ImportError:
    from opencv_image_quality_analyzer import OpenCVImageQualityAnalyzer


class OpenCVAnalysisSession:
    """
    Session-based wrapper for OpenCV image quality analysis.
    
    Provides compatibility with the original AI-based analyzer interface
    while using computer vision algorithms for quality assessment.
    """
    
    def __init__(self, profile: str = 'general'):
        """
        Initialize the analysis session.
        
        Args:
            profile: Analysis profile ('general', 'document', 'portrait')
        """
        self.analyzer = OpenCVImageQualityAnalyzer(profile=profile)
        self.profile = profile
        
        # Session tracking
        self.total_images_processed = 0
        self.session_start_time = datetime.datetime.now()
        self.last_results = []
        self.messages = []  # For compatibility with original interface
        
        # Path configuration
        container_mode = os.environ.get('CONTAINER_MODE', 'false').lower() == 'true'
        
        if container_mode:
            # Running in container
            self.base_path = Path("/app")
            self.images_dir = Path("/app/images")
            self.output_dir = Path("/app/output")
        else:
            # Running on host
            current_dir = Path(__file__).parent
            self.base_path = current_dir.parent
            self.images_dir = self.base_path / "images"
            self.output_dir = self.base_path / "output"
        
        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)
        
        print(f"OpenCV Image Quality Analysis Session initialized")
        print(f"Profile: {profile}")
        print(f"Images directory: {self.images_dir}")
        print(f"Output directory: {self.output_dir}")
        
    def load_images(self) -> int:
        """
        Load and count available images in the images directory.
        
        Returns:
            Number of images found
        """
        if not self.images_dir.exists():
            print(f"Warning: Images directory not found: {self.images_dir}")
            return 0
            
        image_files = []
        for ext in self.analyzer.supported_formats:
            image_files.extend(self.images_dir.glob(f"*{ext}"))
            image_files.extend(self.images_dir.glob(f"*{ext.upper()}"))
            
        print(f"Found {len(image_files)} images to analyze")
        return len(image_files)
    
    def analyze_all_images(self) -> List[Dict]:
        """
        Analyze all images in the images directory.
        
        Returns:
            List of analysis results
        """
        print("Starting batch analysis of all images...")
        
        try:
            results = self.analyzer.analyze_batch(str(self.images_dir))
            self.last_results = results
            self.total_images_processed += len([r for r in results if 'error' not in r])
            
            print(f"\nAnalysis complete!")
            print(f"Images processed: {len(results)}")
            
            # Generate summary
            summary = self.analyzer._generate_summary(results)
            if 'error' not in summary:
                print(f"Average score: {summary['average_score']}")
                print(f"Keep recommendations: {summary['keep_recommendations']}")
                print(f"Retake recommendations: {summary['retake_recommendations']}")
            
            return results
            
        except Exception as e:
            print(f"Error during batch analysis: {e}")
            return []
    
    def analyze_single_image(self, image_name: str) -> Dict:
        """
        Analyze a specific image by name.
        
        Args:
            image_name: Name of the image file (with or without extension)
            
        Returns:
            Analysis result dictionary
        """
        # Find the image file
        image_path = None
        
        # Try exact match first
        potential_path = self.images_dir / image_name
        if potential_path.exists():
            image_path = potential_path
        else:
            # Try adding extensions
            for ext in self.analyzer.supported_formats:
                potential_path = self.images_dir / f"{image_name}{ext}"
                if potential_path.exists():
                    image_path = potential_path
                    break
                    
        if image_path is None:
            return {
                "file_name": image_name,
                "error": f"Image not found: {image_name}",
                "Overall_Score": 0.0,
                "Decision": "Error"
            }
        
        print(f"Analyzing: {image_path.name}")
        result = self.analyzer.analyze_single_image(str(image_path))
        
        if 'error' not in result:
            self.total_images_processed += 1
            print(f"Score: {result['Overall_Score']} - Decision: {result['Decision']}")
        
        return result
    
    def chat(self, prompt: str) -> List[Dict]:
        """
        Process a chat prompt and return analysis results.
        Maintains compatibility with the original chat interface.
        
        Args:
            prompt: User prompt (typically requesting analysis)
            
        Returns:
            List of analysis results
        """
        # Add message to history for compatibility
        self.add_message(prompt, role='user')
        
        # Perform analysis
        results = self.analyze_all_images()
        
        # Add results to message history
        for result in results:
            self.add_message(json.dumps(result, indent=2), role='assistant')
        
        return results
    
    def add_message(self, message: str, role: str = 'user'):
        """Add a message to the conversation history."""
        self.messages.append({
            "role": role,
            "content": message,
            "timestamp": datetime.datetime.now().isoformat()
        })
    
    def clear_messages(self):
        """Clear the conversation history."""
        self.messages = []
    
    def save(self, results: Optional[List[Dict]] = None) -> str:
        """
        Save analysis results and session data to files.
        
        Args:
            results: Optional results to save (uses last_results if None)
            
        Returns:
            Path to saved file
        """
        if results is None:
            results = self.last_results
            
        if not results:
            print("No results to save.")
            return ""
        
        try:
            # Save JSON results
            json_file = self.analyzer.save_results(results, str(self.output_dir))
            
            # Save detailed report
            report = self.analyzer.generate_detailed_report(results)
            report_path = self.output_dir / f"{datetime.datetime.now().strftime('%Y%m%d %H-%M-%S')} OpenCV Analysis Report.txt"
            
            with open(report_path, 'w') as f:
                f.write(report)
            
            # Save session messages for compatibility
            if self.messages:
                messages_path = self.output_dir / f"{datetime.datetime.now().strftime('%Y%m%d %H-%M-%S')} Session Messages.json"
                with open(messages_path, 'w') as f:
                    json.dump(self.messages, f, indent=4)
                print(f"Session messages saved to: {messages_path}")
            
            print(f"All results saved. JSON: {json_file}, Report: {report_path}")
            return json_file
            
        except Exception as e:
            print(f"Error saving results: {e}")
            return ""
    
    def start(self):
        """
        Start an interactive analysis session.
        Provides compatibility with the original chat-based interface.
        """
        print(f"\nStarting OpenCV Image Quality Analysis Session")
        print("=" * 50)
        print("Commands:")
        print("  'analyze' or 'start' - Analyze all images")
        print("  'analyze <filename>' - Analyze specific image")
        print("  'profile <name>' - Change analysis profile (general/document/portrait)")
        print("  'save' - Save current results")
        print("  'report' - Show detailed report")
        print("  'summary' - Show quick summary")
        print("  'exit', 'quit', or 'stop' - End session")
        print("=" * 50)
        
        # Load and show available images
        image_count = self.load_images()
        if image_count == 0:
            print("No images found. Please add images to the images folder.")
            return
        
        while True:
            try:
                user_input = input("\nOpenCV Analyzer> ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'stop']:
                    print("Session ended.")
                    break
                    
                elif user_input.lower() in ['analyze', 'start', '']:
                    results = self.analyze_all_images()
                    if results:
                        self.show_summary()
                        
                elif user_input.lower().startswith('analyze '):
                    filename = user_input[8:].strip()
                    result = self.analyze_single_image(filename)
                    print(json.dumps(result, indent=2))
                    
                elif user_input.lower().startswith('profile '):
                    new_profile = user_input[8:].strip()
                    if new_profile in ['general', 'document', 'portrait']:
                        self.analyzer = OpenCVImageQualityAnalyzer(profile=new_profile)
                        self.profile = new_profile
                        print(f"Profile changed to: {new_profile}")
                    else:
                        print("Invalid profile. Use: general, document, or portrait")
                        
                elif user_input.lower() == 'save':
                    saved_file = self.save()
                    if saved_file:
                        print("Results saved successfully.")
                        
                elif user_input.lower() == 'report':
                    if self.last_results:
                        report = self.analyzer.generate_detailed_report(self.last_results)
                        print("\n" + report)
                    else:
                        print("No results available. Run analysis first.")
                        
                elif user_input.lower() == 'summary':
                    self.show_summary()
                    
                else:
                    print("Unknown command. Type 'exit' to quit or 'analyze' to start analysis.")
                    
            except KeyboardInterrupt:
                print("\nSession interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def show_summary(self):
        """Display a quick summary of the last analysis results."""
        if not self.last_results:
            print("No analysis results available.")
            return
            
        summary = self.analyzer._generate_summary(self.last_results)
        
        if 'error' in summary:
            print(f"Summary error: {summary['error']}")
            return
            
        print(f"\nAnalysis Summary:")
        print(f"  Images analyzed: {summary['total_analyzed']}")
        print(f"  Average score: {summary['average_score']}")
        print(f"  Keep: {summary['keep_recommendations']} ({summary['keep_percentage']}%)")
        print(f"  Retake: {summary['retake_recommendations']}")
        
        # Show top and bottom performers
        valid_results = [r for r in self.last_results if 'Overall_Score' in r and isinstance(r['Overall_Score'], (int, float))]
        if valid_results:
            valid_results.sort(key=lambda x: x['Overall_Score'], reverse=True)
            
            print(f"\nBest image: {valid_results[0]['file_name']}.{valid_results[0]['file_extension']} (Score: {valid_results[0]['Overall_Score']})")
            if len(valid_results) > 1:
                print(f"Worst image: {valid_results[-1]['file_name']}.{valid_results[-1]['file_extension']} (Score: {valid_results[-1]['Overall_Score']})")


def main():
    """Main entry point for the OpenCV analysis session."""
    session = OpenCVAnalysisSession()
    session.start()


if __name__ == "__main__":
    main()
