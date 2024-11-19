import os
import shutil
from datetime import datetime


def create_backup(kubeconfig_path):
    backup_dir = os.path.join(os.path.dirname(kubeconfig_path), "kubezap_backups")
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"kubeconfig_backup_{timestamp}.yaml"
    backup_path = os.path.join(backup_dir, backup_filename)

    shutil.copy2(kubeconfig_path, backup_path)
    return backup_path


def manage_backups(kubeconfig_path, max_backups):
    backup_dir = os.path.join(os.path.dirname(kubeconfig_path), "kubezap_backups")
    if not os.path.exists(backup_dir):
        return

    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.startswith("kubeconfig_backup_")],
        reverse=True,
    )

    while len(backups) > max_backups:
        oldest_backup = backups.pop()
        os.remove(os.path.join(backup_dir, oldest_backup))

