# Contributing

## Local checks

Create a virtual environment, install `requirements.txt`, and run:

```bash
python manage.py check
python -m pytest -q
```

Keep API keys in `.env` and never commit local databases, uploads, or generated
vector indexes. Use focused commit messages that describe one logical change.

