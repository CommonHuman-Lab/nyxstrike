# Contributing

Thank you for your interest in contributing 🎉
We appreciate all contributions from the community. To keep the project stable and maintainable, please follow the guidelines below.

## Getting Started

1. Fork the repository
2. Create a feature branch from beta/x.x.x
3. Make your changes
4. Test your changes
5. Open a Pull Request against beta/x.x.x

## Pull Request Guidelines

[Pull Request Template](https://github.com/CommonHuman-Lab/nyxstrike/wiki/Pull-Request-Template)

### Scope

Pull Requests should be small, focused, and address a single concern.

✅ Allowed:

- Bug fixes
- New features
- Refactoring with a clear purpose
- Documentation updates

❌ Avoid:

- Modifying files unrelated to your change
- Mixing formatting changes with functional changes
- Large bulk or automated changes without review

If you want to submit formatting changes, they must be done in a separate Pull Request.

## Pull Request Size Limits

To keep reviews efficient and maintain high code quality, Pull Requests should remain reasonably small and focused.

### Recommended Limits

- Prefer PRs under **300 changed lines**
- Avoid PRs exceeding **500 changed lines**
- Large changes should be split into smaller, logical PRs

### Exclusions

The following may exceed size limits if submitted separately:

- Formatting-only changes
- Dependency updates
- Generated files
- Large documentation updates

### Best Practices

- Keep PRs scoped to a single feature or fix  
- Separate refactoring from functional changes  
- Submit formatting or lint fixes in their own PR  
- Break large features into smaller incremental changes  

### Maintainer Policy

Maintainers may request that oversized Pull Requests be split into smaller ones before review. Extremely large or unfocused PRs may be closed and asked to be resubmitted in a more reviewable format.

## Code Style & Formatting

This project uses consistent formatting and style rules. Please ensure that you:

- Follow the existing code style
- Run any configured formatters or linters before committing
- Avoid unnecessary whitespace or line-ending changes

Pull Requests containing large formatting-only diffs may be rejected.

## AI-Assisted Contributions

AI tools may be used as assistance, but contributors remain fully responsible for their submissions.

### Requirements

- All generated code must be reviewed and understood by the contributor
- Code must be tested before submission
- Do not submit bulk-generated or unrelated changes

Maintainers may reject Pull Requests containing unreviewed, low-quality, or noisy AI-generated code.

## Testing

Before submitting a Pull Request:

- Ensure existing tests pass
- Add tests when appropriate
- Verify your changes do not break existing functionality

## Commit Messages

Please use clear and descriptive commit messages.

### Recommended style

type: short description

### Examples

- fix: resolve null pointer issue in mcp handler
- feat: add support for configuration profiles
- docs: update installation instructions
- refactor: simplify validation logic

## Branch Naming

Please use descriptive branch names:

- feature/short-description
- fix/short-description
- docs/short-description
- refactor/short-description

## Code Reviews

All contributions require review before merging. Reviewers may request changes to:

- Improve code quality
- Ensure consistency
- Reduce unnecessary complexity
- Remove unrelated changes

## Respect the Scope of the Project

If you are unsure whether your change fits the project, please open an issue first to discuss it.

## Reporting Issues

When reporting issues, please include:

- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (if relevant)

## Code of Conduct

Please be respectful and constructive when interacting with maintainers and other contributors.

---

If you have questions, feel free to open an issue or discussion.

Thank you for helping improve the project ❤️