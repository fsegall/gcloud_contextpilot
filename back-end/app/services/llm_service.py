"""
LLM Service - Abstraction for multiple LLM providers

Supports:
- Google Gemini (primary, GCP-native)
- OpenAI (fallback)
- Mock (testing)
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    GEMINI = "gemini"
    OPENAI = "openai"
    MOCK = "mock"


class LLMService(ABC):
    """Abstract base class for LLM services"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            **kwargs: Provider-specific options (temperature, max_tokens, etc.)
        
        Returns:
            Generated text
        """
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Chat completion with message history.
        
        Args:
            messages: List of {"role": "user|assistant", "content": "..."}
            **kwargs: Provider-specific options
        
        Returns:
            Assistant response
        """
        pass


class GeminiService(LLMService):
    """Google Gemini implementation"""
    
    def __init__(self, model: str = "gemini-2.0-flash"):
        """
        Initialize Gemini service.
        
        Args:
            model: Gemini model name (flash, pro, ultra)
        """
        try:
            import google.generativeai as genai
            
            # Configure Gemini
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not set")
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model)
            self.model_name = model
            
            logger.info(f"[GeminiService] Initialized with model: {model}")
        except ImportError:
            logger.error("[GeminiService] google-generativeai not installed")
            raise
        except Exception as e:
            logger.error(f"[GeminiService] Initialization failed: {e}")
            raise
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Gemini"""
        try:
            temperature = kwargs.get('temperature', 0.7)
            max_tokens = kwargs.get('max_tokens', 2048)
            
            # Configure generation
            generation_config = {
                'temperature': temperature,
                'max_output_tokens': max_tokens,
            }
            
            # Generate
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Extract text
            text = response.text
            
            logger.debug(f"[GeminiService] Generated {len(text)} chars")
            return text
            
        except Exception as e:
            logger.error(f"[GeminiService] Generation failed: {e}")
            raise
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat using Gemini (converts messages to prompt)"""
        # Gemini doesn't have native chat API like OpenAI
        # Convert messages to single prompt
        prompt = self._format_messages(messages)
        return await self.generate(prompt, **kwargs)
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to Gemini prompt format"""
        formatted = []
        for msg in messages:
            role = msg['role']
            content = msg['content']
            
            if role == 'system':
                formatted.append(f"Instructions: {content}\n")
            elif role == 'user':
                formatted.append(f"User: {content}\n")
            elif role == 'assistant':
                formatted.append(f"Assistant: {content}\n")
        
        return '\n'.join(formatted)


class OpenAIService(LLMService):
    """OpenAI implementation (fallback)"""
    
    def __init__(self, model: str = "gpt-4-turbo"):
        """
        Initialize OpenAI service.
        
        Args:
            model: OpenAI model name
        """
        try:
            from openai import OpenAI
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            
            self.client = OpenAI(api_key=api_key)
            self.model_name = model
            
            logger.info(f"[OpenAIService] Initialized with model: {model}")
        except ImportError:
            logger.error("[OpenAIService] openai package not installed")
            raise
        except Exception as e:
            logger.error(f"[OpenAIService] Initialization failed: {e}")
            raise
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI"""
        try:
            temperature = kwargs.get('temperature', 0.7)
            max_tokens = kwargs.get('max_tokens', 2048)
            
            response = self.client.chat.completions.create(
                model=kwargs.get('model', self.model_name),
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            text = response.choices[0].message.content
            logger.debug(f"[OpenAIService] Generated {len(text)} chars")
            return text
            
        except Exception as e:
            logger.error(f"[OpenAIService] Generation failed: {e}")
            raise
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat using OpenAI"""
        try:
            temperature = kwargs.get('temperature', 0.7)
            max_tokens = kwargs.get('max_tokens', 2048)
            
            response = self.client.chat.completions.create(
                model=kwargs.get('model', self.model_name),
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            text = response.choices[0].message.content
            return text
            
        except Exception as e:
            logger.error(f"[OpenAIService] Chat failed: {e}")
            raise


class MockLLMService(LLMService):
    """Mock LLM for testing"""
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Return mock response"""
        return f"[MOCK] Generated response for prompt length: {len(prompt)}"
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Return mock chat response"""
        return f"[MOCK] Chat response for {len(messages)} messages"


# Global LLM service instance
_llm_service: Optional[LLMService] = None


def get_llm_service(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    force_recreate: bool = False
) -> LLMService:
    """
    Get or create LLM service instance.
    
    Args:
        provider: LLM provider (gemini, openai, mock). Auto-detects if None.
        model: Model name (optional)
        force_recreate: Force recreation of service
    
    Returns:
        LLM service instance
    """
    global _llm_service
    
    if _llm_service is not None and not force_recreate:
        return _llm_service
    
    # Auto-detect provider
    if provider is None:
        provider = os.getenv('LLM_PROVIDER', 'gemini').lower()
    
    logger.info(f"[LLMService] Creating service: {provider}")
    
    try:
        if provider == LLMProvider.GEMINI.value:
            model = model or os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
            _llm_service = GeminiService(model=model)
            
        elif provider == LLMProvider.OPENAI.value:
            model = model or os.getenv('OPENAI_MODEL', 'gpt-4-turbo')
            _llm_service = OpenAIService(model=model)
            
        elif provider == LLMProvider.MOCK.value:
            _llm_service = MockLLMService()
            logger.warning("[LLMService] Using MOCK service (testing mode)")
            
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
        
        logger.info(f"[LLMService] Successfully created {provider} service")
        return _llm_service
        
    except Exception as e:
        logger.error(f"[LLMService] Failed to create {provider} service: {e}")
        
        # Fallback to mock
        logger.warning("[LLMService] Falling back to MOCK service")
        _llm_service = MockLLMService()
        return _llm_service


def reset_llm_service():
    """Reset global LLM service (for testing)"""
    global _llm_service
    _llm_service = None


# Convenience functions
async def generate_text(prompt: str, **kwargs) -> str:
    """Generate text using configured LLM service"""
    llm = get_llm_service()
    return await llm.generate(prompt, **kwargs)


async def chat_completion(messages: List[Dict[str, str]], **kwargs) -> str:
    """Chat completion using configured LLM service"""
    llm = get_llm_service()
    return await llm.chat(messages, **kwargs)

