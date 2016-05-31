from setuptools import setup

setup(
    name = "nanosite",
    author = "Andrew Wang",
    url = "https://github.com/qema/nanosite",
    version = "0.1",
    packages = ["nanosite"],
    entry_points = {
        "console_scripts": [
            "nanosite = nanosite:main"
            ]
        }
)
