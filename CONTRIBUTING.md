# Contributing to the Reasoning Council Critique Module

Thank you for considering contributing to this project! We welcome improvements, bug fixes, and additions.

## How to Contribute

1.  **Fork the Repository:** Start by forking the `critique_council` repository to your own GitHub account.
2.  **Create a Branch:** Create a new branch for your changes (e.g., `git checkout -b feature/your-feature-name` or `fix/issue-description`).
3.  **Make Changes:** Implement your changes, ensuring they adhere to the project's standards:
    *   Follow Python best practices and the style defined in `.editorconfig` (e.g., 2-space indentation).
    *   If adding new features, consider their alignment with the project's goals.
    *   Update relevant documentation (`README.md`, docstrings) if necessary.
    *   Add or update tests in the `tests/` directory to cover your changes.
4.  **Run Tests:** Ensure all tests pass by running `python -m pytest tests/ -v` from the project root directory.
5.  **Commit Changes:** Commit your changes with clear, descriptive commit messages.
6.  **Push to Fork:** Push your changes to your forked repository (e.g., `git push origin feature/your-feature-name`).
7.  **Open a Pull Request:** Create a Pull Request (PR) from your branch to the `main` branch of the original `critique_council` repository.
    *   Provide a clear title and description for your PR, explaining the changes and their rationale.
    *   Link any relevant issues if applicable.

## Development Setup

Refer to the main `README.md` for instructions on setting up the development environment, including dependencies and configuration (especially API keys for LLM access).

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct (`CODE_OF_CONDUCT.md`). By participating in this project, you agree to abide by its terms.

## Reporting Security Issues

If you discover a security vulnerability, please refer to the `SECURITY.md` file for reporting instructions. Do **not** open a public issue for security concerns.
