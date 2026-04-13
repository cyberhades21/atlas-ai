# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| latest `main` | Yes |
| older branches | No |

## Reporting a Vulnerability

**Do not open a public issue for security vulnerabilities.**

Please report security issues privately using GitHub's [private vulnerability reporting](https://github.com/cyberhades21/atlas-ai/security/advisories/new).

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

You will receive a response within 7 days. If the vulnerability is confirmed, a fix will be prioritised and you will be credited in the release notes unless you prefer to remain anonymous.

## Scope

ATLAS is a **fully local** system with no cloud components. The primary attack surface is:

- The FastAPI server (`uvicorn app.main:app`) — only run it on trusted networks
- PDF parsing (untrusted documents could trigger parser bugs)
- The Ollama API endpoint — assumed to be localhost

Running ATLAS exposed to the public internet without additional hardening (auth, reverse proxy, firewall) is not recommended.
