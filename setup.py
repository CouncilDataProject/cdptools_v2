#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

setup_requirements = [
    "pytest-runner>=5.2",
]

test_requirements = [
    "black>=19.10b0",
    "codecov>=2.1.4",
    "flake8>=3.8.3",
    "flake8-debugger>=3.2.1",
    "pytest>=5.4.3",
    "pytest-cov>=2.9.0",
    "pytest-raises>=0.11",
]

dev_requirements = [
    *setup_requirements,
    *test_requirements,
    "bumpversion>=0.6.0",
    "coverage>=5.1",
    "gitchangelog>=3.0.4",
    "ipython>=7.15.0",
    "m2r>=0.2.1",
    "pytest-runner>=5.2",
    "Sphinx>=2.0.0b1,<3",
    "sphinx_rtd_theme>=0.4.3",
    "tox>=3.15.2",
    "twine>=3.1.1",
    "wheel>=0.34.2",
]

requirements = [
    "beautifulsoup4>=4.9.1",
    "bokeh>=2.1.0",
    "botocore==1.15.32",
    "boto3==1.12.32",
    "cloudpickle>=1.4.0",
    "dask[bag]>=2.19.0",
    "dask_cloudprovider==0.3.0",
    "distributed>=2.19.0",
    "graphviz>=0.14",
    "ffmpeg-python>=0.2.0",
    "rapidfuzz>=0.9.1",
    "nltk>=3.5",
    "pandas>=1.0.4",
    "prefect[viz]>=0.12.1",
    "pyarrow>=0.17.1",
    "requests[security]>=2.23.0",
    "schedule>=0.6.0",
    "setuptools>=44.0.0",
    "tika>=1.24",
    "webvtt-py>=0.4.5",
    "truecase>=0.0.9",
]

extra_requirements = [
    "appdirs>=1.4.3",
]

seattle_requirements = [
    "cryptography>=2.9.2",
    "firebase-admin>=4.3.0",
    "google-cloud-speech>=1.3.2",
    "google-cloud-storage>=1.28.1",
]

extra_requirements = {
    "test": test_requirements,
    "setup": setup_requirements,
    "dev": dev_requirements,
    "extras": extra_requirements,
    "seattle": seattle_requirements,
    "all": [
        *requirements,
        *extra_requirements,
        *seattle_requirements,
        *test_requirements,
        *setup_requirements,
        *dev_requirements,
    ]
}

setup(
    author="Jackson Maxfield Brown, To Huynh, Isaac Na, Nicholas Weber",
    author_email="jmaxfieldbrown@gmail.com, nmweber@uw.edu",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
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
    python_requires=">=3.7",
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    extras_require=extra_requirements,
    url="https://github.com/CouncilDataProject/cdptools",
    version="2.0.5",
    zip_safe=False,
)
