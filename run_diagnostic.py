#!/usr/bin/env python3
"""
Interactive CLI script for running body diagnostics agent.
"""

import sys
import uuid
import asyncio
import json
import os
import warnings
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, try to load from environment directly
    pass

# Suppress warnings from Google ADK about non-text parts and API keys
# These are informational and don't affect functionality
warnings.filterwarnings('ignore', message='.*non-text parts.*')
warnings.filterwarnings('ignore', message='.*Both GOOGLE_API_KEY and GEMINI_API_KEY.*')
warnings.filterwarnings('ignore', message='.*Default value is not supported.*')

# Suppress logging from google libraries
logging.getLogger('google').setLevel(logging.ERROR)
logging.getLogger('google.genai').setLevel(logging.ERROR)
logging.getLogger('google.adk').setLevel(logging.ERROR)

# ANSI color codes for matrix-style terminal
class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Matrix green colors
    GREEN = '\033[92m'
    BRIGHT_GREEN = '\033[92m'
    DARK_GREEN = '\033[32m'
    CYAN = '\033[96m'
    
    # Accent colors
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    RED = '\033[91m'
    
    # Background
    BG_BLACK = '\033[40m'


def print_matrix_header(title: str, width: int = 70):
    """Print a matrix-style header."""
    border = f"{Colors.GREEN}{'═' * width}{Colors.RESET}"
    title_line = f"{Colors.GREEN}║{Colors.RESET} {Colors.BRIGHT_GREEN}{Colors.BOLD}{title.center(width - 4)}{Colors.RESET} {Colors.GREEN}║{Colors.RESET}"
    print(f"\n{Colors.GREEN}╔{border[3:-3]}╗{Colors.RESET}")
    print(title_line)
    print(f"{Colors.GREEN}╚{'═' * width}╝{Colors.RESET}\n")


def print_section_header(title: str, step: int = None):
    """Print a section header."""
    if step:
        header = f"{Colors.CYAN}{Colors.BOLD}Step {step}: {title}{Colors.RESET}"
    else:
        header = f"{Colors.CYAN}{Colors.BOLD}{title}{Colors.RESET}"
    separator = f"{Colors.DARK_GREEN}{'─' * 60}{Colors.RESET}"
    print(f"\n{header}")
    print(f"{separator}")


def print_success(message: str):
    """Print a success message."""
    print(f"{Colors.BRIGHT_GREEN}✓{Colors.RESET} {Colors.GREEN}{message}{Colors.RESET}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {Colors.YELLOW}{message}{Colors.RESET}")


def print_error(message: str):
    """Print an error message."""
    print(f"{Colors.RED}❌{Colors.RESET} {Colors.RED}{message}{Colors.RESET}")


def print_info(message: str):
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {Colors.CYAN}{message}{Colors.RESET}")


def print_progress(message: str):
    """Print a progress message."""
    print(f"{Colors.MAGENTA}🔄{Colors.RESET} {Colors.CYAN}{message}{Colors.RESET}")


def print_block(content: str, title: str = None, color: str = Colors.GREEN):
    """Print content in a bordered block."""
    lines = content.split('\n')
    max_width = max(len(line) for line in lines) if lines else 0
    max_width = max(max_width, len(title) + 2 if title else 0, 50)
    
    border_top = f"{color}╔{'═' * (max_width + 2)}╗{Colors.RESET}"
    border_bottom = f"{color}╚{'═' * (max_width + 2)}╝{Colors.RESET}"
    border_side = f"{color}║{Colors.RESET}"
    
    print(f"\n{border_top}")
    if title:
        print(f"{border_side} {Colors.BRIGHT_GREEN}{Colors.BOLD}{title.center(max_width)}{Colors.RESET} {border_side}")
        print(f"{color}╠{'═' * (max_width + 2)}╣{Colors.RESET}")
    for line in lines:
        print(f"{border_side} {line.ljust(max_width)} {border_side}")
    print(f"{border_bottom}\n")


# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from diagnostic_agent.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Try to import whisper for STT
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠ Warning: whisper library not installed. Install it with: pip install openai-whisper")


