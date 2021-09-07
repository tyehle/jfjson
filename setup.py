import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jfjson",
    version="0.0.3",
    author="Tobin Yehle",
    author_email="tobin@yehle.us",
    description="Automatic json parsing and serialing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tyehle/jfjson",
    packages=["jfjson"],
    package_dir={"": "src"},
    package_data={"jfjson": ["py.typed"]},
    install_requires=[],
    classifiers=[
        "Development Status :: 4 - Beta",

        "License :: OSI Approved :: MIT License",

        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",

        "Operating System :: OS Independent",

        "Topic :: Software Development",

        "Intended Audience :: Developers",

        "Typing :: Typed",
    ],
)
