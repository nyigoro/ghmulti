from setuptools import find_packages
from setuptools import setup

setup(
    name="ghmulti",
    version="0.1.0",
    packages=find_packages(exclude=("tests", "vscode-extension", "vscode-extension.*")),
    python_requires=">=3.10",
    install_requires=[
        "click>=8.1",
        "inquirer>=3.4",
        "keyring>=25.0",
        "requests>=2.31",
    ],
    extras_require={
        "dev": ["pytest>=8.0"],
    },
    entry_points={
        "console_scripts": [
            "ghmulti=cli.commands.__main__:cli",
        ],
    },
)
