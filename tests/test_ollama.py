"""Test script to check if Ollama is running and accessible.

This test verifies that the Ollama service is up and responding to API requests.
"""

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

# Add src to path for imports (if needed)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import settings


def test_ollama_accessible() -> None:
    """Test if Ollama service is running and accessible via API."""
    print("=== Testing Ollama Accessibility ===\n")

    # 1. Attempt to connect to Ollama API
    print("1. Checking Ollama API connection:")
    try:
        with urllib.request.urlopen(
            "http://localhost:11434/api/version", timeout=5
        ) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                version = data.get("version", "unknown")
                print(f"   ✓ Ollama is running (version: {version})")
                print("   API endpoint accessible")
            else:
                pytest.fail(f"Ollama API returned status {response.status}")
    except urllib.error.URLError as e:
        print(f"   ✗ Ollama is not accessible: {e}")
        pytest.fail(f"Ollama service is not running or accessible: {e}")
    except json.JSONDecodeError as e:
        print(f"   ✗ Invalid JSON response from Ollama: {e}")
        pytest.fail(f"Invalid response from Ollama API: {e}")

    print("\n=== Ollama Test Complete ===")
    print("\nTo manually run only this test:")
    print("pytest -k test_ollama_accessible -s")


def test_ollama_models_available() -> None:
    """Test if both chat and embedding models specified in config are available."""
    print("=== Testing Ollama Models Availability ===\n")

    chat_model = settings.CHAT_MODEL
    embedding_model = settings.EMBEDDING_MODEL

    print(f"1. Checking for chat model: {chat_model}")
    print(f"2. Checking for embedding model: {embedding_model}")

    # Get list of available models from Ollama
    try:
        with urllib.request.urlopen(
            f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=10
        ) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                available_models = [model["name"] for model in data.get("models", [])]
                print(f"   Available models: {available_models}")

                # Check if chat model is available
                if chat_model not in available_models:
                    print(f"   ✗ Chat model '{chat_model}' is not available")
                    pytest.fail(
                        f"Chat model '{chat_model}' is not available in Ollama. "
                        f"Available models: {available_models}"
                    )
                else:
                    print(f"   ✓ Chat model '{chat_model}' is available")

                # Check if embedding model is available
                if embedding_model not in available_models:
                    print(f"   ✗ Embedding model '{embedding_model}' is not available")
                    pytest.fail(
                        f"Embedding model '{embedding_model}' is not available in Ollama. "
                        f"Available models: {available_models}"
                    )
                else:
                    print(f"   ✓ Embedding model '{embedding_model}' is available")

            else:
                pytest.fail(
                    f"Failed to get model list from Ollama API (status {response.status})"
                )

    except urllib.error.URLError as e:
        print(f"   ✗ Failed to connect to Ollama API: {e}")
        pytest.fail(f"Cannot check model availability - Ollama API not accessible: {e}")
    except json.JSONDecodeError as e:
        print(f"   ✗ Invalid JSON response from Ollama API: {e}")
        pytest.fail(f"Invalid response from Ollama API when checking models: {e}")

    print("\n=== Models Availability Test Complete ===")
    print("\nTo manually run only this test:")
    print("pytest -k test_ollama_models_available -s")


if __name__ == "__main__":  # Manual invocation
    test_ollama_accessible()
    test_ollama_models_available()
