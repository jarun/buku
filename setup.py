#!/usr/bin/env python3

import re
import sys

from setuptools import setup, find_packages

if sys.version_info < (3, 4):
    print('ERROR: Buku requires at least Python 3.4 to run.')
    sys.exit(1)

with open('buku.py', encoding='utf-8') as f:
    version = re.search('__version__ = \'([^\']+)\'', f.read()).group(1)

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

tests_require = [
    'pytest-cov', 'hypothesis>=3.7.0', 'py>=1.5.0',
    'beautifulsoup4>=4.6.0', 'flake8>=3.4.1', 'pylint>=1.7.2', 'PyYAML>=3.12'
]
if sys.version_info.major == 3 and sys.version_info.minor == 6:
    tests_require.append('pytest>=3.4.2,!=3.5.0,!=3.5.1,!=3.6.0')
else:
    tests_require.append('pytest>=3.4.2')


server_require = [
    'arrow>=0.12.1',
    'click>=6.7',
    'Flask-API>=0.6.9',
    'Flask-Bootstrap>=3.3.7.1',
    'flask-paginate>=0.5.1',
    'Flask-WTF>=0.14.2',
    'Flask>=0.12',
    'requests>=2.18.4',
    'Werkzeug>=0.11.15',
]

setup(
    name='buku',
    version=version,
    description='Bookmark manager like a text-based mini-web.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Arun Prakash Jana',
    author_email='engineerarun@gmail.com',
    url='https://github.com/jarun/Buku',
    license='GPLv3',
    platforms=['any'],
    py_modules=['buku'],
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': ['buku=buku:main', 'bukuserver=bukuserver.server:cli']
    },
    extras_require={
        'HTTP': ['urllib3'],
        'CRYPTO': ['cryptography'],
        'HTML': ['beautifulsoup4'],
        'tests': tests_require,
        'server': server_require,
        'packaging': ['twine>=1.11.0']
    },
    test_suite='tests',
    tests_require=tests_require,
    keywords='cli bookmarks tag utility',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Utilities'
    ]
)
