from setuptools import setup, find_packages

REQUIRES = [
    "psutil"
]

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="pytop",
    version="1.0.0",
    author="Jason Fitch",
    author_email="jasonpfitch@gmail.com",
    description="System Resource Monitor in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jasonpfi/bpytop",
    python_requires='>=3.6',
    install_requires=REQUIRES,
    packages=find_packages()
)