def generate_identifier() -> str:
    """Generate a unique identifier for the diagnostic session."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{timestamp}_{unique_id}"


def detect_language(text: str) -> str:
    """Detect language from text."""
    ukrainian_chars = set('іїєґІЇЄҐ')
    russian_chars = set('ыэъЫЭЪ')
    
    text_chars = set(text.lower())
    
    uk_count = len(text_chars & ukrainian_chars)
    ru_count = len(text_chars & russian_chars)
    
    if uk_count > ru_count and uk_count > 0:
        return 'uk'
    elif ru_count > uk_count and ru_count > 0:
        return 'ru'
    else:
        return 'uk'  # default


def read_transcript_file(file_path: str) -> str:
    """Read transcript from file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def transcribe_audio_with_whisper(audio_path: str, model_size: str = "base") -> str:
    """Transcribe audio file using Whisper STT."""
    if not WHISPER_AVAILABLE:
        raise ImportError("Whisper library is not installed. Install it with: pip install openai-whisper")
    
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    print_progress(f"Loading Whisper model ({model_size})...")
    print_info("This may take a moment on first run")
    
    try:
        # Load Whisper model
        model = whisper.load_model(model_size)
        
        print_success(f"Model loaded. Transcribing audio: {Colors.BOLD}{path.name}{Colors.RESET}")
        print_info("This may take a while depending on audio length...")
        
        # Transcribe audio
        result = model.transcribe(str(path.absolute()), language=None)  # Auto-detect language
        
        transcript = result["text"].strip()
        
        # Show detected language if available
        if "language" in result:
            lang = result["language"]
            lang_names = {
                "uk": "Ukrainian",
                "ru": "Russian", 
                "en": "English"
            }
            lang_name = lang_names.get(lang, lang)
            print_success(f"Detected audio language: {Colors.BOLD}{lang_name}{Colors.RESET} ({lang})")
        
        print_success(f"Transcription complete! {Colors.DIM}({len(transcript)} characters){Colors.RESET}")
        
        return transcript
        
    except Exception as e:
        raise RuntimeError(f"Error transcribing audio with Whisper: {e}")


