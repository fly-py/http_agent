# AGENTS.md - Coding Guidelines for AI Agents

## Project Overview
Python HTTP proxy server with threading support for HTTP and HTTPS tunneling.

## Commands

### Running
```bash
python main.py
```

### Testing
No test framework configured yet. When tests are added:
```bash
# Run all tests
pytest

# Run single test
pytest test_file.py::test_function -v

# Run with coverage
pytest --cov=. --cov-report=term-missing
```

### Linting & Formatting
No linting tools configured. Recommended setup:
```bash
# Format code
black main.py

# Lint code
flake8 main.py

# Type checking
mypy main.py
```

## Code Style Guidelines

### General
- Python 3.x compatibility required
- Use UTF-8 encoding for all files
- Maximum line length: 100 characters

### Imports
- Standard library imports first
- Group imports: stdlib, third-party, local
- Use absolute imports
- Example:
```python
import socket
import threading
import json
import datetime
```

### Naming Conventions
- `PascalCase` for class names (e.g., `HTTPProxy`)
- `snake_case` for functions and variables
- `UPPER_CASE` for constants
- Private methods: prefix with underscore `_private_method`

### Types
- Use type hints where practical
- Document complex return types in docstrings

### Error Handling
- Use specific exceptions (`FileNotFoundError`, `json.JSONDecodeError`)
- Always close sockets in `finally` blocks
- Log errors with context before handling
- Avoid bare `except:` clauses
- Example:
```python
try:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    # Handle missing file
    pass
except json.JSONDecodeError as e:
    # Handle invalid JSON
    pass
finally:
    # Cleanup resources
    socket.close()
```

### Threading
- Set daemon threads for background tasks: `thread.daemon = True`
- Use locks for shared resources (`threading.Lock()`)
- Set timeouts on sockets to prevent indefinite blocking

### Documentation
- Use docstrings for classes and public methods
- Keep comments in Chinese (existing convention)
- Format: `"""Brief description"""`

### Configuration
- Use JSON for configuration files
- Provide default values for all config options
- Handle missing config gracefully with sensible defaults

### Logging
- Use the class `log()` method for consistency
- Include context (client address, target host) in log messages
- Log both to console and optionally to file

## File Structure
```
.
├── main.py          # Main proxy server implementation
├── config.json      # Server configuration
└── proxy.log        # Generated log file (if enabled)
```

## Key Classes
- `HTTPProxy`: Main proxy server class
  - `__init__(config_file)`: Initialize with config
  - `start()`: Start the server
  - `handle_client()`: Handle individual connections
  - `tunnel()`: Bidirectional data forwarding

## Important Notes
- Server binds to `0.0.0.0` by default (all interfaces)
- Default port: 8888 (configurable)
- Supports HTTP and HTTPS (CONNECT method)
- Threads are daemon threads (exits on main thread exit)
