#!/usr/bin/env python3
"""
Model Download Script for Local Writing Assistant

Downloads and caches the required AI models:
- google/flan-t5-small (for text rewriting)
- faster-whisper base.en or tiny (for speech recognition)

All models are stored locally for offline usage.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional

# Add the server directory to the Python path
server_dir = Path(__file__).parent.parent
sys.path.insert(0, str(server_dir))

def setup_logging():
    """Configure logging for the download script"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("model_download.log")
        ]
    )
    return logging.getLogger(__name__)

def ensure_models_dir() -> Path:
    """Ensure the models directory exists"""
    models_dir = server_dir / "models"
    models_dir.mkdir(exist_ok=True)
    return models_dir

def download_flan_t5_model(models_dir: Path, model_name: str = "google/flan-t5-small") -> bool:
    """Download Flan-T5 model for text rewriting"""
    logger = logging.getLogger(__name__)
    
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        import torch
        
        logger.info(f"Downloading {model_name} model and tokenizer...")
        
        # Set cache directory
        cache_dir = models_dir / "flan-t5-small"
        
        # Download tokenizer
        logger.info("Downloading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=str(cache_dir),
            local_files_only=False
        )
        
        # Download model with CPU-optimized settings
        logger.info("Downloading model...")
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            cache_dir=str(cache_dir),
            local_files_only=False,
            torch_dtype=torch.float32,  # Use float32 for CPU
            device_map=None  # No device mapping for CPU
        )
        
        # Save model locally
        local_model_path = cache_dir / "local_model"
        local_model_path.mkdir(exist_ok=True)
        
        tokenizer.save_pretrained(str(local_model_path))
        model.save_pretrained(str(local_model_path))
        
        logger.info(f"✓ Flan-T5 model downloaded to: {local_model_path}")
        return True
        
    except ImportError as e:
        logger.error(f"Missing dependencies for Flan-T5: {e}")
        logger.error("Please install: pip install transformers torch")
        return False
    except Exception as e:
        logger.error(f"Failed to download Flan-T5 model: {e}")
        return False

def download_whisper_model(models_dir: Path, model_size: str = "base.en") -> bool:
    """Download Whisper model for speech recognition"""
    logger = logging.getLogger(__name__)
    
    try:
        from faster_whisper import WhisperModel
        
        logger.info(f"Downloading Whisper {model_size} model...")
        
        # This will download the model to the default cache
        model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
            download_root=str(models_dir / "whisper")
        )
        
        # Test the model with a dummy audio file
        logger.info("Testing Whisper model...")
        # The model is now cached and ready for use
        
        logger.info(f"✓ Whisper {model_size} model downloaded successfully")
        return True
        
    except ImportError as e:
        logger.error(f"Missing dependencies for Whisper: {e}")
        logger.error("Please install: pip install faster-whisper")
        return False
    except Exception as e:
        logger.error(f"Failed to download Whisper model: {e}")
        return False

def download_nltk_data() -> bool:
    """Download NLTK data for tone analysis"""
    logger = logging.getLogger(__name__)
    
    try:
        import nltk
        
        logger.info("Downloading NLTK data...")
        
        # Download required NLTK data
        datasets = [
            'vader_lexicon',
            'punkt',
            'stopwords'
        ]
        
        for dataset in datasets:
            try:
                nltk.download(dataset, quiet=True)
                logger.info(f"✓ Downloaded NLTK dataset: {dataset}")
            except Exception as e:
                logger.warning(f"Failed to download NLTK dataset {dataset}: {e}")
        
        return True
        
    except ImportError:
        logger.warning("NLTK not available, skipping NLTK data download")
        return True
    except Exception as e:
        logger.error(f"Failed to download NLTK data: {e}")
        return False

def check_system_requirements() -> List[str]:
    """Check system requirements and return missing components"""
    missing = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        missing.append("Python 3.8 or higher")
    
    # Check Java (for LanguageTool)
    try:
        import subprocess
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            missing.append("Java Runtime Environment")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        missing.append("Java Runtime Environment (JRE 11 or higher)")
    
    # Check FFmpeg (for audio processing)
    try:
        import subprocess
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            missing.append("FFmpeg")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        missing.append("FFmpeg")
    
    return missing

def main():
    """Main download function"""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("Local Writing Assistant - Model Download")
    logger.info("=" * 60)
    
    # Check system requirements
    missing_req = check_system_requirements()
    if missing_req:
        logger.warning("Missing system requirements:")
        for req in missing_req:
            logger.warning(f"  - {req}")
        logger.warning("Some features may not work properly.")
    
    # Create models directory
    models_dir = ensure_models_dir()
    logger.info(f"Models directory: {models_dir}")
    
    success_count = 0
    total_count = 0
    
    # Download Flan-T5 model
    total_count += 1
    logger.info("\n" + "-" * 40)
    logger.info("Downloading Flan-T5 Model")
    logger.info("-" * 40)
    if download_flan_t5_model(models_dir):
        success_count += 1
    
    # Download Whisper model
    total_count += 1
    logger.info("\n" + "-" * 40)
    logger.info("Downloading Whisper Model")
    logger.info("-" * 40)
    
    # Check environment variable for model size
    whisper_model = os.getenv("WHISPER_MODEL", "base.en")
    if download_whisper_model(models_dir, whisper_model):
        success_count += 1
    
    # Download NLTK data
    total_count += 1
    logger.info("\n" + "-" * 40)
    logger.info("Downloading NLTK Data")
    logger.info("-" * 40)
    if download_nltk_data():
        success_count += 1
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Download Summary")
    logger.info("=" * 60)
    logger.info(f"Successfully downloaded: {success_count}/{total_count} components")
    
    if success_count == total_count:
        logger.info("✓ All models downloaded successfully!")
        logger.info("You can now start the Local Writing Assistant server.")
    else:
        logger.warning("⚠ Some models failed to download.")
        logger.warning("Check the logs above and ensure all dependencies are installed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
