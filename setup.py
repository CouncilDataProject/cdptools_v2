#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

test_requirements = [
    "codecov",
    "flake8",
    "pytest",
    "pytest-cov",
    "pytest-raises",
]

setup_requirements = [
    "pytest-runner",
]

dev_requirements = [
    "bumpversion>=0.5.3",
    "coverage>=5.0a4",
    "flake8>=3.7.7",
    "gitchangelog>=3.0.4",
    "ipython>=7.5.0",
    "m2r>=0.2.1",
    "pytest>=4.3.0",
    "pytest-cov==2.6.1",
    "pytest-raises>=0.10",
    "pytest-runner>=4.4",
    "Sphinx>=2.0.0b1",
    "sphinx_rtd_theme>=0.1.2",
    "tox>=3.5.2",
    "twine>=1.13.0",
    "wheel>=0.33.1",
]

interactive_requirements = [
    "altair",
    "jupyterlab",
    "matplotlib",
]

requirements = [
    "beautifulsoup4==4.8.0",
    "ffmpeg-python==0.2.0",
    "fuzzywuzzy==0.17.0",
    "nltk==3.4.5",
    "pandas==0.25.0",
    "python-Levenshtein==0.12.0",
    "requests[security]==2.22.0",
    "schedule==0.6.0",
    "setuptools>=44.0.0",
    "tika==1.19",
    "webvtt-py==0.4.3",
    "truecase==0.0.5"
]

extra_requirements = [
    "appdirs>=1.4.3"
]

seattle_requirements = [
    "cryptography>=2.8",
    "firebase-admin==2.17.0",
    "google-cloud-speech==1.2.0",
    "google-cloud-storage==1.17.0"
]

extra_requirements = {
    "test": test_requirements,
    "setup": setup_requirements,
    "dev": dev_requirements,
    "interactive": interactive_requirements,
    "extras": extra_requirements,
    "seattle": seattle_requirements,
    "all": [
        *requirements,
        *extra_requirements,
        *seattle_requirements,
        *test_requirements,
        *setup_requirements,
        *dev_requirements,
        *interactive_requirements
    ]
}

setup(
    author="Jackson Maxfield Brown, Nicholas Weber",
    author_email="jmaxfieldbrown@gmail.com, nmweber@uw.edu",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Utilities"
    ],
    description="Tools to interact with and deploy CouncilDataProject instances",
    entry_points={
        "console_scripts": [
            "run_cdp_pipeline=cdptools.bin.run_cdp_pipeline:main",
            "clone_db=cdptools.bin.clone_db:main",
            "process_single_event=cdptools.bin.process_single_event:main",
            "clone_file_store=cdptools.bin.clone_file_store:main"
        ],
    },
    install_requires=requirements,
    license="BSD-3-Clause",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    name="cdptools",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    extras_require=extra_requirements,
    url="https://github.com/CouncilDataProject/cdptools",
    version="2.0.5",
    zip_safe=False,
)
