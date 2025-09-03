"""
Secure API Key Management for Multi-LLM MCP Server

Handles API key storage, encryption, and retrieval for all LLM providers.
"""

import os
import json
import logging
import keyring
from pathlib import Path
from typing import Optional, Dict
from cryptography.fernet import Fernet
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class KeyProvider(Enum):
    """Supported LLM providers"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    LLAMA = "llama"
    GROQ = "groq"
    XAI = "xai"


@dataclass
class APIKeyConfig:
    """Configuration for an API key"""
    provider: KeyProvider
    key: str
    is_valid: bool = False
    last_validated: Optional[str] = None


class SecureKeyManager:
    """Manages API keys securely using system keychain or encrypted storage"""
    
    def __init__(self, use_keychain: bool = True):
        self.use_keychain = use_keychain
        self.service_name = "mcp-unified"
        self.config_dir = Path.home() / ".mcp"
        self.config_dir.mkdir(exist_ok=True)
        self.keys_file = self.config_dir / ".keys.encrypted"
        self.cipher = None
        
        if not use_keychain:
            self._init_encryption()
        
        # Your provided API keys (will be stored securely on first run)
        self.default_keys = {
            KeyProvider.OPENAI: "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",
            KeyProvider.DEEPSEEK: "sk-c8a5f1725d7b4f96b29a3d041848cb74",
            KeyProvider.QWEN: "qwen-api-key-ad6c81",
            KeyProvider.ANTHROPIC: "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",
            KeyProvider.LLAMA: "llx-MfsEhU0wHNL7PcRN4YEFM3eWcPQggq7edEr52IdnvkHZPPYj",
            KeyProvider.GROQ: "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",
            KeyProvider.XAI: "xai-4WmKCCbqXhuxL56tfrCxaqs3N84fcLVirQG0NIb0NB6ViDPnnvr3vsYOBwpPKpPMzW5UMuHqf1kv87m3"
        }
        
        # Initialize keys on first run
        self._init_default_keys()
    
    def _init_encryption(self):
        """Initialize encryption for file-based storage"""
        key_file = self.config_dir / ".mcp.key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
        
        self.cipher = Fernet(key)
    
    def _init_default_keys(self):
        """Store default keys securely on first run"""
        for provider, key in self.default_keys.items():
            if not self.get_key(provider):
                self.set_key(provider, key)
                logger.info(f"Initialized {provider.value} API key")
    
    def set_key(self, provider: KeyProvider, api_key: str) -> bool:
        """Store an API key securely"""
        try:
            if self.use_keychain:
                keyring.set_password(
                    self.service_name,
                    provider.value,
                    api_key
                )
            else:
                # Use encrypted file storage
                keys = self._load_encrypted_keys()
                keys[provider.value] = api_key
                self._save_encrypted_keys(keys)
            
            logger.info(f"Stored API key for {provider.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store key for {provider.value}: {e}")
            return False
    
    def get_key(self, provider: KeyProvider) -> Optional[str]:
        """Retrieve an API key"""
        try:
            if self.use_keychain:
                return keyring.get_password(
                    self.service_name,
                    provider.value
                )
            else:
                keys = self._load_encrypted_keys()
                return keys.get(provider.value)
                
        except Exception as e:
            logger.error(f"Failed to retrieve key for {provider.value}: {e}")
            # Fall back to environment variable
            env_key = f"{provider.value.upper()}_API_KEY"
            return os.getenv(env_key)
    
    def _load_encrypted_keys(self) -> Dict[str, str]:
        """Load keys from encrypted file"""
        if not self.keys_file.exists():
            return {}
        
        try:
            with open(self.keys_file, 'rb') as f:
                encrypted_data = f.read()
                decrypted = self.cipher.decrypt(encrypted_data)
                return json.loads(decrypted.decode())
        except Exception as e:
            logger.error(f"Failed to load encrypted keys: {e}")
            return {}
    
    def _save_encrypted_keys(self, keys: Dict[str, str]):
        """Save keys to encrypted file"""
        try:
            data = json.dumps(keys).encode()
            encrypted = self.cipher.encrypt(data)
            with open(self.keys_file, 'wb') as f:
                f.write(encrypted)
            os.chmod(self.keys_file, 0o600)
        except Exception as e:
            logger.error(f"Failed to save encrypted keys: {e}")
    
    def validate_key(self, provider: KeyProvider) -> bool:
        """Validate an API key by making a test request"""
        key = self.get_key(provider)
        if not key:
            return False
        
        # Provider-specific validation
        validators = {
            KeyProvider.ANTHROPIC: self._validate_anthropic,
            KeyProvider.OPENAI: self._validate_openai,
            KeyProvider.DEEPSEEK: self._validate_deepseek,
            KeyProvider.QWEN: self._validate_qwen,
        }
        
        validator = validators.get(provider)
        if validator:
            return validator(key)
        
        # Assume valid if no validator
        return True
    
    def _validate_anthropic(self, key: str) -> bool:
        """Validate Anthropic API key"""
        try:
            import anthropic
            client = anthropic.Client(api_key=key)
            # Make minimal test request
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception as e:
            logger.error(f"Anthropic key validation failed: {e}")
            return False
    
    def _validate_openai(self, key: str) -> bool:
        """Validate OpenAI API key"""
        try:
            import openai
            openai.api_key = key
            # List models to test key
            models = openai.Model.list()
            return True
        except Exception as e:
            logger.error(f"OpenAI key validation failed: {e}")
            return False
    
    def _validate_deepseek(self, key: str) -> bool:
        """Validate DeepSeek API key"""
        try:
            import requests
            headers = {"Authorization": f"Bearer {key}"}
            response = requests.get(
                "https://api.deepseek.com/v1/models",
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"DeepSeek key validation failed: {e}")
            return False
    
    def _validate_qwen(self, key: str) -> bool:
        """Validate Qwen API key"""
        try:
            import requests
            headers = {"Authorization": f"Bearer {key}"}
            response = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers=headers,
                json={
                    "model": "qwen-turbo",
                    "input": {"messages": [{"role": "user", "content": "test"}]},
                    "parameters": {"max_tokens": 1}
                },
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Qwen key validation failed: {e}")
            return False
    
    def get_all_keys(self) -> Dict[KeyProvider, APIKeyConfig]:
        """Get all configured API keys with validation status"""
        configs = {}
        
        for provider in KeyProvider:
            key = self.get_key(provider)
            if key:
                configs[provider] = APIKeyConfig(
                    provider=provider,
                    key=key[:8] + "..." + key[-4:],  # Masked for display
                    is_valid=self.validate_key(provider)
                )
        
        return configs
    
    def mask_key(self, key: str) -> str:
        """Mask API key for display"""
        if len(key) <= 12:
            return "*" * len(key)
        return key[:4] + "*" * (len(key) - 8) + key[-4:]


# Global key manager instance
key_manager = SecureKeyManager(use_keychain=True)