#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'appdirs>=1.4.3',
    'beautifulsoup4>=4.7.1',
    'ffmpeg-python>=0.1.17',
    'firebase-admin>=2.16.0',
    'fuzzywuzzy[speedup]>=0.17.0',
    'google-cloud-speech>=1.0.0',
    'requests>=2.21.0',
    'schedule>=0.6.0'
]

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', 'pytest-cov', 'pytest-raises', ]

extra_requirements = {
    'test': test_requirements,
    'setup': setup_requirements
}

setup(
    author="Jackson Maxfield Brown",
    author_email='jmaxfieldbrown@gmail.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="Tools used to run Council Data Project pipelines.",
    entry_points={
        'console_scripts': [
            'run_cdp_pipeline=cdptools.bin.run_cdp_pipeline:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='Council Data Project Tools',
    name='cdptools',
    packages=find_packages(include=['cdptools']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    extras_require=extra_requirements,
    url='https://github.com/JacksonMaxfield/cdptools',
    version='0.1.0',
    zip_safe=False,
)
