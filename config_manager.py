import yaml
import difflib
import yamale

import tempfile


def validate_kubeconfig(config_path):
    schema_content = """
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
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as temp_schema_file:
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


def update_kubeconfig(
    kubeconfig_path, new_config, max_backups, show_diff=False, dry_run=False
):
    from backup_manager import create_backup, manage_backups
    import shutil

    changes = []
    diff_output = []
    backup_path = None

    logger.info(f"Running in {'dry run' if dry_run else 'normal'} mode")

    try:
        # Validate the existing kubeconfig
        is_valid, error = validate_kubeconfig(kubeconfig_path)
        if not is_valid:
            raise ValueError(f"Invalid existing kubeconfig: {error}")

        with open(kubeconfig_path, "r") as f:
            existing_config = yaml.safe_load(f)

        logger.debug(f"Existing config: {existing_config}")

        # Get the cluster name from the new config
        new_cluster_name = new_config.get("clusters", [{}])[0].get(
            "name", "Unknown Cluster"
        )

        # Check if the cluster already exists in the kubeconfig
        existing_cluster = next(
            (
                c
                for c in existing_config.get("clusters", [])
                if c["name"] == new_cluster_name
            ),
            None,
        )

        updated_config = merge_configs(existing_config.copy(), new_config)

        if existing_cluster:
            if updated_config != existing_config:
                changes.append(f"Updated cluster {new_cluster_name}")
        else:
            changes.append(f"Added new cluster {new_cluster_name}")

        logger.debug(f"Updated config after merge: {updated_config}")

        if changes:
            new_clusters = [
                c
                for c in updated_config.get("clusters", [])
                if c["name"] == new_cluster_name
            ]
            new_contexts = [
                c
                for c in updated_config.get("contexts", [])
                if new_cluster_name in c.get("context", {}).values()
            ]
            new_users = [
                u
                for u in updated_config.get("users", [])
                if u["name"]
                in [ctx.get("context", {}).get("user") for ctx in new_contexts]
            ]

            for cluster in new_clusters:
                changes.append(f"  Updated cluster: {cluster['name']}")
                # Print detailed cluster changes
                old_cluster = next(
                    (
                        c
                        for c in existing_config.get("clusters", [])
                        if c["name"] == cluster["name"]
                    ),
                    {},
                )
                for key, value in cluster.get("cluster", {}).items():
                    if (
                        key not in old_cluster.get("cluster", {})
                        or old_cluster["cluster"][key] != value
                    ):
                        changes.append(f"    {key}: {value}")
            for context in new_contexts:
                changes.append(f"  Updated context: {context['name']}")
            for user in new_users:
                changes.append(f"  Updated user: {user['name']}")
            if "current-context" in new_config and new_config[
                "current-context"
            ] != existing_config.get("current-context"):
                changes.append(
                    f"  Updated current-context: {new_config['current-context']}"
                )

            if show_diff:
                diff = difflib.unified_diff(
                    yaml.dump(existing_config, default_flow_style=False).splitlines(),
                    yaml.dump(updated_config, default_flow_style=False).splitlines(),
                    fromfile="Original",
                    tofile="Updated",
                    lineterm="",
                )
                diff_output.extend(list(diff))

            if not dry_run:
                backup_path = create_backup(kubeconfig_path)
                with open(kubeconfig_path, "w") as f:
                    yaml.dump(updated_config, f, default_flow_style=False)
                manage_backups(kubeconfig_path, max_backups)
                logger.info(
                    f"Kubeconfig updated successfully. Backup created at {backup_path}"
                )
            else:
                logger.info(
                    "Dry run: The following changes would be made to the kubeconfig:"
                )
                for change in changes:
                    logger.info(f"  {change}")
        else:
            logger.info("No changes would be made to the kubeconfig.")

    except Exception as e:
        logger.error(f"Error updating kubeconfig: {e}")
        if not dry_run and backup_path:
            logger.info("Rolling back to the previous version...")
            shutil.copy2(backup_path, kubeconfig_path)
        return [], []

    return changes, diff_output, updated_config  # Return the updated_config as well


def merge_configs(existing_config, new_config):
    new_cluster_name = new_config.get("clusters", [{}])[0].get("name")

    for key in ["clusters", "contexts", "users"]:
        existing_items = {item["name"]: item for item in existing_config.get(key, [])}
        for new_item in new_config.get(key, []):
            if new_item["name"] in existing_items:
                # Update with new information while preserving custom fields
                existing_item = existing_items[new_item["name"]]
                if key == "clusters":
                    existing_cluster = existing_item.get("cluster", {})
                    new_cluster = new_item.get("cluster", {})
                    for k, v in new_cluster.items():
                        existing_cluster[k] = v
                    existing_item["cluster"] = existing_cluster
                elif key == "contexts":
                    existing_context = existing_item.get("context", {})
                    new_context = new_item.get("context", {})
                    existing_context.update(new_context)
                    existing_item["context"] = existing_context
                elif key == "users":
                    existing_user = existing_item.get("user", {})
                    new_user = new_item.get("user", {})
                    existing_user.update(new_user)
                    existing_item["user"] = existing_user
            else:
                existing_items[new_item["name"]] = new_item
        existing_config[key] = list(existing_items.values())

    # Update current-context
    if "current-context" in new_config:
        existing_config["current-context"] = new_config["current-context"]

    # Remove items not present in new_config
    for key in ["clusters", "contexts", "users"]:
        new_items = {item["name"] for item in new_config.get(key, [])}
        existing_config[key] = [
            item for item in existing_config[key] if item["name"] in new_items
        ]

    logger.debug(f"Merged config: {existing_config}")
    return existing_config

