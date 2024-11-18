from cli import parse_args
from config_manager import update_kubeconfig
from utils import get_kubeconfig_path, get_download_location, get_config_files

def main():
    args = parse_args()

    if args.vv:
        print("Features:")
        print("- Automatic backup creation")
        print(f"- Keeps {args.backup} most recent backups")
        print("- Automatic rollback on failure")
        print("- Diff output available")

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
    changes, diff_output = update_kubeconfig(kubeconfig_path, new_config_files, args.backup, args.diff)

    if changes:
        print("Changes made:")
        for change in changes:
            print(f"- {change}")
        if args.vv:
            print(f"\nBackup created in: {kubeconfig_path.parent / 'kubezap_backups'}")
        if args.diff:
            print("\nDiff of changes:")
            print('\n'.join(diff_output))
    else:
        print("No changes were made. Possible error occurred and changes were rolled back.")

if __name__ == '__main__':
    main()
