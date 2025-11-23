# Body Diagnostics Agent

An AI-powered system that automates the creation of professional diagnostic reports from client consultation sessions. Transform audio recordings, transcripts, or text input into comprehensive, structured diagnostic documents using Google's Agent Development Kit (ADK) and Gemini AI.

## 🎯 Overview

This agent eliminates manual work by automating the complete workflow from raw consultation data to professional diagnostic reports. It saves trainers 40-60 minutes of manual work per consultation by:

- **Transcribing** audio files using Whisper STT
- **Extracting** comprehensive client information (100+ facts)
- **Planning** document structure based on diagnostic templates
- **Generating** professional .docx reports with tables, lists, and structured content

## ✨ Features

- 🎤 **Speech-to-Text**: Automatic transcription of audio files using OpenAI Whisper
- 📊 **Structured Data Extraction**: Extracts comprehensive client portraits covering:
  - Personal information and demographics
  - Lifestyle and daily routines
  - Medical history and injuries
  - Physical assessment findings
  - Sports and training history
  - Emotional and psychological aspects
- 📝 **Document Generation**: Creates professional .docx reports with:
  - Structured tables with headers
  - Ordered and unordered lists
  - Blockquotes for important observations
  - Multi-language support (Ukrainian, Russian, English)
- 🎨 **Interactive CLI**: Beautiful terminal interface with "Matrix" style output
- 🔧 **Customizable Structure**: Define custom document structure via prompts
- 🌍 **Language Detection**: Automatic language detection from transcript content

## 📋 Requirements

- Python 3.10+
- Google ADK API key (`GEMINI_API_KEY` or `GOOGLE_API_KEY`)
- FFmpeg (for audio processing with Whisper)

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd diagnostic_agent
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   
   **Important**: Make sure you're using the correct Python environment. If using `python3` directly:
   ```bash
   python3 -m pip install -r requirements.txt
   ```

4. **Verify installation**:
   ```bash
   python3 -c "import google.adk; print('✓ google-adk installed')"
   ```
   
   If you see an error, ensure you're installing in the correct Python environment.

**Note**: The `run_diagnostic.command` script automatically activates a virtual environment if `venv` or `.venv` directory exists in the project root.

4. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```bash
   # Use only ONE of these options:
   
   # Option 1: Google AI API (recommended)
   GEMINI_API_KEY=your_api_key_here
   
   # Option 2: Vertex AI (alternative)
   GOOGLE_CLOUD_PROJECT=your_project_id
   GOOGLE_CLOUD_LOCATION=us-central1
   ```

   **Note**: If both `GOOGLE_API_KEY` and `GEMINI_API_KEY` are set, the system will use `GOOGLE_API_KEY` and display a warning. Use only one API key to avoid confusion.

## 🎮 Usage

### Interactive CLI

Run the interactive CLI script:

```bash
python3 run_diagnostic.py
```

Or on macOS, double-click `run_diagnostic.command` to launch in Terminal.

The CLI will guide you through:
1. **Diagnostic Identifier**: Enter a unique ID or auto-generate one
2. **Input Type**: Choose audio file or text transcript
3. **File Selection**: Select audio/transcript file interactively
4. **Document Structure Prompt** (optional): Define custom document structure
5. **Additional Instructions** (optional): Provide extra guidance for the agent
6. **Processing**: Automatic transcription (if audio) and report generation

### Example Structure Prompt

When prompted for document structure, you can enter a short paragraph like:

```
Create a diagnostic report with sections: Personal data and anamnesis, Medical history, Sports history, Postural assessment, Visual assessment, Respiratory assessment. Use tables extensively for structured data with headers: Parameter/Data, Disease/Injury/When/Duration/Connection, Question/Observation/Conclusion, Category/Description, Test/Result/Conclusion.
```

### Output

Generated reports are saved to:
```
diagnostics/{identifier}/
├── transcript.txt              # Original transcript
├── diagnostic_report_{identifier}.docx  # Generated report
└── state.json                 # Agent state (for debugging)
```

## 🏗️ Project Structure

