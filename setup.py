"""
Setup configuration for openerb (Open Embodied Robot Brain) package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="openerb",
    version="0.1.0",
    author="OpenERB Project",
    description="Open Embodied Robot Brain - Self-Evolving Robot Control System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/openerb/openerb",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Robotics",
    ],
    python_requires=">=3.9",
    install_requires=[
        "python-dotenv>=0.19.0",
        "pydantic>=2.0.0",
        "requests>=2.31.0",
        "Pillow>=10.0.0",
        "numpy>=1.24.0",
        "sqlalchemy>=2.0.0",
        "RestrictedPython>=6.0.0",
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.1.0",
        "loguru>=0.7.0",
        "click>=8.0.0",
        "pyyaml>=6.0",
        "aiohttp>=3.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "openerb=openerb.core.bootstrap:cli",
        ],
    },
)
