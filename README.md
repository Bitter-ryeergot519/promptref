# promptref

> Git for prompts. Track, diff, branch, and rollback your LLM prompt versions from the CLI.
![promptref demo](demo.gif)

![PyPI version](https://img.shields.io/pypi/v/promptref)
![Python 3.9+](https://img.shields.io/pypi/pyversions/promptref)
![MIT License](https://img.shields.io/badge/license-MIT-blue)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)

## Install

```
pip install promptref
```

## Quick Start

```
promptref init my-agent
promptref save my-agent "You are a helpful assistant. Be concise." --message "initial version"
promptref save my-agent "You are a helpful assistant. Be concise and professional." --message "improved tone"
promptref log my-agent
promptref diff my-agent <hash1> <hash2>
promptref rollback my-agent <hash1>
```

## Commands

| Command   | Description                          |
|-----------|--------------------------------------|
| init      | Create a new prompt project          |
| save      | Save a new prompt version            |
| log       | View version history                 |
| diff      | Compare two versions                 |
| show      | View a specific version              |
| rollback  | Restore a previous version           |
| branch    | Create a new branch                  |
| switch    | Switch active branch                 |
| list      | List all projects                    |
| export    | Export history to json/txt/yaml      |

## Roadmap

- v0.2: Run prompts directly against OpenAI, Anthropic, Groq, Ollama
- v0.3: Side-by-side output comparison
- v0.4: Eval scoring against test datasets
- v0.5: Team sync via Git remote

## Contributing

PRs welcome. Open an issue first for major changes.
