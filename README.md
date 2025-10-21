# CatchSign App Screenshot Analysis - Multi-Version System

A comprehensive analysis system for mobile app screenshots that works across different app versions, using Azure AI Vision OCR and Claude-powered intelligent analysis.

## 🏗️ Architecture

### Multi-Version Support
The system is designed to work with multiple app versions organized in separate folders:
```
CatchSignAppV2Analysis/
├── .env                           # Azure credentials
├── requirements.txt               # Python dependencies
├── analyze_screenshots.py         # OCR processing script
├── run_full_analysis.py          # Complete pipeline
├── README.md                     # This file
├── 2.0.0.b242/                   # App version folder
│   ├── norwegian/                 # Norwegian screenshots
│   ├── english/                   # English screenshots
│   └── prompt.md                 # Version-specific notes
├── 2.1.0.b300/                   # Another version (example)
│   ├── norwegian/
│   └── english/
└── ocr_results/                   # All analysis results
    ├── 2.0.0.b242_20251021_10_30/
    └── 2.1.0.b300_20251021_11_15/
```

### Two-Phase Analysis Process

**Phase 1: OCR Processing**
- Extracts text from screenshots using Azure AI Vision
- Stores results in organized JSON files with image metadata
- Creates session folders with version and timestamp

**Phase 2: Claude Analysis**
- Intelligent language analysis beyond simple word matching
- Generates comprehensive reports with hyperlinked images
- Provides actionable recommendations for developers

## 🚀 Quick Start

### Prerequisites
1. Python 3.7+
2. Azure AI Vision credentials in `.env` file
3. Screenshot folders organized by version

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# List available versions
python run_full_analysis.py --list-versions
```

### Usage

#### Complete Pipeline (Recommended)
```bash
# Analyze specific version
python run_full_analysis.py 2.0.0.b242

# List available versions first
python run_full_analysis.py --list-versions
```

#### Individual Steps
```bash
# OCR processing only
python analyze_screenshots.py 2.0.0.b242

# List versions
python analyze_screenshots.py --list-versions
```

## 📁 Output Structure

Each analysis session creates a structured output:

```
ocr_results/
└── {version}_{timestamp}/
    ├── norwegian/
    │   ├── Screenshot_001_ocr.json    # Individual OCR results
    │   └── Screenshot_002_ocr.json
    ├── english/
    │   ├── Screenshot_001_ocr.json
    │   └── Screenshot_002_ocr.json
    ├── session_metadata.json          # Session overview
    ├── claude_prompt.md               # Analysis instructions
    └── claude_analysis_report.md      # Final report with image links
```

## 📊 Enhanced Reports with Image Hyperlinks

The Claude-generated reports now include direct hyperlinks to screenshot images:

```markdown
### Critical Issue: Language Mismatch
**[Screenshot_20251021-071928.png](../2.0.0.b242/norwegian/Screenshot_20251021-071928.png)**
- Expected: Norwegian
- Detected: English
- Issue: Biometrics screen entirely in English
```

This allows reviewers to click directly on filenames to view the actual screenshots.

## 🎯 Features

### Multi-Version Capabilities
- **Version Detection**: Automatically detects available app versions
- **Isolated Analysis**: Each version analyzed separately
- **Cross-Version Comparison**: Easy to compare issues across versions
- **Timestamped Sessions**: Track analysis over time

### Intelligent Analysis
- **Context-Aware Language Detection**: Claude understands app flow and context
- **Priority Classification**: Issues categorized by severity and impact
- **Pattern Recognition**: Identifies systemic localization problems
- **Actionable Recommendations**: Specific guidance for developers

### Enhanced Reporting
- **Hyperlinked Images**: Click to view actual screenshots
- **Executive Summaries**: High-level overview for stakeholders
- **Technical Details**: Detailed OCR and confidence data
- **Version Metadata**: Clear version and session tracking

## 📋 Example Usage Scenarios

### Scenario 1: New Version Analysis
```bash
# Developer creates new version folder
mkdir 2.1.0.b300
mkdir 2.1.0.b300/norwegian 2.1.0.b300/english

# Copy screenshots to folders
# Run analysis
python run_full_analysis.py 2.1.0.b300
```

### Scenario 2: Cross-Version Comparison
```bash
# Analyze multiple versions
python run_full_analysis.py 2.0.0.b242
python run_full_analysis.py 2.1.0.b300

# Compare reports in ocr_results/
```

### Scenario 3: Development Workflow
```bash
# Check available versions
python run_full_analysis.py --list-versions

# Analyze latest version
python run_full_analysis.py 2.1.0.b300

# Review report with hyperlinks
# Fix issues in code
# Create new version and re-analyze
```

## 🔧 Configuration

### Azure AI Vision Setup
Update `.env` file with your credentials:
```
AZURE_AI_VISION_KEY=your_key_here
AZURE_AI_VISION_ENDPOINT=https://your_endpoint.cognitiveservices.azure.com/
```

### Version Folder Requirements
Each version folder must contain:
- `norwegian/` folder with PNG screenshots
- `english/` folder with PNG screenshots
- Optional: `prompt.md` with version-specific notes

## 📈 Analysis Results

### Latest Capabilities
- **Hyperlinked Reports**: Direct links to screenshot images
- **Version Tracking**: Clear version identification in all reports
- **Cross-Version Analysis**: Compare issues between app versions
- **Improved Accuracy**: Claude's advanced language understanding

### Report Sections
1. **Executive Summary**: Version, counts, critical issues
2. **Language Mismatches**: High-priority localization issues
3. **Screen Analysis**: Detailed screen-by-screen comparison
4. **Technical Observations**: OCR quality, confidence scores
5. **Recommendations**: Prioritized action items

## 🚦 Workflow Integration

### Development Process
1. **Version Creation**: Create new version folder with screenshots
2. **Analysis**: Run pipeline for language consistency check
3. **Review**: Use hyperlinked report to examine issues
4. **Fix**: Address high-priority localization problems
5. **Validation**: Re-run analysis to confirm fixes

### Quality Assurance
- **Automated Testing**: Integrate into CI/CD pipeline
- **Regression Testing**: Compare results across versions
- **Issue Tracking**: Use reports for bug tracking systems
- **Documentation**: Version history and improvement tracking

## 🎪 Advanced Features

### Session Management
- **Timestamped Results**: Track analysis over time
- **Version Comparison**: Easy cross-version analysis
- **Data Persistence**: All OCR data saved for re-analysis
- **Audit Trail**: Complete history of analysis sessions

### Extensibility
- **Plugin Architecture**: Easy to add new analysis types
- **Custom Reports**: Modify Claude prompts for specific needs
- **Integration Ready**: JSON outputs for tool integration
- **Scalable**: Handles multiple versions and large screenshot sets

This multi-version system provides a robust foundation for ongoing mobile app localization quality assurance across development cycles.