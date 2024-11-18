
# KubeZap

KubeZap is a command-line tool that simplifies the process of updating kubeconfig files for multiple Kubernetes clusters. It supports various platforms including Mac, Windows, and Linux.

## Features

- Merge new kubeconfig files into existing kubeconfig
- Automatic backup creation before updating kubeconfig
- Customizable number of backup files to keep
- Automatic rollback on failure
- Detailed merge information in verbose mode
- Diff output to show exact changes

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
- `--kubeconfig PATH`: Path to the kubeconfig file
- `--download-location PATH`: Path to the download location for new configs
- `--conf-name PATTERN`: Pattern for config file names (default: config*.yaml)
- `-n, --number-of-configs NUMBER`: Number of config files to process (default: 1)
- `-vv`: Enable verbose output
- `-v, --version`: Show the version number and exit
- `--backup NUMBER`: Number of backup files to keep (default: 5)
- `-d, --diff`: Show diff of changes

## Environment Variables

- `KUBECONFIG_LOCATION`: Override the default kubeconfig location
- `DEFAULT_DOWNLOAD_LOCATION`: Set the default download location for new kubeconfig files

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

4. Show diff of changes:
   ```
   kubezap -d
   ```

## Development

To set up the development environment:

1. Clone the repository
2. Install the required dependencies: `pip install -r requirements.txt`
3. Run tests: `pytest`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
