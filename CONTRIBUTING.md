# Contributing

Thanks for your interest in improving the Data Quality Framework!

## Development Setup

git clone https://github.com/meownikenia/data-quality-framework.git
cd data-quality-framework
make install
pre-commit install

## Development Workflow

make test      # run test suite
make lint      # run ruff + mypy
make format    # auto-format code
make demo      # run example pipeline

## Coding Standards

- Follow PEP 8 (enforced by Ruff)
- Type hints required for public APIs
- Test coverage target: >= 85%
- Commit messages follow Conventional Commits

## Pull Request Process

1. Fork the repository
2. Create a feature branch (git checkout -b feat/amazing-feature)
3. Add tests for your changes
4. Ensure make test and make lint pass
5. Submit a pull request with a clear description

## Reporting Issues

Please include:
- Python version
- Package version
- Minimal reproducible example
- Expected vs actual behavior

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
