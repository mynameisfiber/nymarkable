from setuptools import setup, find_packages  # type: ignore

with open("README.md") as f:
    long_description = f.read()

setup(
    name="nymarkable",
    version="0.5.0",
    author="Micha Gorelick",
    author_email="mynameisfiber@gmail.com",
    url="https://github.com/mynameisfiber/nymarkable/",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "selenium==4.1.3",
        "pypdf2==1.26.0",
        "click==8.0.3",
        "requests==2.26.0",
    ],
    entry_points={
        "console_scripts": [
            "nymarkable = nymarkable:cli",
        ],
    },
)
