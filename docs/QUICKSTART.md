# Quickstart

Install RAD, confirm it is healthy, then give it a real objective.

## 1. Install

Requires Python 3.9+ (3.11 or 3.12 recommended). The core has **no mandatory
dependencies**.

```bash
git clone https://github.com/seven0070/rad-agent-.git && cd rad-agent-
python3 -m venv .venv && . .venv/bin/activate
pip install -e .
rad version          # prints 0.2.1
```

On Debian/Ubuntu, `python3 -m venv` needs the `python3-venv` package
(`sudo apt install python3-venv`).

## 2. Configure a brain (optional for tests; required for chat)

RAD runs offline without a key (control plane, memory, lab banks, acceptance).
Talking to a model needs **one** of:

```bash
rad keys add groq gsk_…                 # free-tier cloud
# or:  rad keys add nvidia <nvapi-…>     # NVIDIA NIM (default: llama-3.2-11b-vision-instruct)
# or:  export GROQ_API_KEY=… / NVIDIA_NIM_API_KEY=…
# or:  rad keys add openai sk-…
# or:  ollama serve && ollama pull llama3.2   # local, no key
rad providers                            # what RAD can see
```

Keys are read from the vault → environment → `.env`. Never put secrets in prompts.

## 3. Doctor

```bash
rad doctor                 # READY / WARNING / OPTIONAL / ERROR
rad doctor --offline       # skip provider / network probes
```

A missing provider is **OPTIONAL**, not an error. Exit code 1 only if something
is ERROR. `--fix` repairs dirs, permissions, config types, migrations and
quarantines corrupt files (never deletes).

## 4. Start

```bash
rad                        # chat (default)
rad status                 # one-screen health
```

## 5. First objective

Pick a workspace (defaults to `~/.rad/workspace`):

```bash
rad config set workspace "$PWD"
rad objective run "Write hello.py that prints hello, then prove it runs" --auto
rad inspect last           # plan → tasks → evidence
rad why hello.py           # provenance
```

Without `--auto`, file/shell writes ask for confirmation. Hard blocks (sudo,
`rm -rf /`, keys, private hosts) still apply.

## 6. Prove the install

```bash
pip install -e ".[dev]"
python -m pytest -q        # offline unit/integration suite
rad acceptance             # 50-item gate, per-item evidence
rad realworld              # research / coding / multi-agent / crash-resume
```

Live-model evaluation (`rad evaluate`, `rad chat` against a cloud/local brain)
needs a key or a local engine. If none is configured, those commands refuse
honestly instead of fabricating answers.

See [INSTALLATION](INSTALLATION.md), [CONFIGURATION](CONFIGURATION.md),
[CLI](CLI.md), [TROUBLESHOOTING](TROUBLESHOOTING.md).
