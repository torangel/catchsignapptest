#!/usr/bin/env python3
"""
CatchSign Analysis - Full Pipeline with Multi-Version Support

This script runs the complete analysis pipeline:
1. OCR processing with Azure AI Vision
2. Claude-powered language analysis and reporting with image hyperlinks

Works across different app versions.
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import argparse

def run_full_analysis(version_folder: str):
    """Run the complete analysis pipeline for a specific version"""
    script_dir = Path(__file__).parent
    
    print("CatchSign App - Complete Analysis Pipeline")
    print("=" * 50)
    print(f"Analyzing version: {version_folder}")
    
    # Step 1: Run OCR processing
    print("\nStep 1: Running Azure AI Vision OCR processing...")
    try:
        result = subprocess.run([
            sys.executable, 
            str(script_dir / "analyze_screenshots.py"),
            version_folder
        ], capture_output=True, text=True, cwd=script_dir)
        
        if result.returncode != 0:
            print(f"OCR processing failed: {result.stderr}")
            print(f"Output: {result.stdout}")
            return False
            
        print("OCR processing completed successfully!")
        
        # Extract session folder from output
        output_lines = result.stdout.split('\n')
        session_folder = None
        for line in output_lines:
            if "OCR results stored in:" in line:
                session_folder = line.split("OCR results stored in: ")[1].strip()
                break
        
        if not session_folder:
            print("Could not determine session folder location")
            return False
            
        session_path = Path(session_folder)
        
    except Exception as e:
        print(f"Error running OCR processing: {e}")
        return False
    
    # Step 2: Notify about Claude analysis
    print("\n" + "=" * 50)
    print("Step 2: Claude Analysis Ready!")
    print(f"Session folder: {session_path}")
    
    # Check if Claude report exists (it will be created manually by Claude)
    claude_report = session_path / "claude_analysis_report.md"
    if claude_report.exists():
        print(f"✅ Claude analysis report: {claude_report}")
        
        # Show summary from the report
        try:
            with open(claude_report, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract summary section
            lines = content.split('\n')
            in_summary = False
            summary_lines = []
            
            for line in lines:
                if line.startswith('## Summary'):
                    in_summary = True
                    continue
                elif line.startswith('## ') and in_summary:
                    break
                elif in_summary:
                    summary_lines.append(line)
            
            if summary_lines:
                print("\nAnalysis Summary:")
                for line in summary_lines:
                    if line.strip():
                        print(f"  {line}")
                        
        except Exception as e:
            print(f"Could not read summary: {e}")
    else:
        print("📋 Claude prompt ready for analysis")
        print(f"   Prompt file: {session_path / 'claude_prompt.md'}")
    
    print("\n" + "=" * 50)
    print("Analysis Pipeline Complete!")
    print(f"Results available in: {session_path}")
    print(f"\nFiles generated:")
    print(f"  📁 OCR Data: {session_path}")
    print(f"  📊 Claude Report: {claude_report}")
    print(f"  📋 Session Metadata: {session_path / 'session_metadata.json'}")
    print(f"  🎯 Claude Prompt: {session_path / 'claude_prompt.md'}")
    
    return True

def list_versions():
    """List available version folders"""
    base_path = Path(__file__).parent
    print("Available version folders:")
    
    found_versions = []
    for item in base_path.iterdir():
        if item.is_dir() and not item.name.startswith('.') and item.name not in ['ocr_results', '__pycache__']:
            norwegian_path = item / 'norwegian'
            english_path = item / 'english'
            if norwegian_path.exists() or english_path.exists():
                nor_count = len(list(norwegian_path.glob('*.png'))) if norwegian_path.exists() else 0
                eng_count = len(list(english_path.glob('*.png'))) if english_path.exists() else 0
                print(f"  {item.name} ({nor_count} Norwegian, {eng_count} English screenshots)")
                found_versions.append(item.name)
    
    if not found_versions:
        print("  No version folders with screenshots found")
    
    return found_versions

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run complete CatchSign app analysis pipeline')
    parser.add_argument('version', nargs='?', help='App version folder name (e.g., 2.0.0.b242)')
    parser.add_argument('--list-versions', action='store_true', help='List available version folders')
    
    args = parser.parse_args()
    
    if args.list_versions:
        list_versions()
        return 0
    
    if not args.version:
        print("Error: Please specify a version folder")
        print("Usage: python run_full_analysis.py <version>")
        print("Use --list-versions to see available versions")
        print("\nAvailable versions:")
        list_versions()
        return 1
    
    success = run_full_analysis(args.version)
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)