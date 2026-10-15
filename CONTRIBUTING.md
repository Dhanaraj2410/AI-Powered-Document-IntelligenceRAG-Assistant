# Contributing

## Local checks

Create a virtual environment, install `requirements.txt`, and run:

```bash
python manage.py check
python -m pytest -q
```

Keep API keys in `.env` and never commit local databases, uploads, or generated
vector indexes. Include a migration whenever a model change requires one, and
avoid creating migrations for changes that affect no model schema. Update the
README or implementation notes when configuration or API behavior changes. Use
focused commit messages that describe one logical change.

## Pull requests

Work from a topic branch, keep commits focused, and include the validation
commands you ran in the pull request description. Changes affecting retrieval
quality should include the evaluation command and note the model/index used.
