from setuptools import setup

setup(
    name = "nanosite",
    author = "Andrew Wang",
    author_email = "azw7@cornell.edu",
    url = "https://github.com/qema/nanosite",
    description = "Speedy static site generator in Python.",
    version = "0.1.9",
    packages = ["nanosite"],
    install_requires = ["markdown"],
    entry_points = {
        "console_scripts": [
            "nanosite = nanosite:main"
            ]
        }
)
