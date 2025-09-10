#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# 读取requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="lite-slurm",
    version="1.0.0",
    author="zheng",
    author_email="zheng.zheng.luck@gmail.com",
    description="A tmux-based task scheduling and monitoring tool",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/zz9tf/slurm-like-task-manager",
    project_urls={
        "Bug Reports": "https://github.com/zz9tf/slurm-like-task-manager/issues",
        "Source": "https://github.com/zz9tf/slurm-like-task-manager",
        "Documentation": "https://github.com/zz9tf/slurm-like-task-manager#readme",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
    install_requires=[
        "psutil>=5.8.0",
        "google-auth>=2.0.0",
        "google-auth-oauthlib>=0.5.0",
        "google-auth-httplib2>=0.1.0",
        "google-api-python-client>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
    },
    entry_points={
        "console_scripts": [
            "task=task_manager.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "task_manager": [
            "config/*.json",
            "templates/*.html",
        ],
    },
    zip_safe=False,
)
