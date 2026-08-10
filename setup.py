"""
视频自动化 VideoForge — 安装配置
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="videoforge",
    version="2.0.0",
    author="VideoForge Team",
    description="视频自动化工作流 — 选题→脚本→分镜→生成→发布，全流程自动化",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="#",  # GitHub 仓库地址，发布后替换
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": ["*.html", "*.css", "*.js", "*.json", "*.bat", "*.md"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Video",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "videoforge=app:main",
        ],
    },
)
