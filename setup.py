# setup.py
from setuptools import setup, find_packages

setup(
    name='alfa',
    version='0.1.1',
    packages=find_packages(),
    description='A minimalist platform for playing with trading strategies.',
    author='Mircea Avram',
    author_email='mavram@gmail.com',
    install_requires=[
        'yfinance',
        'setuptools'
    ],
    include_package_data=False,

    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ]
)
