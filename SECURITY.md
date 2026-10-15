# Security policy

## Reporting a vulnerability

Please do not open a public issue for a suspected security vulnerability. Send
the details privately to the repository owner through GitHub so the issue can be
reviewed before disclosure.

Include the affected endpoint or component, reproduction steps, impact, and
any suggested mitigation. Do not include real API keys, personal documents, or
other sensitive data in a report.

## Deployment baseline

- Keep `.env`, uploaded documents, and local databases out of version control.
- Use a unique secret key and `DEBUG=False` in deployed environments.
- Restrict `ALLOWED_HOSTS` and configure HTTPS at the application or proxy layer.
- Rotate any credential that is accidentally exposed in logs or commits.
