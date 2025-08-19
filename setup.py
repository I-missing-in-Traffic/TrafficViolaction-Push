from setuptools import setup, find_packages

setup(
    name="traffic-violation-reporter",
    version="1.1.0",
    description="台中市交通違規檢舉自動化工具",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="kaminzhi",
    author_email="kamin@kaminzhi.com",
    url="https://github.com/I-missing-in-Traffic/TrafficViolaction-Push"
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.32.4",
        "beautifulsoup4>=4.13.4",
        "pillow>=11.3.0",
        "pytesseract>=0.3.13",
        "pydantic>=2.11.7",
    ],
    extras_require={
        "api": ["fastapi>=0.116.1", "uvicorn>=0.35.0", "python-multipart>=0.0.20"],
        "dev": ["pytest>=7.0.0", "black>=23.0.0", "flake8>=6.0.0"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="traffic violation report automation taiwan taichung",
    license="MIT",
)
