from setuptools import setup

setup(
    name = "nanosite",
    author = "Andrew Wang",
    author_email = "azw7@cornell.edu",
    url = "https://github.com/qema/nanosite",
    version = "0.1.3",
    packages = ["nanosite"],
    install_requires = ["markdown"],
    entry_points = {
        "console_scripts": [
            "nanosite = nanosite:main"
            ]
        }
)
