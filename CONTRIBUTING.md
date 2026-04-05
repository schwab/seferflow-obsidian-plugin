# Contributing to Book Reader

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## How to Contribute

### Reporting Bugs

1. **Check existing issues** - Avoid duplicates
2. **Create a detailed bug report** including:
   - Python version (`python --version`)
   - OS and version (`uname -a`)
   - Installation method
   - Exact steps to reproduce
   - Expected vs actual behavior
   - Error messages/logs
   - Audio device info (`aplay -l`)

### Suggesting Features

1. **Check discussions** - See if it's already been suggested
2. **Describe the feature**:
   - What problem does it solve?
   - How should it work?
   - Any mockups or examples?
   - Potential challenges?
3. **Consider implications**:
   - Will it break existing code?
   - Does it fit the scope?
   - What's the maintenance burden?

### Code Changes

1. **Fork the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/book-reader.git
   cd book-reader
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/my-amazing-feature
   ```

3. **Set up development environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install pytest pytest-cov black flake8
   ```

4. **Make your changes**
   - Keep commits atomic and focused
   - Write clear commit messages
   - Add comments for complex logic
   - Test your changes thoroughly

5. **Follow code style**
   ```bash
   # Format code
   black book_reader*.py
   
   # Check for issues
   flake8 book_reader*.py
   
   # Verify syntax
   python -m py_compile book_reader*.py
   ```

6. **Test your changes**
   ```bash
   # Run linting
   flake8 book_reader*.py
   
   # Test specific functionality manually
   ./verify_book_reader.sh
   
   # Test interactive mode
   ./book_reader
   
   # Test batch mode
   ./book_reader --batch --list-voices
   ```

7. **Commit and push**
   ```bash
   git add .
   git commit -m "Add feature: descriptive message"
   git push origin feature/my-amazing-feature
   ```

8. **Create a Pull Request**
   - Link to related issues
   - Describe changes clearly
   - Explain why this is needed
   - Note any breaking changes
   - Include testing instructions

## Code Style Guidelines

### Python Style
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use `black` for formatting: `black book_reader*.py`
- Line length: max 127 characters
- Use type hints where helpful (optional)

### Documentation
- Docstrings for all functions
- Clear comments for complex logic
- Update README.md if adding features
- Add entry to CHANGELOG.md

### Terminal Safety
- **NO raw tty mode** (`tty.setraw()`)
- **NO `select.select()` on stdin** (polling)
- Use simple `input()` for user input
- ANSI codes for display only (safe)
- Test on multiple terminals (xterm, alacritty, etc.)

### Commit Messages
```
Capitalized, short (50 chars or less) summary

More detailed explanation if necessary. Wrap at 72 characters.
Explain what the change does, not how it does it.

Fixes #123
Closes #456
```

## Testing

### Manual Testing Checklist

- [ ] Run on target Python version (3.8-3.11)
- [ ] Test on Linux and macOS
- [ ] Verify no terminal corruption
- [ ] Test with different PDFs
- [ ] Try different chapter lengths
- [ ] Test all voice options
- [ ] Try all speed settings
- [ ] Test Ctrl+C handling
- [ ] Verify error messages are helpful
- [ ] Check memory usage (long chapters)

### Adding Tests

If adding major features:

1. Create `tests/test_feature.py`
2. Write unit tests for new functions
3. Include edge cases
4. Run: `pytest tests/ -v`
5. Check coverage: `pytest --cov=book_reader tests/`

## Performance Considerations

- **First audio**: Target ~15-20 seconds
- **Display updates**: 400ms polling (don't exceed)
- **Memory**: Queue maxsize=3 (bounded)
- **CPU**: Should not spike during display
- **Audio**: No stuttering or gaps

## Debugging Tips

### Enable verbose output
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test TTS generation
```bash
./book_reader --batch /path/to/book.pdf --chapter 1
```

### Check buffer queue
```python
# In stream_and_play(), inspect queue size:
print(f"Queue: {audio_queue.qsize()} / {audio_queue.maxsize}")
```

### Audio device debugging
```bash
# List devices
aplay -l

# Test with specific device
aplay -D hw:0,0 /path/to/audio.wav
```

## Areas We Need Help

- [ ] macOS testing
- [ ] Different terminal emulators
- [ ] Non-ASCII PDF text handling
- [ ] Performance optimization
- [ ] Documentation improvements
- [ ] Additional voice/TTS engines
- [ ] Pause/resume implementation (safely)
- [ ] Web UI prototype
- [ ] Integration tests

## Review Process

1. **Automated checks** must pass (CI/CD)
2. **Code review** for quality and style
3. **Testing** on multiple platforms
4. **Documentation** must be updated
5. **Merge** to develop, then main

## License

By contributing, you agree that your contributions will be licensed under the same MIT License that covers the project.

## Questions?

- Open a GitHub issue
- Start a discussion
- Check existing docs
- Review closed issues/PRs for similar questions

## Recognition

Contributors are acknowledged in:
- CHANGELOG.md
- GitHub contributors page
- Project README (major contributions)

Thank you for making Book Reader better! 🎉

---

**Happy contributing!**
