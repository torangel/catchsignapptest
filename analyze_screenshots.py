#!/usr/bin/env python3
"""
CatchSign App Screenshot Analysis Tool - Multi-Version Support

This script:
1. Uses Azure AI Vision to extract text from all screenshots in any app version folder
2. Stores OCR results in a structured folder
3. Uses Claude agent to analyze the results and create reports with image hyperlinks

Works across different app versions by specifying the version folder.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import argparse

try:
    import requests
    from dotenv import load_dotenv
except ImportError:
    print("Installing required packages...")
    os.system("pip install requests python-dotenv")
    import requests
    from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

class AzureVisionAnalyzer:
    def __init__(self):
        self.endpoint = os.getenv('AZURE_AI_VISION_ENDPOINT')
        self.key = os.getenv('AZURE_AI_VISION_KEY')
        
        if not self.endpoint or not self.key:
            raise ValueError("Azure AI Vision credentials not found in .env file")
        
        # Remove trailing slash from endpoint if present
        self.endpoint = self.endpoint.rstrip('/')
        
        self.vision_url = f"{self.endpoint}/vision/v3.2/read/analyze"
        self.headers = {
            'Ocp-Apim-Subscription-Key': self.key,
            'Content-Type': 'application/octet-stream'
        }

    def analyze_image(self, image_path: str) -> Dict:
        """Analyze a single image using Azure AI Vision OCR"""
        try:
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
            
            # Start the OCR operation
            response = requests.post(self.vision_url, headers=self.headers, data=image_data)
            
            if response.status_code != 202:
                return {
                    'error': f'OCR initiation failed: {response.status_code} - {response.text}',
                    'text': '',
                    'confidence': 0,
                    'raw_response': None
                }
            
            operation_location = response.headers.get('Operation-Location')
            if not operation_location:
                return {
                    'error': 'No Operation-Location header received',
                    'text': '',
                    'confidence': 0,
                    'raw_response': None
                }
            
            # Poll for results
            max_attempts = 30
            for attempt in range(max_attempts):
                time.sleep(1)  # Wait before polling
                
                result_response = requests.get(operation_location, headers={'Ocp-Apim-Subscription-Key': self.key})
                
                if result_response.status_code != 200:
                    continue
                
                result = result_response.json()
                status = result.get('status')
                
                if status == 'succeeded':
                    return self._extract_text_from_result(result)
                elif status == 'failed':
                    return {
                        'error': f'OCR failed: {result.get("error", "Unknown error")}',
                        'text': '',
                        'confidence': 0,
                        'raw_response': result
                    }
            
            return {
                'error': 'OCR operation timed out',
                'text': '',
                'confidence': 0,
                'raw_response': None
            }
            
        except Exception as e:
            return {
                'error': f'Exception during OCR: {str(e)}',
                'text': '',
                'confidence': 0,
                'raw_response': None
            }

    def _extract_text_from_result(self, result: Dict) -> Dict:
        """Extract text and confidence from Azure Vision result"""
        extracted_text = []
        total_confidence = 0
        line_count = 0
        
        try:
            analyze_result = result.get('analyzeResult', {})
            read_results = analyze_result.get('readResults', [])
            
            for read_result in read_results:
                lines = read_result.get('lines', [])
                for line in lines:
                    text = line.get('text', '')
                    confidence = line.get('confidence', 0)
                    
                    if text.strip():
                        extracted_text.append(text)
                        total_confidence += confidence
                        line_count += 1
            
            avg_confidence = total_confidence / line_count if line_count > 0 else 0
            
            return {
                'text': '\n'.join(extracted_text),
                'confidence': avg_confidence,
                'error': None,
                'raw_response': result
            }
            
        except Exception as e:
            return {
                'error': f'Error extracting text: {str(e)}',
                'text': '',
                'confidence': 0,
                'raw_response': result
            }

class ScreenshotOCRProcessor:
    def __init__(self, version_folder: str):
        self.base_path = Path(__file__).parent
        self.version_folder = Path(version_folder)
        self.version_path = self.base_path / self.version_folder
        self.vision_analyzer = AzureVisionAnalyzer()
        
        # Validate version folder exists
        if not self.version_path.exists():
            raise ValueError(f"Version folder not found: {self.version_path}")
        
        # Create OCR results folder at the root level
        self.ocr_results_folder = self.base_path / "ocr_results"
        self.ocr_results_folder.mkdir(exist_ok=True)
        
    def process_all_screenshots(self) -> str:
        """Process all screenshots and store OCR results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H_%M")
        session_folder = self.ocr_results_folder / f"{self.version_folder.name}_{timestamp}"
        session_folder.mkdir(exist_ok=True)
        
        results = {
            'session_id': f"{self.version_folder.name}_{timestamp}",
            'app_version': str(self.version_folder.name),
            'processing_timestamp': datetime.now().isoformat(),
            'base_path': str(self.base_path),
            'version_path': str(self.version_path),
            'folders': {},
            'summary': {}
        }
        
        # Process Norwegian screenshots
        norwegian_path = self.version_path / 'norwegian'
        if norwegian_path.exists():
            print(f"Processing Norwegian screenshots for {self.version_folder.name}...")
            norwegian_results = self._process_folder(norwegian_path, 'norwegian', session_folder)
            results['folders']['norwegian'] = norwegian_results
        
        # Process English screenshots
        english_path = self.version_path / 'english'
        if english_path.exists():
            print(f"Processing English screenshots for {self.version_folder.name}...")
            english_results = self._process_folder(english_path, 'english', session_folder)
            results['folders']['english'] = english_results
        
        # Create summary
        results['summary'] = {
            'norwegian_count': len(results['folders'].get('norwegian', {})),
            'english_count': len(results['folders'].get('english', {})),
            'total_screenshots': len(results['folders'].get('norwegian', {})) + len(results['folders'].get('english', {})),
            'session_folder': str(session_folder)
        }
        
        # Save session metadata
        session_metadata_file = session_folder / "session_metadata.json"
        with open(session_metadata_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Create Claude prompt file
        self._create_claude_prompt(session_folder, results)
        
        print(f"OCR processing complete for {self.version_folder.name}!")
        print(f"Results saved to: {session_folder}")
        print(f"Total screenshots processed: {results['summary']['total_screenshots']}")
        
        return str(session_folder)

    def _process_folder(self, folder_path: Path, language: str, session_folder: Path) -> Dict:
        """Process all screenshots in a folder"""
        results = {}
        
        # Create language-specific folder in session
        lang_folder = session_folder / language
        lang_folder.mkdir(exist_ok=True)
        
        image_files = list(folder_path.glob('*.png')) + list(folder_path.glob('*.jpg')) + list(folder_path.glob('*.jpeg'))
        image_files.sort()
        
        for i, image_file in enumerate(image_files, 1):
            print(f"  Processing {image_file.name} ({i}/{len(image_files)})")
            
            # Perform OCR
            ocr_result = self.vision_analyzer.analyze_image(str(image_file))
            
            # Store individual OCR result with relative path for hyperlinks
            relative_image_path = image_file.relative_to(self.base_path)
            
            result_data = {
                'filename': image_file.name,
                'original_path': str(image_file),
                'relative_path': str(relative_image_path),
                'expected_language': language,
                'app_version': str(self.version_folder.name),
                'processing_timestamp': datetime.now().isoformat(),
                'ocr_result': ocr_result
            }
            
            # Save individual result file
            result_file = lang_folder / f"{image_file.stem}_ocr.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            
            results[image_file.name] = {
                'result_file': str(result_file),
                'relative_path': str(relative_image_path),
                'text': ocr_result.get('text', ''),
                'ocr_confidence': ocr_result.get('confidence', 0),
                'ocr_error': ocr_result.get('error'),
                'has_error': bool(ocr_result.get('error'))
            }
        
        return results

    def _create_claude_prompt(self, session_folder: Path, results: Dict):
        """Create a prompt file for Claude to analyze the OCR results"""
        
        prompt_content = f"""# CatchSign App Screenshot Analysis - Claude Agent Task

## Session Information
- **Session ID**: {results['session_id']}
- **App Version**: {results['app_version']}
- **Processing Date**: {results['processing_timestamp']}
- **Total Screenshots**: {results['summary']['total_screenshots']}
- **Norwegian Screenshots**: {results['summary']['norwegian_count']}
- **English Screenshots**: {results['summary']['english_count']}

## Task for Claude Agent

You are a specialized test agent analyzing mobile app screenshots for language consistency issues. 

### Your Mission:
1. **Analyze OCR Results**: Review all the extracted text from screenshots in both Norwegian and English folders
2. **Language Detection**: Determine if the extracted text is actually in Norwegian, English, or mixed/unknown
3. **Find Issues**: Identify language mismatches (e.g., English text in Norwegian folder, Norwegian text in English folder)
4. **Create Comprehensive Report**: Generate a detailed markdown report with findings INCLUDING HYPERLINKS TO IMAGES

### Data Structure:
- Each screenshot has an individual OCR result file in the respective language folder
- OCR results include extracted text, confidence scores, and any processing errors
- Screenshots are organized by expected language (norwegian/ and english/ folders)
- Each OCR result includes the relative path to the original image for hyperlinking

### OCR Results Location:
```
{session_folder}/
├── norwegian/
│   ├── Screenshot_*.json (individual OCR results)
├── english/
│   ├── Screenshot_*.json (individual OCR results)
└── session_metadata.json (overall session data)
```

### Analysis Instructions:

1. **Read all OCR result files** from both norwegian/ and english/ folders
2. **For each screenshot, analyze**:
   - The extracted text content
   - Whether the language matches the expected folder (norwegian vs english)
   - OCR confidence and any processing errors
   - Specific Norwegian/English words and phrases found

3. **Language Detection Guidelines**:
   - Look for Norwegian words like: og, eller, med, til, fra, jeg, du, vi, de, det, en, et, på, i, av, for, så, ikke, bare, skal, kan, vil, har, var, er, som, når, hvor, hva, hvem, dette, disse, den, ett, nå, her, der, også, men, fordi, hvis, siden, logg, inn, registrer, avbryt, fortsett, tilbake, neste, ferdig, lagre, slette, innstillinger, profil, konto, passord, bruker, brukernavn, e-post, telefon, adresse
   - Look for English words like: and, or, with, to, from, i, you, we, they, the, a, an, on, in, of, for, so, not, only, should, can, will, have, had, is, are, was, were, as, when, where, what, who, this, these, that, one, now, here, there, also, but, because, if, since, login, register, cancel, continue, back, next, done, save, delete, settings, profile, account, password, user, username, email, phone, address

4. **Create Report** with format including IMAGE HYPERLINKS:


```markdown
# CatchSign App Analysis Report - {results['app_version']}
Generated: [Current timestamp]

## Summary
- **App Version**: {results['app_version']}
- **Norwegian Screenshots**: X files
- **English Screenshots**: Y files  
- **Total Issues Found**: Z
- **High Priority Issues**: N (language mismatches)

## Critical Issues Found
### Language Mismatches
- [List specific files with wrong language content, include hyperlinks to images]

## Detailed Analysis
### Screen Comparisons
[For each aligned pair, show Norwegian vs English with analysis and IMAGE HYPERLINKS]
Make sure to include ALL pairs, even if no issues found. If errors are found (english vs norwegian or norwegian vs english), highlight them clearly.

## Recommendations
[Your recommendations for fixing the issues]
```

### IMPORTANT: Include Image Hyperlinks
For each screenshot mentioned in the report, include a hyperlink to the actual image file using the relative_path from the OCR results. Format as:
```markdown
**[Screenshot_filename.png](../relative/path/to/image.png)**
```

This allows reviewers to click directly to see the actual screenshot being analyzed.

### Important Notes:
- Focus on **language consistency** as the primary concern
- **Language mismatches are HIGH PRIORITY** issues that need immediate attention
- Consider OCR errors but prioritize actual language content issues
- Use your advanced language understanding to make better decisions than simple word matching
- Provide specific examples and evidence for each issue found
- **ALWAYS include hyperlinks to the actual screenshot images** for easy reference

### Next Steps:
1. Read all the OCR result files in this session folder
2. Analyze the content using your language expertise
3. Generate the comprehensive report WITH IMAGE HYPERLINKS
4. Save the report as `claude_analysis_report.md` in the session folder

Please proceed with the analysis using your superior language understanding capabilities!
"""

        prompt_file = session_folder / "claude_prompt.md"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt_content)
        
        print(f"Claude prompt created: {prompt_file}")

