from setuptools import find_packages, setup

setup(
    name="alfa",
    version="0.0.1",
    packages=find_packages(),
    description="A minimalist platform for running trading strategies.",
    author="Mircea Avram",
    author_email="mavram@gmail.com",
    python_requires=">=3.12",
    install_requires=["dynaconf", "setuptools", "yfinance"],
    extras_require={
        "development": [
            "pytest",
            "pytest-cov",
            "black",
            "flake8",
        ]
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
