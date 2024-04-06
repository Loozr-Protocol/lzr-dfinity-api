from setuptools import find_packages, setup


def read(f):
    with open(f, "r", encoding="utf-8") as file:
        return file.read()


setup(
    name="lzr-dfinityapi",
    version="0.1.3",
    url="https://github.com/your-name/your_library",
    license="MIT",
    author="Confidence Yobo",
    author_email="confiyobo@gmail.com",
    description="Loozr Dfinity API.",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests*"]),
    include_package_data=True,
    install_requires=["django>=3.0", 'backports.zoneinfo;python_version<"3.9"'],
    python_requires=">=3.6",
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
)
