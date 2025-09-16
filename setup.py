from setuptools import find_packages, setup

setup(
    name="microglia-pipeline",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
)
