# Clean Python environment

The previously tracked `venv/` contained obsolete copies of cryptography,
OAuthlib and django-allauth. It is removed from the repository in this PR.
Git history is preserved. This source change does not delete or modify any
existing hosting environment, database, uploaded file or credential.

For local development or isolated staging, use Python 3.11 or 3.12 and create
a fresh environment from the reviewed requirements:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python manage.py test security_tests --settings=security_test_settings
```

Keep both `venv/` and `.venv/` out of Git. Do not activate the old tracked
environment or copy it to a host. Preserve any existing configuration privately;
never copy credentials into Git.

The above test command uses disposable test settings. Production migration and
deployment remain separate user-approved operations. Before such a release,
review existing allauth email/provider data and the actual production Python
version. Setuptools is updated in the follow-up build-toolchain PR. Its removal of
`pkg_resources` requires django-countries 9.1.0; address validation and
storage of country codes are covered by isolated tests.
