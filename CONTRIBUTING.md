# Contributing to PawVision

Thank you for your interest in contributing to PawVision! This document provides guidelines and instructions for contributing.

## 🎯 Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of Python and Flask

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/PawVision.git
   cd PawVision
   ```

2. **Install the locked development environment**
    ```bash
    uv sync --locked --group dev
    ```

4. **Run tests to verify setup**
   ```bash
   uv run pytest tests/ -v
   ```

5. **Start the development server**
   ```bash
   uv run python main.py
   ```
   The application will auto-detect dev mode and run on `http://localhost:5001`

## 🔧 Development Workflow

### Branch Strategy

- `main` - Stable production releases
- `dev` - Development branch for next release
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, readable code
   - Follow PEP 8 style guidelines
   - Add docstrings to functions and classes
   - Include type hints where possible

3. **Write tests**
   - Add tests for new features
   - Ensure existing tests pass
   - Aim for 80%+ code coverage

4. **Run quality checks**
   ```bash
   # Format code
   make format
   
   # Run linters
   make lint
   
   # Run tests
   make test
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing new feature"
   ```
   
   Use [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` - New features
   - `fix:` - Bug fixes
   - `docs:` - Documentation changes
   - `style:` - Code style changes (formatting, etc.)
   - `refactor:` - Code refactoring
   - `test:` - Adding or updating tests
   - `chore:` - Maintenance tasks

6. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📝 Pull Request Guidelines

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated (if needed)
- [ ] No merge conflicts with `dev` branch
- [ ] Commit messages follow conventional commits

### PR Description Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How has this been tested?

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code formatted with black
- [ ] Linting passes
```

## 🧪 Testing Guidelines

### Writing Tests

Place tests in the `tests/` directory:
- `test_*.py` - Test files
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies

Example:
```python
import unittest
from unittest.mock import Mock, patch
from pawvision.video_player import VideoPlayer

class TestVideoPlayer(unittest.TestCase):
    def setUp(self):
        self.config = Mock()
        self.player = VideoPlayer(self.config, ["/videos"])
    
    def test_play_video_success(self):
        """Test successful video playback."""
        result = self.player.play_random_video()
        self.assertTrue(result)
    
    def test_play_video_no_videos(self):
        """Test playback fails when no videos available."""
        self.player.video_dirs = []
        result = self.player.play_random_video()
        self.assertFalse(result)
```

### Running Tests

```bash
# Run all tests
 uv run pytest tests/ -v

# Run specific test file
 uv run pytest tests/test_video_player.py -v

# Run with coverage
 uv run pytest tests/ --cov=pawvision --cov-report=html

# Run only unit tests (skip integration)
 uv run pytest tests/ -v -m "not integration"
```

## 📚 Documentation Guidelines

### Code Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Include parameter types and return types

Example:
```python
def play_video(self, video_path: str, source: str = "manual") -> bool:
    """Play a video file.
    
    Args:
        video_path: Absolute path to the video file
        source: Source of the play request ("button", "schedule", "api")
    
    Returns:
        True if playback started successfully, False otherwise
    
    Raises:
        VideoNotFoundError: If video file doesn't exist
        PlaybackError: If video playback fails to start
    """
```

### Documentation Files

- Update relevant `.md` files in `docs/`
- Keep README.md up to date
- Update API.md for API changes
- Add examples for new features

## 🎨 Code Style Guidelines

### Python Style

Follow PEP 8 with these specifics:
- Line length: 100 characters (relaxed from 79)
- Use double quotes for strings
- Use f-strings for formatting
- One import per line
- Group imports: stdlib, third-party, local

### Frontend Style

- Use 4 spaces for indentation
- Semicolons optional but consistent
- Use `const` and `let`, not `var`
- Meaningful variable names
- JSDoc comments for functions

### Example

```python
"""Module for video playback management."""

import os
import logging
from typing import List, Optional

from flask import Flask, request
from .config import PawVisionConfig


class VideoPlayer:
    """Manages video playback with proper process management."""
    
    def __init__(self, config: PawVisionConfig, video_dirs: List[str]):
        """Initialize the video player.
        
        Args:
            config: Application configuration
            video_dirs: List of directories containing videos
        """
        self.config = config
        self.video_dirs = video_dirs
        self.logger = logging.getLogger(__name__)
```

## 🐛 Bug Reports

### Before Submitting

1. Check if the bug is already reported
2. Verify it's not a configuration issue
3. Try to reproduce with minimal steps

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g., Raspberry Pi OS]
- Python version: [e.g., 3.11]
- PawVision version: [e.g., 2.0.0]

**Additional context**
Any other relevant information.
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Additional context**
Any other context or screenshots.

**Would you like to implement this feature?**
Yes/No - If yes, we'll provide guidance!
```

## 🏆 Recognition

Contributors will be:
- Listed in the README
- Mentioned in release notes
- Credited in commit history

## 📞 Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Chat**: Join our community (link TBD)

## 📄 License

By contributing, you agree that your contributions will be licensed under the AGPL v3 license.

---

Thank you for contributing to PawVision! 🐾
