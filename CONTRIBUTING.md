# Contributing

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

### Get Started!

Ready to contribute? Here's how to set up `cdptools` for local development.

1. Fork the `cdptools` repo on GitHub.
2. Clone your fork locally:

```bash
$ git clone git@github.com:your_name_here/cdptools.git
```

3. Install the project in editable mode.
(It is also recommended to work in a virtualenv or anaconda environment):

```bash
$ cd cdptools/
$ pip install -e .[dev]
```

4. Create a branch for local development:

```bash
$ git checkout -b TYPE/short-description
```

Ex: FEATURE/read-tiff-files or BUGFIX/handle-file-not-found

Now you can make your changes locally.

5. When you're done making changes, check that your changes pass linting and
   tests, including testing other Python versions with tox:

```bash
$ tox
```

6. Commit your changes and push your branch to GitHub:

```bash
$ git add .
$ git commit -m "Resolves gh-###. Your detailed description of your changes."
$ git push origin TYPE/short-description
```

7. Submit a pull request through the GitHub website.

### Deploying

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed.
Then run:

```bash
$ bumpversion patch # possible: major / minor / patch
$ git push
$ git push --tags
```

Travis will then deploy to PyPI if tests pass.