def main():
    """Main function to run the OCR processing"""
    parser = argparse.ArgumentParser(description='Process screenshots for CatchSign app analysis')
    parser.add_argument('version', nargs='?', help='App version folder name (e.g., 2.0.0.b242)')
    parser.add_argument('--list-versions', action='store_true', help='List available version folders')
    
    args = parser.parse_args()
    
    base_path = Path(__file__).parent
    
    if args.list_versions:
        print("Available version folders:")
        for item in base_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name not in ['ocr_results', '__pycache__']:
                norwegian_path = item / 'norwegian'
                english_path = item / 'english'
                if norwegian_path.exists() or english_path.exists():
                    nor_count = len(list(norwegian_path.glob('*.png'))) if norwegian_path.exists() else 0
                    eng_count = len(list(english_path.glob('*.png'))) if english_path.exists() else 0
                    print(f"  {item.name} ({nor_count} Norwegian, {eng_count} English screenshots)")
        return 0
    
    if not args.version:
        print("Error: Please specify a version folder")
        print("Usage: python analyze_screenshots.py <version>")
        print("Use --list-versions to see available versions")
        return 1
    
    version_folder = args.version
    
    print("CatchSign App Screenshot OCR Processor")
    print("=" * 50)
    print("Phase 1: Azure AI Vision OCR Processing")
    print(f"Processing version: {version_folder}")
    
    try:
        processor = ScreenshotOCRProcessor(version_folder)
        session_folder = processor.process_all_screenshots()
        
        print("\n" + "=" * 50)
        print("Phase 1 Complete!")
        print(f"OCR results stored in: {session_folder}")
        print("\nNext Steps:")
        print("1. Review the Claude prompt file in the session folder")
        print("2. Use Claude agent to analyze the OCR results")
        print("3. Claude will create a comprehensive analysis report with image hyperlinks")
        print("\nClaude will now have access to all OCR data and can make")
        print("intelligent decisions about language detection and issues!")
        
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)