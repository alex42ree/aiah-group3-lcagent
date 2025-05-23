from setuptools import setup, find_packages

setup(
    name="langchain_react_agent",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "langchain-core>=0.1.0",
        "langserve>=0.0.10",
        "fastapi>=0.100.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "openai>=1.0.0",
        "requests>=2.31.0",
    ],
    python_requires=">=3.9",
    author="Your Name",
    author_email="your.email@example.com",
    description="A LangChain agent with React and Hono API integration",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 