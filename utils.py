import os
from pathlib import Path

def get_kubeconfig_path(args):
    if args.kubeconfig:
        return Path(args.kubeconfig).expanduser()
    elif 'KUBECONFIG_LOCATION' in os.environ:
        return Path(os.environ['KUBECONFIG_LOCATION']).expanduser()
    else:
        return Path.home() / '.kube' / 'config'

def get_download_location(args):
    if args.download_location:
        return Path(args.download_location).expanduser()
    elif 'DEFAULT_DOWNLOAD_LOCATION' in os.environ:
        return Path(os.environ['DEFAULT_DOWNLOAD_LOCATION']).expanduser()
    else:
        return Path.home() / '.kube'

def get_config_files(download_location, conf_name, num_configs):
    pattern = download_location / conf_name
    files = sorted(pattern.parent.glob(pattern.name), key=os.path.getmtime, reverse=True)
    return files[:num_configs]