```
diagnostic_agent/
├── diagnostic_agent/          # Main package
│   ├── agent.py               # Root agent definition
│   ├── instructions.md        # Agent instructions and workflow
│   ├── sub_agents/
│   │   ├── client_portrait_agent/  # Extracts comprehensive client info
│   │   └── doc_structure_planner/   # Plans document structure
│   └── tools/
│       ├── docx_creator.py    # .docx document generator
│       └── memory.py           # Memory utilities
├── diagnostics/               # Output directory (gitignored)
├── run_diagnostic.py          # Interactive CLI script
├── run_diagnostic.command     # macOS launcher
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🔧 Architecture

The system uses a multi-agent architecture:

1. **Root Agent** (`root_agent`): Orchestrates the workflow and coordinates sub-agents
2. **Client Portrait Agent** (`client_portrait_agent`): Extracts comprehensive client information (aims for 100+ facts)
3. **Document Structure Planner** (`doc_structure_planner_agent`): Plans the document structure based on extracted data
4. **Document Creator Tool** (`create_docx_from_structure`): Generates .docx files from structured data

### Document Elements

The system supports various document element types:

- **Tables**: Structured data with headers (prefer `table_data` array over markdown)
- **Lists**: Ordered (`ol`) and unordered (`ul`) lists with `list_items` array
- **Quotes**: Blockquotes for important observations (`quote_text`)
- **Paragraphs**: Regular text content
- **Headings**: H1-H6 headings

## 📝 Document Structure Model

The document structure follows a hierarchical model:

```python
DocStructure
└── sections: List[Section]
    ├── title: str
    ├── description: Optional[str]
    ├── conclusion: Optional[str]
    ├── elements: List[DocElement]  # Preferred
    └── subsections: Optional[List[Subsection]]  # For complex hierarchies
```

## 🌐 Language Support

The system automatically detects document language from transcript content:
- **Ukrainian**: Detected by characters (і, ї, є, ґ)
- **Russian**: Detected by characters (ы, э, ъ)
- **English**: Default fallback

Language is used for document generation and can be manually specified.

## ⚙️ Configuration

### Environment Variables

- `GEMINI_API_KEY`: Google AI API key (recommended)
- `GOOGLE_API_KEY`: Alternative Google API key
- `GOOGLE_CLOUD_PROJECT`: Vertex AI project ID (alternative to API key)
- `GOOGLE_CLOUD_LOCATION`: Vertex AI location (default: us-central1)

### Model Configuration

The system uses `gemini-2.5-flash` by default. You can modify this in:
- `diagnostic_agent/agent.py` (root agent)
- `diagnostic_agent/sub_agents/*/agent.py` (sub-agents)

## 🐛 Troubleshooting

### Common Issues

1. **`ModuleNotFoundError: No module named 'google'`**
   - **Solution**: Install dependencies using the correct Python interpreter:
     ```bash
     python3 -m pip install -r requirements.txt
     ```
   - If using a virtual environment, make sure it's activated:
     ```bash
     source venv/bin/activate  # On macOS/Linux
     # or
     venv\Scripts\activate  # On Windows
     ```
   - Verify installation:
     ```bash
     python3 -c "import google.adk; print('✓ Dependencies installed correctly')"
     ```
   - If the error persists, check which Python is being used:
     ```bash
     which python3  # macOS/Linux
     # or
     where python3  # Windows
     ```

2. **"No API credentials found"**
   - Ensure `.env` file exists with `GEMINI_API_KEY` or `GOOGLE_CLOUD_PROJECT`
   - Check that environment variables are loaded correctly
   - Verify `.env` file is in the project root directory

3. **"Whisper STT is not available"**
   - Install Whisper: `pip install openai-whisper` or `python3 -m pip install openai-whisper`
   - Ensure FFmpeg is installed for audio processing:
     ```bash
     # macOS
     brew install ffmpeg
     
     # Ubuntu/Debian
     sudo apt-get install ffmpeg
     
     # Windows
     # Download from https://ffmpeg.org/download.html
     ```

4. **"Both GOOGLE_API_KEY and GEMINI_API_KEY are set"**
   - Remove one of the keys from `.env` to avoid confusion
   - The system will use `GOOGLE_API_KEY` if both are present

5. **Document generation fails**
   - Check that `doc_structure` exists in agent state
   - Verify that `doc_structure_planner_agent` completed successfully
   - Review `state.json` in output directory for debugging

## 📚 Dependencies

- `google-adk`: Google Agent Development Kit
- `python-docx`: Document generation
- `openai-whisper`: Speech-to-Text
- `python-dotenv`: Environment variable management

See `requirements.txt` for complete list.

## 🔒 Privacy & Security

- All processing happens locally (except API calls to Google AI)
- Transcripts and generated documents are stored in `diagnostics/` directory
- Audio files are processed locally using Whisper
- API keys should never be committed to version control

## 📄 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]

## 📧 Support

[Add support/contact information here]

---

**Note**: This project uses Google's Agent Development Kit (ADK) and requires valid API credentials. Make sure to follow Google's usage policies and rate limits.