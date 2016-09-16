from setuptools import setup
from pip.req import parse_requirements
from os import path
from codecs import open

setup(
    name='buku',
    version='0.0.5',
    description='Powerful command-line bookmark manager. Your mini web!',
    url='https://github.com/jarun/Buku',
    author='Ovv',
    author_email='ovv@outlook.com',
    license='GPLv3',
    packages=['buku', 'tests', 'auto-completion'],
    zip_safe=False,
    include_package_data=True,
    package_data={'tests': ['ci-test-wrapper'],
                  'auto-completion': ['bash/*', 'fish/*', 'zsh/*']},
    entry_points={
        'console_scripts': ['buku=buku.buku:entry_point']
    },
    install_requires=['beautifulsoup4>=4.4.1', 'cryptography>=1.3.2'],
)