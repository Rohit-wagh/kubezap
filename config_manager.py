import yaml
import difflib

def merge_configs(existing_config, new_config):
    """
    Merge two kubeconfig configurations.

    Args:
        existing_config (dict): The existing kubeconfig.
        new_config (dict): The new kubeconfig to merge.

    Returns:
        dict: The merged kubeconfig.
    """
    print("Merging configs...")
    if not existing_config and not new_config:
        return {}

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
    if existing_clusters:
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
    if existing_contexts:
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
    if existing_users:
        existing_config['users'] = list(existing_users.values())

    # Update other top-level keys
    for key in new_config:
        if key not in ['clusters', 'contexts', 'users']:
            existing_config[key] = new_config[key]

    return existing_config

def update_kubeconfig(kubeconfig_path, new_config_files, max_backups, show_diff=False):
    from backup_manager import create_backup, manage_backups
    import shutil

    backup_path = create_backup(kubeconfig_path)
    
    try:
        with open(kubeconfig_path, 'r') as f:
            existing_config = yaml.safe_load(f)

        changes = []
        diff_output = []
        for new_config_file in new_config_files:
            with open(new_config_file, 'r') as f:
                new_config = yaml.safe_load(f)
            
            original_clusters = set(c['name'] for c in existing_config.get('clusters', []))
            original_contexts = set(c['name'] for c in existing_config.get('contexts', []))
            original_users = set(u['name'] for u in existing_config.get('users', []))
            
            updated_config = merge_configs(existing_config.copy(), new_config)
            
            new_clusters = set(c['name'] for c in updated_config.get('clusters', [])) - original_clusters
            new_contexts = set(c['name'] for c in updated_config.get('contexts', [])) - original_contexts
            new_users = set(u['name'] for u in updated_config.get('users', [])) - original_users
            
            if new_clusters or new_contexts or new_users or updated_config != existing_config:
                changes.append(f"Updated from {new_config_file}:")
                changes.append(f"  Added clusters: {', '.join(new_clusters) if new_clusters else 'None'}")
                changes.append(f"  Added contexts: {', '.join(new_contexts) if new_contexts else 'None'}")
                changes.append(f"  Added users: {', '.join(new_users) if new_users else 'None'}")

                if show_diff:
                    old_yaml = yaml.dump(existing_config, default_flow_style=False)
                    new_yaml = yaml.dump(updated_config, default_flow_style=False)
                    diff = list(difflib.unified_diff(old_yaml.splitlines(), new_yaml.splitlines(), fromfile='Old Config', tofile='New Config', lineterm=''))
                    diff_output.extend(diff)

                existing_config = updated_config

        if changes:
            with open(kubeconfig_path, 'w') as f:
                yaml.dump(existing_config, f)
            manage_backups(backup_path.parent, max_backups)
        else:
            # Remove the unnecessary backup if no changes were made
            backup_path.unlink()

        return changes, diff_output
    except Exception as e:
        print(f"Error updating kubeconfig: {e}")
        print("Rolling back to the previous version...")
        shutil.copy2(backup_path, kubeconfig_path)
        return [], []
