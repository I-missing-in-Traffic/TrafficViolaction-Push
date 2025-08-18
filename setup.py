from setuptools import setup, find_packages

setup(
    name="traffic-violation-reporter",
    version="1.0.0",
    description="台中市交通違規檢舉自動化工具",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "pillow>=10.0.0",
        "pytesseract>=0.3.10",
    ],
    extras_require={
        "api": ["fastapi>=0.100.0", "uvicorn>=0.23.0", "python-multipart>=0.0.6"],
    },
    python_requires=">=3.8",
)
