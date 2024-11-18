import yaml
import difflib
import yamale

import tempfile

def validate_kubeconfig(config_path):
    schema_content = '''
apiVersion: str()
kind: str()
clusters: list(include('cluster'))
contexts: list(include('context'), required=False)
users: list(include('user'), required=False)
current-context: str(required=False)
preferences: map(required=False)

---
cluster:
  name: str()
  cluster: map()

---
context:
  name: str()
  context: map()

---
user:
  name: str()
  user: map()
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_schema_file:
        temp_schema_file.write(schema_content)
        temp_schema_file.flush()
        schema = yamale.make_schema(temp_schema_file.name)

    data = yamale.make_data(config_path)
    try:
        yamale.validate(schema, data)
        return True, None
    except ValueError as e:
        return False, str(e)
    finally:
        import os
        os.unlink(temp_schema_file.name)

import logging

logger = logging.getLogger(__name__)

def update_kubeconfig(kubeconfig_path, new_config_files, max_backups, show_diff=False, dry_run=False):
    from backup_manager import create_backup, manage_backups
    import shutil

    if not dry_run:
        backup_path = create_backup(kubeconfig_path)
    
    try:
        # Validate the existing kubeconfig
        is_valid, error = validate_kubeconfig(kubeconfig_path)
        if not is_valid:
            raise ValueError(f"Invalid existing kubeconfig: {error}")

        with open(kubeconfig_path, 'r') as f:
            existing_config = yaml.safe_load(f)

        logger.debug(f"Existing config: {existing_config}")

        changes = []
        diff_output = []
        for new_config_file in new_config_files:
            # Validate the new config file
            is_valid, error = validate_kubeconfig(new_config_file)
            if not is_valid:
                raise ValueError(f"Invalid new config file {new_config_file}: {error}")

            with open(new_config_file, 'r') as f:
                new_config = yaml.safe_load(f)
            
            logger.debug(f"New config from {new_config_file}: {new_config}")

            original_clusters = set(c['name'] for c in existing_config.get('clusters', []))
            original_contexts = set(c['name'] for c in existing_config.get('contexts', []))
            original_users = set(u['name'] for u in existing_config.get('users', []))
            
            updated_config = merge_configs(existing_config.copy(), new_config)
            
            logger.debug(f"Updated config after merge: {updated_config}")

            new_clusters = set(c['name'] for c in updated_config.get('clusters', [])) - original_clusters
            new_contexts = set(c['name'] for c in updated_config.get('contexts', [])) - original_contexts
            new_users = set(u['name'] for u in updated_config.get('users', [])) - original_users
            
            logger.debug(f"New clusters: {new_clusters}")
            logger.debug(f"New contexts: {new_contexts}")
            logger.debug(f"New users: {new_users}")

            if new_clusters or new_contexts or new_users or updated_config != existing_config:
                changes.append(f"Updated from {new_config_file}:")
                for cluster in new_clusters:
                    changes.append(f"  Added cluster: {cluster}")
                for context in new_contexts:
                    changes.append(f"  Added context: {context}")
                for user in new_users:
                    changes.append(f"  Added user: {user}")
                if 'current-context' in new_config and new_config['current-context'] != existing_config.get('current-context'):
                    changes.append(f"  Updated current-context: {new_config['current-context']}")
                
                if show_diff:
                    diff = difflib.unified_diff(
                        yaml.dump(existing_config, default_flow_style=False).splitlines(),
                        yaml.dump(updated_config, default_flow_style=False).splitlines(),
                        fromfile='Original',
                        tofile='Updated',
                        lineterm=''
                    )
                    diff_output.extend(list(diff))
                
                existing_config = updated_config

        if changes and not dry_run:
            with open(kubeconfig_path, 'w') as f:
                yaml.dump(existing_config, f, default_flow_style=False)
            
            manage_backups(kubeconfig_path, max_backups)
            logger.info(f"Kubeconfig updated successfully. Backup created at {backup_path}")
        elif changes and dry_run:
            logger.info("Dry run: Changes would be made to the kubeconfig.")
        else:
            logger.info("No changes to be made to the kubeconfig.")
            if not dry_run and 'backup_path' in locals() and backup_path.exists():
                backup_path.unlink()
    
        return changes, diff_output
    except Exception as e:
        logger.error(f"Error updating kubeconfig: {e}")
        if not dry_run and 'backup_path' in locals():
            logger.info("Rolling back to the previous version...")
            shutil.copy2(backup_path, kubeconfig_path)
        return [], []

def merge_configs(existing_config, new_config):
    for key in ['clusters', 'contexts', 'users']:
        existing_items = {item['name']: item for item in existing_config.get(key, [])}
        for new_item in new_config.get(key, []):
            existing_items[new_item['name']] = new_item
        existing_config[key] = list(existing_items.values())
    
    # Add or update current-context if present in new_config
    if 'current-context' in new_config:
        existing_config['current-context'] = new_config['current-context']
    
    logger.debug(f"Merged config: {existing_config}")
    return existing_config



