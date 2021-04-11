from setuptools import find_packages, setup

inst_reqs = [
    "requests",
    # "cachetools",
    # "click",
    # "beautifulsoup4",

]

extra_reqs = {
    "test": ["pytest", "pytest-cov", "pytest-mock", "mypy", "flake8"],
}


setup(
    name="Lightricks Crawler",
    version="0.0.1",
    description=u"Ariel's Crawler for Lightricks",
    python_requires=">=3.8",
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.8",
    ],
    packages=find_packages(exclude=["stack*", "tests*"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
    author_email='arielzerahia@gmail.com',
    author='Ariel Zerahia'

)
