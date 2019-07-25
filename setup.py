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

setup_requirements = ["pytest-runner", ]

dev_requirements = [
    "bumpversion>=0.5.3",
    "wheel>=0.33.1",
    "flake8>=3.7.7",
    "tox>=3.5.2",
    "coverage>=5.0a4",
    "Sphinx>=2.0.0b1",
    "twine>=1.13.0",
    "pytest>=4.3.0",
    "pytest-cov==2.6.1",
    "pytest-raises>=0.10",
    "pytest-runner>=4.4",
]

interactive_requirements = [
    "altair",
    "jupyterlab",
    "matplotlib",
]

requirements = [
    "beautifulsoup4>=4.7.1",
    "ffmpeg-python>=0.1.17",
    "fuzzywuzzy>=0.17.0",
    "nltk>=3.4.4",
    "pandas",
    "python-Levenshtein>=0.12.0",
    "requests>=2.21.0",
    "schedule>=0.6.0"
]

local_requirements = [
    "appdirs>=1.4.3"
]

google_cloud_requirements = [
    "firebase-admin>=2.16.0",
    "google-cloud-speech>=1.0.0",
    "google-cloud-storage>=1.14.0"
]

extra_requirements = {
    "test": test_requirements,
    "setup": setup_requirements,
    "dev": dev_requirements,
    "interactive": interactive_requirements,
    "local": local_requirements,
    "google-cloud": google_cloud_requirements,
    "all": [
        *requirements,
        *local_requirements,
        *google_cloud_requirements,
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
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Utilities"
    ],
    description="Tools used to run Council Data Project pipelines.",
    entry_points={
        "console_scripts": [
            "run_cdp_pipeline=cdptools.bin.run_cdp_pipeline:main",
        ],
    },
    install_requires=requirements,
    license="BSD-3-Clause",
    long_description=readme,
    include_package_data=True,
    keywords="Council Data Project Pipeline Tools",
    name="cdptools",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    extras_require=extra_requirements,
    url="https://github.com/JacksonMaxfield/cdptools",
    version="0.1.0",
    zip_safe=False,
)
