# Development & Contributing

## How to Contribute
1. Fork the repository and clone your fork.
2. Create a feature branch for your changes.
3. Make your changes, following the code style and structure.
4. Write or update tests as needed.
5. Commit and push your changes.
6. Open a pull request (PR) with a clear description.

---

## How Development Works (Step by Step)
1. **Branching**: Always work on a new branch for each feature or fix.
2. **Coding**: Follow the modular structure—put new features in the right submodule.
3. **Testing**: Add or update tests to cover your changes.
4. **Documentation**: Update the docs so others can understand and use your work.
5. **Pull Request**: Submit your PR and respond to feedback.

---

### In Plain English
- Contributing is like adding a new tool or feature to a well-organized workshop: you put it in the right place, label it clearly, and make sure everyone knows how to use it.

## Code Style
- Use clear, descriptive names for classes, functions, and variables.
- Keep modules focused and maintainable.
- Document all public classes and functions.
- Use type hints where possible.

## Testing
- Place tests in `test_simple_agent.py` or a dedicated `tests/` directory.
- Use standard Python testing tools (e.g., `unittest`, `pytest`).
- Ensure all tests pass before submitting a PR.

## Adding New Features
- For new tools/commands, see [commands.md](commands.md).
- For new core features, add to the appropriate submodule in `core/`.
- Update documentation for any new features or changes.

## Reporting Issues
- Use GitHub Issues to report bugs or request features.
- Provide as much detail as possible for reproducibility. 