# Contributing to Tidal MCP

## Welcome Contributors! 🎉

Thank you for your interest in contributing to Tidal MCP. We're excited to collaborate with the community and appreciate your help in making this project better.

## 🌟 Our Vision

Tidal MCP aims to provide a robust, high-performance, and developer-friendly interface for interacting with the Tidal music streaming service. We're committed to creating a tool that is:

- **Performant**: Efficient, non-blocking async operations
- **Type-safe**: Strong typing and comprehensive error handling
- **User-friendly**: Intuitive API design and clear documentation
- **Extensible**: Modular architecture supporting future enhancements

## 📋 Contribution Guidelines

### Getting Started

1. **Fork the Repository**
   - Click "Fork" on the GitHub repository page
   - Clone your forked repository locally
   ```bash
   git clone https://github.com/YOUR_USERNAME/tidal-mcp.git
   cd tidal-mcp
   ```

2. **Set Up Development Environment**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate

   # Install development dependencies
   pip install -e .[dev]
   ```

### Development Workflow

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/issue-description
   ```

2. **Make Changes**
   - Follow PEP 8 style guidelines
   - Use type hints
   - Write comprehensive docstrings
   - Implement robust error handling

3. **Testing**
   ```bash
   # Run unit tests
   pytest tests/

   # Run with coverage
   pytest --cov=tidal_mcp

   # Run specific test types
   pytest -m unit
   pytest -m integration
   ```

### Code Quality Checks

Before submitting a PR, run the following checks:

```bash
# Code formatting
black .

# Type checking
mypy src/tidal_mcp

# Linting
flake8 src/tidal_mcp

# Comprehensive tests
pytest
```

### Commit Guidelines

- Use descriptive, concise commit messages
- Follow conventional commits format:
  ```
  <type>(<scope>): <description>

  Examples:
  feat(auth): add OAuth2 token refresh mechanism
  fix(search): resolve pagination bug in tidal_search
  docs(readme): update installation instructions
  ```

## 🤝 Contribution Types

We welcome various types of contributions:

- 🐛 Bug reports
- 🚀 Feature requests
- 📖 Documentation improvements
- 🧪 Test coverage enhancements
- 💻 Code contributions

### Reporting Issues

1. Check existing issues to avoid duplicates
2. Use issue templates when available
3. Provide clear, reproducible steps
4. Include environment details and error messages

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add tests for new functionality
4. Get approval from maintainers
5. Squash and merge

## Development Setup

### Required Tools
- Python 3.10+
- `pip` or `uvx`
- `git`

### Recommended VSCode Extensions
- Python
- Pylance
- Black Formatter
- Mypy Type Checker

## 🔒 Code of Conduct

- Be respectful and inclusive
- Constructive feedback only
- Collaborate openly and professionally

## 📬 Contact

For questions or discussions:
- Open a GitHub issue
- Join our community discussions

## 🙏 Acknowledgments

Contributors are the heart of open-source projects. Your efforts are greatly appreciated!

---

**Happy Coding!** 🎵🐍
