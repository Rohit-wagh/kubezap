from setuptools import setup, find_packages

setup(
    name="kubezap",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "PyYAML",
        "argcomplete",
    ],
    entry_points={
        "console_scripts": [
            "kubezap=kubezap:main",
        ],
    },
    author="Rohit Wagh",
    author_email="waghrohit70@gmail.com",
    description="A tool to update kubeconfig files for multiple Kubernetes clusters",
    long_description=(
        "KubeZap is a command-line tool that simplifies the process of updating kubeconfig files "
        "for multiple Kubernetes clusters. It supports various platforms including Mac, Windows, "
        "and Linux. Features include automatic backup creation, keeping recent backups, "
        "and automatic rollback on failure."
    ),
    url="https://github.com/Rohit-wagh/kubezap",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)


