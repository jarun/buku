from setuptools import setup
from pip.req import parse_requirements
from os import path
from codecs import open

with open("README.md", encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='buku',
    version='0.0.9',
    description='Powerful command-line bookmark manager. Your mini web!',
    long_description=long_description,
    url='https://github.com/jarun/Buku',
    author='Jarun',
    author_email='ovv@outlook.com',
    license='GPLv3',
    packages=['buku'],
    include_package_data=True,
    package_data={'auto-completion': ['bash/*', 'fish/*', 'zsh/*']},
    entry_points={
        'console_scripts': ['buku=buku.buku:entry_point']
    },
    install_requires=['beautifulsoup4>=4.4.1', 'cryptography>=1.3.2'],
    classifiers=['Topic :: Internet :: WWW/HTTP :: Indexing/Search',
                 'Programming Language :: Python :: 3.3',
                 'Operating System :: POSIX :: Linux',
                 'Natural Language :: English',
                 'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                 'Development Status :: 5 - Production/Stable'],
)
