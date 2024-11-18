
# KubeZap

KubeZap is a command-line tool that simplifies the process of updating kubeconfig files for multiple Kubernetes clusters. It supports various platforms including Mac, Windows, and Linux.

## Features

- Automatic backup creation before updating kubeconfig
- Customizable number of backup files to keep
- Automatic rollback on failure
- Support for multiple cluster configurations
- Detailed merge information in verbose mode
- Cross-platform compatibility (Mac, Windows, Linux)

## Installation

You can install KubeZap using pip:

```
pip install kubezap
```

## Usage

```
kubezap [OPTIONS]
```

Options:
- `--kubeconfig KUBECONFIG`: Path to the kubeconfig file
- `--download-location DOWNLOAD_LOCATION`: Path to the download location for new configs
- `--conf-name CONF_NAME`: Pattern for config file names (default: config*.yaml)
- `-n NUMBER_OF_CONFIGS, --number-of-configs NUMBER_OF_CONFIGS`: Number of config files to process (default: 1)
- `-vv`: Enable verbose output
- `--backup BACKUP`: Number of backup files to keep (default: 5)
- `-v, --version`: Show program's version number and exit
- `-h, --help`: Show this help message and exit

## Environment Variables

- `KUBECONFIG_LOCATION`: Override the default kubeconfig location
- `DEFAULT_DOWNLOAD_LOCATION`: Set the default download location for new kubeconfig files

Note: Information about these environment variables is also available in the command-line help (use `kubezap --help` to view). The help output displays these variables with the same formatting as the command-line options for improved readability.

## Examples

1. Update kubeconfig with default settings:
   ```
   kubezap
   ```

2. Specify custom kubeconfig and download locations:
   ```
   kubezap --kubeconfig /path/to/kubeconfig --download-location /path/to/downloads
   ```

3. Process multiple config files and keep more backups:
   ```
   kubezap -n 3 --backup 10
   ```

4. Enable verbose output:
   ```
   kubezap -vv
   ```

## Building from source

To build KubeZap from source:

1. Clone the repository
2. Install the required dependencies:
   - For basic functionality: `pip install PyYAML`
   - For development (including testing and linting): `pip install -r requirements.txt`
3. Run `python setup.py install`

## Development

For development, you can install all dependencies including testing and linting tools:

```
pip install -r requirements.txt
```

This will install pytest for testing, flake8 for linting, and black for code formatting.

## Creating standalone executables

To create standalone executables for different platforms, you can use PyInstaller:

```
pyinstaller --onefile kubezap.py
```

This will create a single executable file in the `dist` directory.

## License

This project is licensed under the MIT License.
