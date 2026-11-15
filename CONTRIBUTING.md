# Contributing

Thanks for helping improve this Kanban board. Bug fixes, accessibility improvements, documentation, tests, and thoughtful product ideas are welcome.

## Before you start

- Search existing issues and pull requests to avoid duplicate work. Open an issue for a substantial change so its behavior can be discussed first.
- For a small fix, feel free to open a pull request directly.
- Follow the [community guidelines](CODE_OF_CONDUCT.md). Report security problems through the [security policy](SECURITY.md), not a public issue.

## Make a change

1. Fork the repository and create a branch from `main` with a descriptive name, such as `fix/card-order`.
2. Follow the [local setup](README.md#run-locally). The React source is in `web/src`, the API and database logic are in `kanban.py`, and server tests are in `tests`.
3. Keep changes focused. Include a test when behavior or a permission rule changes. Update documentation or screenshots when the user experience changes.
4. Run the checks below, then open a pull request against `main`. Explain what changed, how you checked it, and link any related issue. Add before-and-after screenshots for visual changes.

```sh
python3 -m unittest discover -s tests -v
npm --prefix web ci
npm --prefix web run build
```

For interaction changes, also follow the [visible browser walkthrough](TESTING.md). GitHub Actions runs the server tests and frontend build on pull requests; the Chrome walkthrough runs locally.

Do not commit SQLite databases, `web/node_modules`, `web/dist`, credentials, or personal account data. Use disposable test accounts and a temporary database for screenshots.

Maintainers review pull requests for challenge coverage, server-side permissions, usability, and clear documentation. Please be patient with review and respond to requested changes on the same pull request.
