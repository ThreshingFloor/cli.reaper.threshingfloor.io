# cli.reaper.threshingfloor.io
The CLI to reduce noisy lines from log files.

# Publish new version

- Update the setup.py to include the new version
- Ensure your pypi credentials are set
- Run the following commands

```
python setup.py sdist
twine upload dist/*
```

