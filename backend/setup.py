from setuptools import setup, find_packages

setup(
    name="minedu-backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
    ],
    python_requires=">=3.8",
)
