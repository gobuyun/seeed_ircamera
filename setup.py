# coding=utf-8

"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='seeed_python_ircamera',
    version='1.8.0',
    description='32 x 24 pixels IRCamera Application',
    long_description=long_description,
    long_description_content_type='text/markdown',

    # The project's main homepage.
    url='https://github.com/gobuyun/seeed_ircamera',
    entry_points = {
    'console_scripts': [
        'ircamera = seeed_python_ircamera:run'
    ]},
    # Author details
    author='gobuyun',
    author_email='874751353@qq.com',

    install_requires=[
        'PyQt5',
        'pyserial',
        'seeed-python-mlx90640'
    ],

    # Choose your license
    license='MIT',
    packages=find_packages(),
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Hardware',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    # What does your project relate to?
    keywords='seeed 32x24 IR sensor Application',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    py_modules=['seeed_python_ircamera'],
)