from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="pycode-cli",
    version="0.1.0",
    author="CloudClaw",
    description="轻量级 Python Agent CLI — 让 AI 帮你写代码",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/allinaiianilla/test",
    packages=find_packages(),
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "pycode=pycode.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
