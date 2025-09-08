# Sophia Audit CLI

A lightweight command-line tool that provides project-aware audit helpers.

Current subcommands:

- audit codebase structure [--path PATH] [--format json|text] [--top N] [--exclude DIR ...]
- audit repo size [--path PATH] [--format json|text] [--top N] [--exclude DIR ...]
- audit deps vulnerabilities [--format json|text]
- audit py security [--path PATH] [--format json|text]
- audit smells [--path PATH] [--format json|text] [--exclude DIR ...] [--large-file-mb N] [--long-file-lines N] [--top N]

Examples:

- audit codebase structure
- audit codebase structure --path . --format json --top 15
- audit repo size --exclude node_modules --exclude .venv --exclude .next
- audit deps vulnerabilities --format json
- audit py security --path app --format json
- audit smells --path . --exclude node_modules --large-file-mb 20 --top 5
