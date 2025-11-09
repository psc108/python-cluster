"""Setup configuration for Python clustering software"""
from setuptools import setup, find_packages

setup(
    name="python-cluster",
    version="1.0.0",
    description="Distributed clustering software system",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "asyncio>=3.4.3",
        "aiohttp>=3.8.6",
        "pydantic>=2.5.0",
        "pytest>=7.4.3",
        "pytest-asyncio>=0.21.1",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "cluster-node=src.main:main",
        ],
    },
)