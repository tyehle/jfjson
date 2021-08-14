import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jfjson",
    version="0.0.1",
    author="Tobin Yehle",
    author_email="tobin@yehle.us",
    description="Automatic json parsing and serialing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tyehle/jfjson",
    py_modules=["jfjson"],
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development",
    ],
)
