import os
import shutil
from datetime import datetime
from pathlib import Path

def create_backup(kubeconfig_path):
    backup_dir = kubeconfig_path.parent / 'kubezap_backups'
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"kubeconfig_backup_{timestamp}"
    shutil.copy2(kubeconfig_path, backup_path)
    return backup_path

def manage_backups(backup_dir, max_backups=10):
    backups = sorted(backup_dir.glob('kubeconfig_backup_*'), key=os.path.getmtime, reverse=True)
    # Keep only the most recent max_backups
    for old_backup in backups[max_backups:]:
        old_backup.unlink()
    # Remove any files that don't match the backup pattern
    for file in backup_dir.glob('*'):
        if not file.name.startswith('kubeconfig_backup_'):
            file.unlink()
