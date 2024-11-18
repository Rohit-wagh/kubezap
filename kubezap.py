import os
import argparse
import yaml
from pathlib import Path
import glob
import shutil
from datetime import datetime
import textwrap

__version__ = "1.0.0"

class CustomFormatter(argparse.HelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, max_help_position=40, width=100)

    def _format_action(self, action):
        if action.help is not None:
            help_text = self._expand_help(action)
            if action.default != argparse.SUPPRESS:
                help_text += f" (default: {action.default})"
            help_lines = textwrap.wrap(help_text, 80)
            help_text = '\n'.join(help_lines)
        else:
            help_text = ''

        if action.option_strings:
            option_string = ', '.join(action.option_strings)
            option_string = f'{option_string:<35}'
        else:
            option_string = ''

        return f"  {option_string}{help_text}\n\n"

    def _format_usage(self, usage, actions, groups, prefix):
        return super()._format_usage(usage, actions, groups, prefix) + '\n'

    def _split_lines(self, text, width):
        return text.splitlines()

    def _format_env_var(self, var, description):
        var_string = f'{var:<35}'
        desc_lines = textwrap.wrap(description, 60)
        desc_text = '\n'.join(desc_lines)
        return f"  {var_string}{desc_text}\n\n"

    def format_help(self):
        help = super().format_help()
        env_vars = "\n\nEnvironment Variables:\n\n"
        env_vars += self._format_env_var("KUBECONFIG_LOCATION", "Override the default kubeconfig location")
        env_vars += self._format_env_var("DEFAULT_DOWNLOAD_LOCATION", "Set the default download location for new kubeconfig files")
        return f"{help}{env_vars}"

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

def merge_configs(existing_config, new_config):
    print("Merging configs...")
    # Merge clusters
    existing_clusters = {cluster['name']: cluster for cluster in existing_config.get('clusters', [])}
    for new_cluster in new_config.get('clusters', []):
        if new_cluster['name'] in existing_clusters:
            print(f"Updating existing cluster: {new_cluster['name']}")
            # Update existing cluster
            for key, value in new_cluster['cluster'].items():
                existing_clusters[new_cluster['name']]['cluster'][key] = value
        else:
            print(f"Adding new cluster: {new_cluster['name']}")
            # Add new cluster
            existing_clusters[new_cluster['name']] = new_cluster
    existing_config['clusters'] = list(existing_clusters.values())

    # Merge contexts
    existing_contexts = {context['name']: context for context in existing_config.get('contexts', [])}
    for new_context in new_config.get('contexts', []):
        if new_context['name'] in existing_contexts:
            print(f"Updating existing context: {new_context['name']}")
            # Update existing context
            for key, value in new_context['context'].items():
                existing_contexts[new_context['name']]['context'][key] = value
        else:
            print(f"Adding new context: {new_context['name']}")
            # Add new context
            existing_contexts[new_context['name']] = new_context
    existing_config['contexts'] = list(existing_contexts.values())

    # Merge users
    existing_users = {user['name']: user for user in existing_config.get('users', [])}
    for new_user in new_config.get('users', []):
        if new_user['name'] in existing_users:
            print(f"Updating existing user: {new_user['name']}")
            # Update existing user
            for key, value in new_user['user'].items():
                existing_users[new_user['name']]['user'][key] = value
        else:
            print(f"Adding new user: {new_user['name']}")
            # Add new user
            existing_users[new_user['name']] = new_user
    existing_config['users'] = list(existing_users.values())

    # Update other top-level keys
    for key in new_config:
        if key not in ['clusters', 'contexts', 'users']:
            existing_config[key] = new_config[key]

    return existing_config

def create_backup(kubeconfig_path):
    backup_dir = kubeconfig_path.parent / 'kubezap_backups'
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    backup_path = backup_dir / f"kubeconfig_backup_{timestamp}"
    shutil.copy2(kubeconfig_path, backup_path)
    return backup_path

