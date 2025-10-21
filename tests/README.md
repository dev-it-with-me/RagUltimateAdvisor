# Testing Documentation

## Overview

This directory contains the test suite for the Ultimate Advisor RAG application. Tests are written using pytest and cover unit tests, integration tests, and end-to-end tests.

## Test Structure

```
tests/
├── test_query_vector_store.py  # Vector store query tests
├── conftest.py                  # Shared fixtures (if needed)
└── README.md                    # This file
```

## Running Tests

### Run All Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with output capture disabled (see print statements)
uv run pytest -s
```

### Run Specific Tests

```bash
# Run a specific test file
uv run pytest tests/test_query_vector_store.py

# Run a specific test function
uv run pytest tests/test_query_vector_store.py::test_query_function

# Run tests matching a pattern
uv run pytest -k "query"
```

### Test Coverage

```bash
# Run with coverage report
uv run pytest --cov=src --cov-report=html

# View coverage in terminal
uv run pytest --cov=src --cov-report=term-missing

# Generate XML coverage report (for CI/CD)
uv run pytest --cov=src --cov-report=xml
```

Coverage reports are generated in `htmlcov/` directory. Open `htmlcov/index.html` in a browser to view detailed coverage.

## Test Categories

### Unit Tests

Test individual components in isolation:

```python
def test_rag_repository_initialization():
    """Test RAGRepository initializes correctly."""
    repo = RAGRepository()
    assert repo.client is not None
    assert repo.embed_model is not None
```

### Integration Tests

Test interactions between components:

```python
def test_query_processing_flow():
    """Test complete query processing flow."""
    service = RAGService()
    result = service.query("test query")
    assert result.response is not None
    assert len(result.source_documents) > 0
```

### End-to-End Tests

Test complete user workflows:

```python
def test_api_query_endpoint():
    """Test API query endpoint."""
    response = client.post(
        "/api/rag/query",
        json={"query": "test query"}
    )
    assert response.status_code == 200
    assert "response" in response.json()
```

## Writing Tests

### Test File Naming

- Test files must start with `test_` or end with `_test.py`
- Example: `test_feature.py` or `feature_test.py`

### Test Function Naming

- Test functions must start with `test_`
- Use descriptive names that explain what is being tested
- Example: `test_query_returns_relevant_documents()`

### Basic Test Structure

```python
import pytest
from src.rag.services import RAGService

class TestRAGService:
    """Test suite for RAG service."""

    @pytest.fixture
    def service(self):
        """Create RAG service instance."""
        return RAGService()

    def test_query_success(self, service):
        """Test successful query processing."""
        # Arrange
        query = "What is RAG?"

        # Act
        result = service.query(query)

        # Assert
        assert result is not None
        assert result.response != ""
        assert len(result.source_documents) > 0

    def test_query_empty_input(self, service):
        """Test query with empty input."""
        with pytest.raises(ValueError):
            service.query("")
```

## Fixtures

### Common Fixtures

```python
# conftest.py
import pytest
from src.dependencies import get_rag_repository

@pytest.fixture
def rag_repository():
    """Provide RAG repository instance."""
    return get_rag_repository()

@pytest.fixture
def sample_document():
    """Provide sample document for testing."""
    return {
        "content": "Sample document content",
        "metadata": {"source": "test.pdf"}
    }
```

### Using Fixtures

```python
def test_with_fixtures(rag_repository, sample_document):
    """Test using fixtures."""
    result = rag_repository.index_document(sample_document)
    assert result is True
```

## Mocking

### Mocking External Services

```python
from unittest.mock import Mock, patch

def test_with_mock_llm():
    """Test with mocked LLM."""
    with patch('src.rag.repositories.Anthropic') as mock_llm:
        mock_llm.return_value.complete.return_value = "Mocked response"

        service = RAGService()
        result = service.query("test")

        assert result.response == "Mocked response"
```

### Mocking Database

```python
@patch('src.history.repositories.Session')
def test_with_mock_db(mock_session):
    """Test with mocked database."""
    mock_session.return_value.query.return_value.all.return_value = []

    service = HistoryService()
    result = service.get_history()

    assert result == []
```

## Test Configuration

### pytest.ini

Create `pytest.ini` in project root:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

### Environment Variables

For testing, create `.env.test`:

```bash
APP_CHROMA_PERSIST_DIRECTORY=.chroma_test
APP_HISTORY_DB_PATH=test_advisor.db
APP_LOG_LEVEL=WARNING
```

Load test environment:

```python
from dotenv import load_dotenv

@pytest.fixture(autouse=True)
def load_test_env():
    """Load test environment variables."""
    load_dotenv(".env.test")
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.12'

    - name: Install UV
      run: |
        powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

    - name: Install dependencies
      run: |
        uv sync

    - name: Run tests
      run: |
        uv run pytest --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Performance Testing

### Load Testing

```python
import time
import concurrent.futures

def test_concurrent_queries():
    """Test system under concurrent load."""
    queries = ["query1", "query2", "query3"] * 10

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        start = time.time()
        results = list(executor.map(process_query, queries))
        duration = time.time() - start

    assert all(r is not None for r in results)
    assert duration < 30  # Should complete within 30 seconds
```

### Benchmark Tests

```python
import pytest

@pytest.mark.benchmark
def test_indexing_performance(benchmark):
    """Benchmark document indexing."""
    documents = load_test_documents()

    result = benchmark(index_documents, documents)

    assert result is True
    assert benchmark.stats['mean'] < 1.0  # Average under 1 second
```

## Debugging Tests

### Using pdb

```python
def test_debug_example():
    """Example test with debugging."""
    import pdb; pdb.set_trace()  # Debugger breakpoint

    result = complex_function()
    assert result is not None
```

### Verbose Output

```bash
# Show all output including print statements
uv run pytest -s -vv

# Show only failed tests
uv run pytest --tb=short

# Show local variables in tracebacks
uv run pytest -l
```

## Best Practices

1. **Keep tests fast**: Mock external services when possible
2. **Use descriptive names**: Test names should explain what they test
3. **Test one thing**: Each test should verify a single behavior
4. **Use fixtures**: Share common setup code via fixtures
5. **Clean up**: Ensure tests don't leave side effects
6. **Test edge cases**: Include tests for error conditions
7. **Maintain coverage**: Aim for >80% code coverage

## Common Issues

### Import Errors

Ensure the project root is in Python path:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Database Lock

Use separate test database:

```python
@pytest.fixture
def test_db():
    """Create test database."""
    db_path = "test_temp.db"
    yield db_path
    os.remove(db_path)  # Cleanup
```

### Async Tests

For async code:

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_function()
    assert result is not None
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Best Practices](https://docs.pytest.org/en/latest/explanation/goodpractices.html)
- [Testing FastAPI](https://fastapi.tiangolo.com/tutorial/testing/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)