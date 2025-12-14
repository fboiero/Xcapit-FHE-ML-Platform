# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

### How to Report

Send an email to: **security@xcapit.com**

Include the following information:
- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting)
- Full paths of source file(s) related to the issue
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### Response Timeline

- **Initial Response:** Within 48 hours
- **Status Update:** Within 5 business days
- **Resolution Target:** Within 90 days (depending on complexity)

### Disclosure Policy

- We follow coordinated disclosure
- Security advisories will be published after fixes are released
- Credit will be given to reporters (unless anonymity is requested)

## Security Best Practices

### For Users

1. **API Keys:** Never commit API keys to version control
2. **FHE Keys:** Store encryption keys securely, never in logs
3. **Dependencies:** Keep all dependencies up to date
4. **Access Control:** Use principle of least privilege

### For Contributors

1. **Input Validation:** Validate all user inputs
2. **Dependencies:** Use `pip-audit` to check for vulnerabilities
3. **Secrets:** Use environment variables for sensitive data
4. **Code Review:** All PRs require security review

## Smart Contract Security

The smart contracts in `/contracts/` have been audited. See `docs/SECURITY_AUDIT_REPORT.md` for details.

Key security measures:
- ReentrancyGuard on all external calls
- Access control with Ownable2Step
- Input validation with custom errors
- Pull-over-push pattern for payments