def manage_backups(backup_dir, max_backups=10):
    backups = sorted(backup_dir.glob('kubeconfig_backup_*'), key=os.path.getmtime, reverse=True)
    for old_backup in backups[max_backups:]:
        old_backup.unlink()

def update_kubeconfig(kubeconfig_path, new_config_files, max_backups):
    backup_path = create_backup(kubeconfig_path)
    
    try:
        with open(kubeconfig_path, 'r') as f:
            existing_config = yaml.safe_load(f)

        changes = []
        for new_config_file in new_config_files:
            with open(new_config_file, 'r') as f:
                new_config = yaml.safe_load(f)
            
            original_clusters = set(c['name'] for c in existing_config.get('clusters', []))
            original_contexts = set(c['name'] for c in existing_config.get('contexts', []))
            original_users = set(u['name'] for u in existing_config.get('users', []))
            
            existing_config = merge_configs(existing_config, new_config)
            
            new_clusters = set(c['name'] for c in existing_config.get('clusters', [])) - original_clusters
            new_contexts = set(c['name'] for c in existing_config.get('contexts', [])) - original_contexts
            new_users = set(u['name'] for u in existing_config.get('users', [])) - original_users
            
            changes.append(f"Updated from {new_config_file}:")
            changes.append(f"  Added clusters: {', '.join(new_clusters) if new_clusters else 'None'}")
            changes.append(f"  Added contexts: {', '.join(new_contexts) if new_contexts else 'None'}")
            changes.append(f"  Added users: {', '.join(new_users) if new_users else 'None'}")

        with open(kubeconfig_path, 'w') as f:
            yaml.dump(existing_config, f)

        manage_backups(backup_path.parent, max_backups)
        return changes
    except Exception as e:
        print(f"Error updating kubeconfig: {e}")
        print("Rolling back to the previous version...")
        shutil.copy2(backup_path, kubeconfig_path)
        return []

def main():
    description = '''
    KubeZap: A tool to update kubeconfig with new configurations.

    This tool allows you to merge new kubeconfig files into your existing kubeconfig,
    while maintaining backups and providing detailed information about the changes made.

    Features:
    - Automatic backup creation
    - Customizable number of backup files to keep
    - Automatic rollback on failure
    - Detailed merge information in verbose mode
    '''

    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=CustomFormatter
    )
    
    parser.add_argument('--kubeconfig', help='Path to the kubeconfig file')
    parser.add_argument('--download-location', help='Path to the download location for new configs')
    parser.add_argument('--conf-name', default='config*', help='Pattern for config file names')
    parser.add_argument('-n', '--number-of-configs', type=int, default=1, 
                        help='Number of config files to process')
    parser.add_argument('-vv', action='store_true', help='Enable verbose output')
    parser.add_argument('-v', '--version', action='version', 
                        version=f'KubeZap v{__version__}')
    parser.add_argument('--backup', type=int, default=5, 
                        help='Number of backup files to keep')
    
    args = parser.parse_args()

    if args.vv:
        print("Features:")
        print("- Automatic backup creation")
        print(f"- Keeps {args.backup} most recent backups")
        print("- Automatic rollback on failure")

    kubeconfig_path = get_kubeconfig_path(args)
    download_location = get_download_location(args)
    
    if args.vv:
        print(f"\nUsing kubeconfig: {kubeconfig_path}")
        print(f"Looking for new configs in: {download_location}")
    
    new_config_files = get_config_files(download_location, args.conf_name, args.number_of_configs)
    
    if not new_config_files:
        print(f"No matching config files found in {download_location}")
        return

    if args.vv:
        print("\nUpdating kubeconfig...")
    changes = update_kubeconfig(kubeconfig_path, new_config_files, args.backup)

    if changes:
        print("Changes made:")
        for change in changes:
            print(f"- {change}")
        if args.vv:
            print(f"\nBackup created in: {kubeconfig_path.parent / 'kubezap_backups'}")
    else:
        print("No changes were made. Possible error occurred and changes were rolled back.")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
        print("For more information, run with the -vv flag.")
