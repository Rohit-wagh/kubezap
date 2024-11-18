import os
from pathlib import Path


def get_kubeconfig_path(args):
    if args.kubeconfig:
        return Path(args.kubeconfig).expanduser()
    elif "KUBECONFIG" in os.environ:
        return Path(os.environ["KUBECONFIG"]).expanduser()
    else:
        raise ValueError("Kubeconfig file location not provided. Please specify using --kubeconfig or set KUBECONFIG environment variable.")


def get_download_location(args):
    if args.download_location:
        location = Path(args.download_location).expanduser()
    elif "DEFAULT_DOWNLOAD_LOCATION" in os.environ:
        location = Path(os.environ["DEFAULT_DOWNLOAD_LOCATION"]).expanduser()
    else:
        raise ValueError("Download location not provided. Please specify using --download-location or set DEFAULT_DOWNLOAD_LOCATION environment variable.")
    
    return location


def get_config_files(download_location, conf_name, num_configs):
    if conf_name:
        pattern = download_location / conf_name
        files = sorted(
            pattern.parent.glob(pattern.name), key=os.path.getmtime, reverse=True
        )
    else:
        files = sorted(
            list(download_location.glob('config*.yaml')) + list(download_location.glob('*-config.yaml')),
            key=os.path.getmtime, reverse=True
        )
    return files[:num_configs]

