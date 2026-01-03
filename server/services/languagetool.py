"""
LanguageTool Service for Local Writing Assistant

Provides offline grammar, style, and spelling checking using LanguageTool.
Requires Java JDK 17+ to be installed on the system.
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

import language_tool_python


@dataclass
class GrammarIssue:
    """Represents a grammar/spelling issue found by LanguageTool"""
    start: int
    end: int
    message: str
    replacements: List[str]
    rule_id: str
    category: Optional[str] = None
    rule_description: Optional[str] = None


class LanguageToolService:
    """Service for handling grammar checking with LanguageTool"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._tool: Optional[language_tool_python.LanguageTool] = None
        self._current_language = "en-US"
        self._is_initialized = False
        
    async def initialize(self) -> None:
        """Initialize the LanguageTool service"""
        try:
            self.logger.info("Initializing LanguageTool service...")
            
            # Check if Java is available
            if not await self._check_java_availability():
                raise RuntimeError("Java is not available. LanguageTool requires Java JDK 17+")
            
            # Initialize LanguageTool with default language
            default_language = os.getenv("LT_LANGUAGE", "en-US")
            await self._create_language_tool(default_language)
            
            self._is_initialized = True
            self.logger.info(f"✅ LanguageTool service initialized successfully with language: {self._current_language}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize LanguageTool: {e}")
            self.logger.warning("LanguageTool will not be available for grammar checking")
            # Don't re-raise the exception - let the service start without LanguageTool
            self._is_initialized = False
    
    async def _check_java_availability(self) -> bool:
        """Check if Java is available on the system"""
        try:
            import subprocess
            
            # Try async subprocess first
            try:
                result = await asyncio.create_subprocess_exec(
                    "java", "-version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0:
                    # Java outputs version info to stderr, try both stdout and stderr
                    version_output = ""
                    if stderr:
                        try:
                            version_output = stderr.decode('utf-8', errors='ignore')
                        except:
                            version_output = stderr.decode('cp1252', errors='ignore')  # Windows encoding
                    if not version_output and stdout:
                        try:
                            version_output = stdout.decode('utf-8', errors='ignore')
                        except:
                            version_output = stdout.decode('cp1252', errors='ignore')
                    
                    if version_output and ('java' in version_output.lower() or 'openjdk' in version_output.lower()):
                        version_line = version_output.strip().split('\n')[0]
                        self.logger.info(f"Java detected: {version_line}")
                        return True
                    
            except Exception as async_error:
                self.logger.debug(f"Async subprocess failed: {async_error}, trying sync fallback")
                
                # Fallback to synchronous subprocess
                result = subprocess.run(
                    ["java", "-version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    # Check both stdout and stderr
                    version_output = result.stderr or result.stdout
                    if version_output and ('java' in version_output.lower() or 'openjdk' in version_output.lower()):
                        version_line = version_output.strip().split('\n')[0]
                        self.logger.info(f"Java detected (sync): {version_line}")
                        return True
            
            self.logger.error("Java not found or not working properly")
            return False
                
        except Exception as e:
            self.logger.error(f"Failed to check Java availability: {e}")
            return False
    
    async def _create_language_tool(self, language: str) -> None:
        """Create a new LanguageTool instance"""
        try:
            # Run the blocking LanguageTool creation in a thread pool
            loop = asyncio.get_event_loop()
            
            # Try multiple approaches to initialize LanguageTool
            def create_tool():
                attempts = [
                    # Attempt 1: Simple initialization
                    lambda: language_tool_python.LanguageTool(language=language),
                    # Attempt 2: With basic config
                    lambda: language_tool_python.LanguageTool(
                        language=language,
                        config={'maxSpellingSuggestions': 3}
                    ),
                    # Attempt 3: English only fallback
                    lambda: language_tool_python.LanguageTool(language='en'),
                ]
                
                last_error = None
                for i, attempt in enumerate(attempts, 1):
                    try:
                        self.logger.info(f"LanguageTool initialization attempt {i}/3 for language {language}")
                        tool = attempt()
                        self.logger.info(f"✅ LanguageTool successfully created with attempt {i}")
                        return tool
                    except Exception as e:
                        last_error = e
                        self.logger.warning(f"❌ Attempt {i} failed: {e}")
                        # Add delay between attempts
                        import time
                        time.sleep(1)
                        continue
                
                # If all attempts failed, try to manually clear cache and retry once
                self.logger.info("All standard attempts failed, trying cache cleanup...")
                try:
                    import shutil
                    import os
                    cache_dir = os.path.expanduser('~/.cache/language_tool_python')
                    if os.path.exists(cache_dir):
                        shutil.rmtree(cache_dir)
                        self.logger.info("Cleared LanguageTool cache, retrying...")
                        return language_tool_python.LanguageTool(language='en')
                except Exception as cleanup_error:
                    self.logger.warning(f"Cache cleanup also failed: {cleanup_error}")
                
                raise RuntimeError(f"All LanguageTool initialization attempts failed. Last error: {last_error}")
            
            self._tool = await loop.run_in_executor(None, create_tool)
            self._current_language = language
            self.logger.info(f"LanguageTool created for language: {language}")
            
        except Exception as e:
            self.logger.error(f"Failed to create LanguageTool for language {language}: {e}")
            raise
    
    async def check_text(self, text: str, language: str = None) -> List[GrammarIssue]:
        """
        Check text for grammar, style, and spelling issues
        
        Args:
            text: Text to check
            language: Language code (e.g., 'en-US', 'en-GB'). If None, uses current language.
            
        Returns:
            List of GrammarIssue objects
        """
        if not self._is_initialized:
            raise RuntimeError("LanguageTool service not initialized")
        
        # Switch language if needed
        if language and language != self._current_language:
            await self._create_language_tool(language)
        
        try:
            # Run the blocking check in a thread pool
            loop = asyncio.get_event_loop()
            matches = await loop.run_in_executor(
                None,
                self._tool.check,
                text
            )
            
            # Convert matches to our GrammarIssue format
            issues = []
            for match in matches:
                issue = GrammarIssue(
                    start=match.offset,
                    end=match.offset + match.errorLength,
                    message=match.message,
                    replacements=match.replacements[:3],  # Limit to top 3 suggestions
                    rule_id=match.ruleId,
                    category=match.category,
                    rule_description=match.rule.description if hasattr(match, 'rule') and match.rule else None
                )
                issues.append(issue)
            
            self.logger.debug(f"Found {len(issues)} issues in text of length {len(text)}")
            return issues
            
        except Exception as e:
            self.logger.error(f"Failed to check text: {e}")
            raise
    
    async def check_sentence(self, sentence: str, language: str = None) -> List[GrammarIssue]:
        """
        Check a single sentence for issues
        Optimized for real-time checking with debouncing
        """
        # Skip very short texts
        if len(sentence.strip()) < 3:
            return []
        
        return await self.check_text(sentence, language)
    
    async def get_languages(self) -> List[str]:
        """Get list of supported languages"""
        if not self._tool:
            return ["en-US", "en-GB"]  # Default fallback
        
        try:
            # This is a simplified list of commonly used languages
            # LanguageTool supports many more languages
            return [
                "en-US",  # American English
                "en-GB",  # British English
                "en-CA",  # Canadian English
                "en-AU",  # Australian English
                "de-DE",  # German
                "fr-FR",  # French
                "es-ES",  # Spanish
                "pt-BR",  # Portuguese (Brazil)
                "it-IT",  # Italian
                "nl-NL",  # Dutch
            ]
        except Exception as e:
            self.logger.error(f"Failed to get supported languages: {e}")
            return ["en-US", "en-GB"]
    
    async def health_check(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if the LanguageTool service is healthy
        
        Returns:
            Tuple of (is_healthy: bool, details: dict)
        """
        details = {
            "initialized": self._is_initialized,
            "current_language": self._current_language,
            "java_available": False,
            "tool_available": self._tool is not None
        }
        
        try:
            # Check Java availability
            details["java_available"] = await self._check_java_availability()
            
            if not details["java_available"]:
                return False, details
            
            if not self._is_initialized or not self._tool:
                return False, details
            
            # Test with a simple sentence
            test_issues = await self.check_text("This is a test sentance with a spelling error.")
            details["test_issues_found"] = len(test_issues)
            details["test_passed"] = len(test_issues) > 0  # Should find "sentance" -> "sentence"
            
            is_healthy = details["test_passed"]
            return is_healthy, details
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            details["error"] = str(e)
            return False, details
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        if self._tool:
            try:
                # Close LanguageTool in a thread pool since it's blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._tool.close)
                self.logger.info("LanguageTool service closed")
            except Exception as e:
                self.logger.error(f"Error closing LanguageTool: {e}")
            finally:
                self._tool = None
                self._is_initialized = False