def read_audio_file(file_path: str) -> str:
    """Read audio file and transcribe it using Whisper."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not WHISPER_AVAILABLE:
        raise ImportError(
            "Whisper library is not installed.\n"
            "Install it with: pip install openai-whisper\n"
            "Or use a transcript file instead (option 2)."
        )
    
    # Transcribe audio file
    return transcribe_audio_with_whisper(str(path.absolute()))


def find_files_in_directory(directory: Path, extensions: list, max_depth: int = 3) -> list[Path]:
    """Find files with given extensions in directory and subdirectories."""
    found_files = []
    extensions_lower = [ext.lower() for ext in extensions]
    
    # Directories to exclude
    exclude_dirs = {'.git', '__pycache__', '.pytest_cache', 'venv', 'env', '.venv', 'node_modules', 'diagnostics'}
    
    # Search recursively
    for file_path in directory.rglob("*"):
        # Skip excluded directories
        if any(excluded in file_path.parts for excluded in exclude_dirs):
            continue
        
        # Check depth limit
        relative_path = file_path.relative_to(directory)
        if len(relative_path.parts) > max_depth + 1:  # +1 because parts includes filename
            continue
        
        if file_path.is_file():
            # Check if file extension matches
            file_ext = file_path.suffix.lower()
            if file_ext in extensions_lower and file_path not in found_files:
                found_files.append(file_path)
    
    return sorted(found_files)


def select_file_interactive(directory: Path, file_type: str, extensions: list) -> Optional[Path]:
    """Interactive file selection from directory."""
    print_progress(f"Searching for {file_type} files...")
    
    # Find files
    found_files = find_files_in_directory(directory, extensions)
    
    if not found_files:
        print_warning(f"No {file_type} files found in the project directory.")
        return None
    
    # Display files in a block
    file_list = '\n'.join([f"{i}. {file_path.relative_to(directory)}" for i, file_path in enumerate(found_files, 1)])
    print_block(
        file_list,
        title=f"Found {len(found_files)} {file_type} file(s)",
        color=Colors.CYAN
    )
    print(f"{Colors.DARK_GREEN}  0.{Colors.RESET} Enter path manually")
    
    # Get user selection
    while True:
        try:
            choice = input(f"\n{Colors.GREEN}Select file{Colors.RESET} {Colors.DIM}(1-{len(found_files)}) or 0 for manual entry{Colors.RESET}: ").strip()
            
            if choice == "0":
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(found_files):
                selected_file = found_files[choice_num - 1]
                print_success(f"Selected: {Colors.BOLD}{selected_file.relative_to(directory)}{Colors.RESET}")
                return selected_file
            else:
                print_error(f"Invalid choice. Please enter a number between 1 and {len(found_files)}, or 0.")
        except ValueError:
            print_error("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print()
            print_warning("Selection cancelled.")
            return None


def _print_event_progress(event):
    """Helper function to print event progress."""
    if hasattr(event, 'content') and event.content:
        if hasattr(event.content, 'parts'):
            # Extract only text parts, ignoring non-text parts (thought_signature, function_call, etc.)
            text_parts = []
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    text_parts.append(part.text)
            
            if text_parts:
                # Combine all text parts
                combined_text = '\n'.join(text_parts)
                # Print short status messages
                if len(combined_text) < 150 and not combined_text.startswith("```"):
                    print(f"{Colors.DARK_GREEN}   →{Colors.RESET} {Colors.GREEN}{combined_text[:100]}{Colors.RESET}")


async def run_agent(transcript: str, identifier: str, output_dir: Path, initial_message: Optional[str] = None, structure_prompt: Optional[str] = None):
    """Run the diagnostic agent with the given transcript."""
    print(f"\n{'='*60}")
    print(f"Starting diagnostic processing for: {identifier}")
    print(f"{'='*60}\n")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save transcript to output directory
    transcript_path = output_dir / "transcript.txt"
    with open(transcript_path, 'w', encoding='utf-8') as f:
        f.write(transcript)
    print(f"✓ Transcript saved to: {transcript_path}")
    
    # Detect language
    language = detect_language(transcript)
    print(f"✓ Detected language: {language}")
    
    # Prepare initial message with structure prompt if provided
    message_parts = []
    
    if structure_prompt:
        message_parts.append(f"DOCUMENT STRUCTURE REQUIREMENTS:\n{structure_prompt}\n")
    
    if initial_message:
        message_parts.append(initial_message)
    
    message_parts.append(f"\nPlease analyze this diagnostic transcript and create a comprehensive diagnostic report following the structure requirements above:\n\n{transcript}")
    
    user_message = "\n".join(message_parts)
    
    # Set output path for document in absolute path
    output_docx = output_dir.absolute() / f"diagnostic_report_{identifier}.docx"
    
    print_section_header("Processing Pipeline")
    print_progress("Extracting client portrait...")
    print_progress("Planning document structure...")
    print_progress("Generating document...")
    print()
    
    try:
        # Create a simple state dict to pass through
        state = {
            'output_path': str(output_docx),
            'language': language
        }
        
        events = []
        
        # Use Runner to orchestrate agent execution
        # According to ADK docs: https://google.github.io/adk-docs/runtime/#runners-role-orchestrator
        # Runner acts as the central coordinator for a single user invocation
        session_service = InMemorySessionService()
        
        # Create Runner with session service
        # Runner requires either 'app' or both 'app_name' and 'agent'
        runner = Runner(
            app_name="diagnostic_agent",
            agent=root_agent,
            session_service=session_service
        )
        
        # Initialize state in session before running
        # Create a session and set initial state
        from google.genai.types import Content, Part
        
        user_id = f"user_{identifier}"
        session_id = str(uuid.uuid4())
        app_name = "diagnostic_agent"
        
        # Create session with initial state
        # Runner will handle session creation if it doesn't exist, but we can pre-create it
        session = await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            state=state
        )
        
        # Create Content object from user message
        user_content = Content(parts=[Part(text=user_message)])
        
        # Runner.run_async is the primary method for executing agent invocations
        # It receives the user query (new_message) and manages the event loop
        # The Runner will:
        # 1. Append the message to session history
        # 2. Start event generation by calling agent.run_async
        # 3. Process events and commit state changes
        # 4. Yield events upstream
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content,
            state_delta=state
        ):
            events.append(event)
            _print_event_progress(event)
            
            # State is managed by Runner through SessionService
            # Changes are committed after events are processed
        
        # Check if document was generated
        generated_path = None
        
        # Get final state from session (Runner commits state changes after events)
        final_session = await session_service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        if final_session and final_session.state:
            context_state = final_session.state
        else:
            context_state = state  # Fallback to initial state
        
        # Check state for generated document path
        if 'generated_docx' in context_state:
            generated_path = Path(context_state['generated_docx'])
        elif 'output_path' in context_state:
            generated_path = Path(context_state['output_path'])
        
        if generated_path and generated_path.exists():
            print(f"\n✓ Document generated: {generated_path}")
        else:
            # Try to find the document in output directory
            docx_files = list(output_dir.glob("*.docx"))
            if docx_files:
                print(f"\n✓ Document found: {docx_files[0]}")
            else:
                print("\n⚠ No document found. Agent may not have completed generation.")
                print("   Check the output directory for any generated files.")
        
        # Save state if available
        if context_state:
            state_path = output_dir / "state.json"
            # Convert state to JSON-serializable format
            # Handle both dict-like objects and actual dicts
            if hasattr(context_state, 'items'):
                state_dict = dict(context_state.items())
            elif isinstance(context_state, dict):
                state_dict = context_state
            else:
                state_dict = {}
            
            # Ensure all values are JSON-serializable
            serializable_dict = {}
            for key, value in state_dict.items():
                try:
                    json.dumps(value)  # Test if serializable
                    serializable_dict[key] = value
                except (TypeError, ValueError):
                    serializable_dict[key] = str(value)
            
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_dict, f, indent=2, ensure_ascii=False)
            print_success(f"State saved to: {state_path}")
        
        print_matrix_header("PROCESSING COMPLETE", 70)
        print_success(f"Results saved to: {Colors.BOLD}{output_dir}{Colors.RESET}")
        print()
        
    except Exception as e:
        print_error(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """Main interactive CLI function."""
    # Check for API credentials before starting
    # ADK uses GOOGLE_API_KEY if both GOOGLE_API_KEY and GEMINI_API_KEY are set
    api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
    google_cloud_project = os.getenv('GOOGLE_CLOUD_PROJECT')
    
    # Warn if both API keys are set (ADK will use GOOGLE_API_KEY and print a message)
    if os.getenv('GOOGLE_API_KEY') and os.getenv('GEMINI_API_KEY'):
        print_warning("Both GOOGLE_API_KEY and GEMINI_API_KEY are set. ADK will use GOOGLE_API_KEY.")
        print_info("Consider removing GEMINI_API_KEY from .env to avoid duplicate messages.")
    
    if not api_key and not google_cloud_project:
        print_error("No API credentials found!")
        print_info("Please set one of the following:")
        print_info("  - GOOGLE_API_KEY or GEMINI_API_KEY (for Google AI API)")
        print_info("  - GOOGLE_CLOUD_PROJECT (for Vertex AI)")
        print_info("\nCreate a .env file based on .env.example or set environment variables.")
        sys.exit(1)
    
    print_matrix_header("BODY DIAGNOSTICS AGENT", 70)
    print(f"{Colors.CYAN}{Colors.BOLD}Interactive Diagnostic System{Colors.RESET}\n")
    
    # Step 1: Get identifier
    print_section_header("Diagnostic Identifier", 1)
    identifier_input = input(f"{Colors.GREEN}Enter unique identifier{Colors.RESET} {Colors.DIM}(or press Enter for auto-generation){Colors.RESET}: ").strip()
    
    if identifier_input:
        identifier = identifier_input
        print_success(f"Using identifier: {Colors.BOLD}{identifier}{Colors.RESET}")
    else:
        identifier = generate_identifier()
        print_success(f"Auto-generated identifier: {Colors.BOLD}{identifier}{Colors.RESET}")
    
    # Step 2: Choose input type
    print_section_header("Input Type", 2)
    print(f"{Colors.CYAN}1.{Colors.RESET} Audio file {Colors.DIM}(requires STT){Colors.RESET}")
    print(f"{Colors.CYAN}2.{Colors.RESET} Text transcript")
    
    while True:
        choice = input(f"\n{Colors.GREEN}Select option{Colors.RESET} {Colors.DIM}(1 or 2){Colors.RESET}: ").strip()
        if choice in ['1', '2']:
            break
        print_error("Invalid choice. Please enter 1 or 2.")
    
    # Step 3: Get input file (but don't process yet)
    project_dir = Path(__file__).parent
    audio_path = None
    transcript_input = None
    is_audio = choice == '1'
    
    if is_audio:
        print_section_header("Audio File Selection", 3)
        
        if not WHISPER_AVAILABLE:
            print_warning("Whisper STT is not available.")
            print_info("Install it with: pip install openai-whisper")
            print_info("Or select option 2 to use a text transcript instead.")
            print()
            fallback = input(f"{Colors.YELLOW}Continue anyway?{Colors.RESET} {Colors.DIM}(y/n){Colors.RESET}: ").strip().lower()
            if fallback != 'y':
                print_info("Exiting...")
                sys.exit(0)
        
        # Offer file selection
        audio_extensions = ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.mp4', '.m4v', '.mov']
        selected_audio = select_file_interactive(project_dir, "audio", audio_extensions)
        
        if selected_audio:
            audio_path = str(selected_audio)
        else:
            audio_path = input(f"{Colors.GREEN}Enter path to audio file{Colors.RESET}: ").strip()
        
        print_success(f"Audio file selected: {Colors.BOLD}{Path(audio_path).name}{Colors.RESET}")
    else:
        print_section_header("Transcript Selection", 3)
        
        # Offer transcript file selection
        transcript_extensions = ['.txt']
        selected_transcript = select_file_interactive(project_dir, "transcript", transcript_extensions)
        
        if selected_transcript:
            transcript_input = str(selected_transcript)
        else:
            transcript_input = input(f"{Colors.GREEN}Enter transcript text or path to .txt file{Colors.RESET}: ").strip()
        
        print_success("Transcript source selected")
    
    # Step 4: Document structure prompt (optional)
    print_section_header("Document Structure Prompt (Optional)", 4)
    print_info("Enter a short paragraph describing the desired document structure.")
    print_info("Example: 'Create a diagnostic report with sections: Personal data and anamnesis, Medical history, Sports history, Postural assessment, Visual assessment, Respiratory assessment. Use tables extensively for structured data.'")
    print()
    structure_prompt = input(f"{Colors.GREEN}Enter structure prompt{Colors.RESET} {Colors.DIM}(or press Enter to use default){Colors.RESET}: ").strip()
    
    if not structure_prompt:
        structure_prompt = None
        print_info("Using default document structure")
    else:
        print_success("Structure prompt saved")
    
    # Step 5: Optional additional message
    print_section_header("Additional Instructions (Optional)", 5)
    additional_message = input(f"{Colors.GREEN}Enter any additional instructions for the agent{Colors.RESET} {Colors.DIM}(or press Enter to skip){Colors.RESET}: ").strip()
    
    if not additional_message:
        additional_message = None
        print_info("No additional instructions provided")
    else:
        print_success("Additional instructions saved")
    
    # Step 6: Output directory
    print_section_header("Output Configuration", 6)
    output_dir = Path("diagnostics") / identifier
    print_success(f"Output directory: {Colors.BOLD}{output_dir}{Colors.RESET}")
    
    # Step 7: Process input (transcribe if audio, read if transcript)
    print_matrix_header("CONFIGURATION COMPLETE", 70)
    print_progress("Starting processing pipeline...")
    print()
    
    transcript = None
    
    if is_audio:
        # Transcribe audio using Whisper
        print_section_header("Transcribing Audio File", 7)
        try:
            transcript = read_audio_file(audio_path)
            print_success("Audio transcribed successfully!")
            print()
        except ImportError as e:
            print_error(f"Error: {e}")
            print_warning("Falling back to manual transcript entry...")
            transcript_extensions = ['.txt']
            selected_transcript = select_file_interactive(project_dir, "transcript", transcript_extensions)
            
            if selected_transcript:
                transcript_path = str(selected_transcript)
            else:
                transcript_path = input(f"{Colors.GREEN}Enter path to transcript file{Colors.RESET}: ").strip()
            
            transcript = read_transcript_file(transcript_path)
        except (FileNotFoundError, RuntimeError) as e:
            print_error(f"Error: {e}")
            sys.exit(1)
    else:
        # Read transcript
        print_section_header("Reading Transcript", 6)
        if Path(transcript_input).exists():
            try:
                transcript = read_transcript_file(transcript_input)
                print_success("Transcript loaded from file")
                print()
            except Exception as e:
                print_error(f"Error reading file: {e}")
                sys.exit(1)
        else:
            transcript = transcript_input
            print_success("Transcript entered manually")
            print()
    
    if not transcript or len(transcript.strip()) < 10:
        print_error("Transcript is too short or empty.")
        sys.exit(1)
    
    # Step 7: Run agent
    print_matrix_header("RUNNING DIAGNOSTIC AGENT", 70)
    print()
    
    try:
        asyncio.run(run_agent(transcript, identifier, output_dir, additional_message, structure_prompt))
    except KeyboardInterrupt:
        print()
        print_warning("Process interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print()
        print_error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

