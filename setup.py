from pathlib import Path
import re

from setuptools import setup

root = Path(__file__).parent

init = (root / "enums.py").read_text("utf-8")

result = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', init, re.MULTILINE)

if result is None:
    raise RuntimeError("Failed to find version.")

version = result.group(1)

readme = (root / "README.rst").read_text("utf-8")


setup(
    name="enums.py",
    author="nekitdev",
    author_email="nekitdevofficial@gmail.com",
    url="https://github.com/nekitdev/enums.py",
    project_urls={"Issue tracker": "https://github.com/nekitdev/enums.py/issues"},
    version=version,
    py_modules=["enums", "test_enums"],
    license="MIT",
    description="Enhanced Enum Implementation for Python",
    long_description=readme,
    long_description_content_type="text/x-rst",
    include_package_data=True,
    extras_require={"test": ["coverage", "flake8", "pytest"]},
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Natural Language :: English",
        "Operating System :: OS Independent",
    ],
)
