
# KubeZap

KubeZap is a command-line tool that simplifies the process of updating kubeconfig files for multiple Kubernetes clusters. It supports various platforms including Mac, Windows, and Linux.

## Features

- Automatic backup creation before updating kubeconfig
- Keeps 10 most recent backups
- Automatic rollback on failure
- Support for multiple cluster configurations
- Cross-platform compatibility (Mac, Windows, Linux)

## Installation

You can install KubeZap using pip:

```
pip install kubezap
```

## Usage

```
kubezap [--kubeconfig KUBECONFIG] [--download-location DOWNLOAD_LOCATION] [--conf-name CONF_NAME] [-n NUMBER_OF_CONFIGS]
```

Options:
- `--kubeconfig`: Path to the kubeconfig file (default: ~/.kube/config)
- `--download-location`: Path to the download location for new configs (default: ~/.kube/)
- `--conf-name`: Pattern for config file names (default: config*.yaml)
- `-n, --number-of-configs`: Number of config files to process (default: 1)

## Environment Variables

- `KUBECONFIG_LOCATION`: Override the default kubeconfig location
- `DEFAULT_DOWNLOAD_LOCATION`: Set the default download location for new kubeconfig files

## Building from source

To build KubeZap from source:

1. Clone the repository
2. Install the required dependencies: `pip install -r requirements.txt`
3. Run `python setup.py install`

## Creating standalone executables

To create standalone executables for different platforms, you can use PyInstaller:

```
pyinstaller --onefile kubezap.py
```

This will create a single executable file in the `dist` directory.

## License

This project is licensed under the MIT License.
