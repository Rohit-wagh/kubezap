import logging
import yaml
import os
from cli import parse_args
from config_manager import update_kubeconfig
from utils import get_kubeconfig_path, get_download_location, get_config_files
from tqdm import tqdm
from colorama import init, Fore, Style

init(autoreset=True)

logger = logging.getLogger(__name__)

def setup_logging(verbose):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

def list_contexts(kubeconfig_path):
    with open(kubeconfig_path, 'r') as f:
        config = yaml.safe_load(f)
    contexts = config.get('contexts', [])
    current_context = config.get('current-context')
    
    logger.info(Fore.CYAN + "Available contexts:")
    for context in contexts:
        name = context['name']
        if name == current_context:
            logger.info(Fore.GREEN + f"* {name} (current)")
        else:
            logger.info(Fore.CYAN + f"  {name}")

def main():
    args = parse_args()
    setup_logging(args.vv)

    try:
        kubeconfig_path = get_kubeconfig_path(args)
        if not kubeconfig_path.exists():
            raise FileNotFoundError(f"Kubeconfig file not found at {kubeconfig_path}. Please provide a valid kubeconfig file.")

        download_location = get_download_location(args)
        
        new_config_files = get_config_files(download_location, args.conf_name, args.number_of_configs)
        logger.debug(f"Found config files: {new_config_files}")
        
        if not new_config_files:
            logger.warning(Fore.YELLOW + f"No matching config files found in {download_location}")
            logger.info(Fore.CYAN + f"To add config files, place them in {download_location} with names matching the pattern '{args.conf_name or 'config*.yaml'}'")
            logger.info(Fore.CYAN + "You can also specify a different location using the --download-location argument")
            return

        changes = []
        diff_output = []
        files_processed = 0
        files_changed = 0
        with tqdm(total=len(new_config_files), desc="Updating kubeconfig", unit="file") as pbar:
            for new_config_file in new_config_files:
                with open(new_config_file, 'r') as f:
                    new_config = yaml.safe_load(f)
                cluster_name = new_config.get('clusters', [{}])[0].get('name', 'Unknown Cluster')
                pbar.set_description(f"Updating kubeconfig for {cluster_name}")
                
                file_changes, file_diff_output = update_kubeconfig(kubeconfig_path, [new_config_file], args.backup, args.diff, args.dry_run)
                changes.extend(file_changes)
                diff_output.extend(file_diff_output)
                files_processed += 1
                if file_changes:
                    files_changed += 1
                pbar.update(1)

        logger.info(f"Processed {files_processed} file(s), {files_changed} file(s) resulted in changes.")

        if changes:
            logger.info(Fore.GREEN + "Changes made:")
            for change in changes:
                logger.info(Fore.GREEN + f"- {change}")

            if args.diff:
                logger.info(Fore.CYAN + "Diff:")
                for line in diff_output:
                    logger.info(Fore.CYAN + line)

            # List contexts after making changes
            list_contexts(kubeconfig_path)

            if not args.dry_run:
                logger.info(f"Backup created in: {os.path.dirname(kubeconfig_path)}/kubezap_backups")

    except ValueError as e:
        logger.error(Fore.RED + f"An error occurred: {str(e)}")
    except FileNotFoundError as e:
        logger.error(Fore.RED + f"File not found: {str(e)}")
    except Exception as e:
        logger.error(Fore.RED + f"An unexpected error occurred: {str(e)}")
        logger.debug("Error details:", exc_info=True)

if __name__ == "__main__":
    main()

