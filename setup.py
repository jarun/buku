#!/usr/bin/env python3

import os
import re
import shutil

from setuptools import find_packages, setup

if os.path.isfile('buku'):
    shutil.copyfile('buku', 'buku.py')

with open('buku.py', encoding='utf-8') as f:
    version = re.search('__version__ = \'([^\']+)\'', f.read()).group(1)  # type: ignore

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

tests_require = [
    'attrs>=17.4.0',
    'beautifulsoup4>=4.6.0',
    'Click>=7.0',
    'flake8>=3.4.1',
    'hypothesis>=6.0.0',
    'mypy-extensions==0.4.1',
    'py>=1.5.0',
    'pylint>=1.7.2',
    'pytest-cov',
    'pytest-recording>=0.12.1',
    'pytest>=6.2.1',
    'PyYAML>=4.2b1',
    'setuptools>=41.0.1',
    'vcrpy>=1.13.0',
    'lxml',
    'flask_babel',
]


server_require = [
    "arrow>=1.2.2",
    "Flask-Admin>=1.6.1",
    "Flask-API>=3.0.post1",
    "Flask-Bootstrap>=3.3.7.1",
    "flask-paginate>=2022.1.8",
    "Flask-WTF>=1.0.1",
    "Flask>=2.2.2,<2.3",
    "werkzeug<2.4",
]
reverse_proxy = " ".join(
    [
        "flask-reverse-proxy-fix",
        "@",
        "https://github.com/rachmadaniHaryono/flask-reverse-proxy-fix/archive/refs/tags/v0.2.3.zip",
    ]
)
install_requires = [
    'beautifulsoup4>=4.4.1',
    'certifi',
    'cryptography>=1.2.3',
    'html5lib>=1.0.1',
    'urllib3>=1.23,<2',
    'pyreadline3; sys_platform == \'win32\'',
    'colorama>=0.4.6; sys_platform == \'win32\'',
]

setup(
    name='buku',
    version=version,
    description='Bookmark manager like a text-based mini-web.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Arun Prakash Jana',
    author_email='engineerarun@gmail.com',
    url='https://github.com/jarun/buku',
    license='GPLv3',
    python_requires='>=3.8',  # requires pip>=9.0.0
    platforms=['any'],
    py_modules=['buku'],
    install_requires=install_requires,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    entry_points={
        'console_scripts': ['buku=buku:main', 'bukuserver=bukuserver.server:cli']
    },
    extras_require={
        "tests": tests_require + server_require + [reverse_proxy],
        "server": server_require,
        "reverse_proxy": [reverse_proxy],
        "docs": [
            "myst-parser>=0.17.0",
            "sphinx-rtd-theme>=1.0.0",
            "sphinx-autobuild>=2021.3.14",
        ],
        "packaging": ["twine>=1.11.0"],
    },
    test_suite='tests',
    tests_require=tests_require,
    keywords='cli bookmarks tag utility',
    project_urls={
        "Documentation": "https://buku.readthedocs.io/en/latest",
        "Funding": "https://github.com/sponsors/jarun",
        "Source": "https://github.com/jarun/buku",
        "Tracker": "https://github.com/jarun/buku/issues",
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Utilities'
    ]
)
