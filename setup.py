# setup.py
from setuptools import setup, find_packages

setup(
    name='alfa',
    version='0.1.1',
    packages=find_packages(),
    description='A minimialist trading package.',
    author='Mircea Avram',
    author_email='mavram@gmail.com',
    install_requires=[
        'pandas'
    ],
    include_package_data=False,

    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ]
)
