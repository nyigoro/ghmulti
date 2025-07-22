from setuptools import setup

setup(
    name="ghmulti",
    version="0.1",
    packages=["ghmulti", "cli"],
    install_requires=["click"],
    entry_points={
        "console_scripts": [
            "ghmulti=ghmulti.__main__:cli",
        ],
    },
)
