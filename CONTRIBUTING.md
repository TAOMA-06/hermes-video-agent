# Contributing

Thanks for helping improve Hermes Video Agent.

## Before opening a change

- Read [SECURITY.md](SECURITY.md) first. Do not file public issues for potential security vulnerabilities.
- Keep the project a standalone Hermes user plugin. Changes must not require edits to Hermes core.
- Preserve the safety model: do not overwrite source media, bypass Hermes approvals, accept paths outside the configured workspace, or introduce shell-string command execution.

## Development setup

1. Fork and clone this repository.
2. Obtain a clean Hermes checkout separately.
3. Run the isolated integration test from the Hermes checkout:

~~~sh
scripts/run_tests.sh /absolute/path/to/hermes-video-agent/tests/test_hermes_video_agent.py
~~~

The test uses a temporary Hermes home and fake ffmpeg, STT, and LLM implementations. Do not add real API keys, real media, generated previews, or local profile files to the repository.

## Pull requests

- Use a focused title and explain the user-visible behavior.
- Add or update tests for behavior changes.
- Update documentation and [CHANGELOG.md](CHANGELOG.md) when appropriate.
- Keep configuration examples free of credentials and machine-specific paths.
- Ensure the CI workflow passes before requesting review.

By contributing, you agree that your contribution is licensed under the [MIT License](LICENSE).
