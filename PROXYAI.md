# ProxyAI Instructions

## Project Overview
Music Library Organizer - A Python-based movie collection management system that automates movie file organization, metadata extraction from Douban API, and intelligent filename parsing.

## Conventions
- **Branch naming**: Use descriptive branch names (e.g., `feature/`, `fix/`, `docs/`)
- **Commit messages**: Follow semantic commit format (`type: message` or `feat:`, `fix:`, `refactor:`)
- **Code style**: PEP 8 compliant Python code with type hints
- **Documentation**: Maintain README.md and docs/ directory for all new features
- **Testing**: Write unit tests for all new functionality before merging

## Risk Areas
1. **Douban API changes**: External dependencies may break existing integrations
2. **Filename parsing logic**: Changes to regex patterns affect existing file organization
3. **Configuration files**: YAML configuration changes require careful versioning
4. **Logging system**: Logger refactoring impacts debugging capabilities across modules

## Review Rules
- All pull requests must include test coverage (minimum 80% for new features)
- Documentation updates required for public APIs and user-facing features
- Breaking changes require migration guide in CHANGE_HISTORY.md
- Code must pass all existing tests before merging
- New dependencies require justification and PyPI packaging considerations

## Development Workflow
1. Create branch from `master`
2. Implement feature with tests and documentation
3. Run `pytest` to verify all tests pass
4. Update CHANGE_HISTORY.md with significant changes
5. Submit pull request with clear description

---