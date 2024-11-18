import argparse
import argcomplete
import glob
import os
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
            help_text = "\n".join(help_lines)
        else:
            help_text = ""

        if action.option_strings:
            option_string = ", ".join(action.option_strings)
            option_string = f"{option_string:<35}"
        else:
            option_string = ""

        return f"  {option_string}{help_text}\n\n"

    def _format_usage(self, usage, actions, groups, prefix):
        return super()._format_usage(usage, actions, groups, prefix) + "\n"

    def _split_lines(self, text, width):
        return text.splitlines()

    def _format_env_var(self, var, description):
        var_string = f"{var:<35}"
        desc_lines = textwrap.wrap(description, 60)
        desc_text = "\n".join(desc_lines)
        return f"  {var_string}{desc_text}\n\n"

    def format_help(self):
        help = super().format_help()
        env_vars = "\n\nEnvironment Variables:\n"
        env_vars += self._format_env_var(
            "KUBECONFIG_LOCATION", "Override the default kubeconfig location"
        )
        env_vars += self._format_env_var(
            "DEFAULT_DOWNLOAD_LOCATION",
            "Set the default download location for new kubeconfig files",
        )
        return f"{help}{env_vars}"

class VersionAction(argparse.Action):
    def __init__(
        self,
        option_strings,
        version=None,
        dest=None,
        default=argparse.SUPPRESS,
        help="show program's version number and exit",
    ):
        super(VersionAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )
        self.version = version

    def __call__(self, parser, namespace, values, option_string=None):
        version = self.version
        if version is None:
            version = parser.version
        print(version)
        parser.exit()

def config_completer(prefix, parsed_args, **kwargs):
    download_location = parsed_args.download_location or os.environ.get('DEFAULT_DOWNLOAD_LOCATION', '.')
    return (f for f in glob.glob(os.path.join(download_location, prefix + '*')) if os.path.isfile(f))

def parse_args():
    description = '''
    KubeZap: A tool to update kubeconfig with new configurations.

    This tool allows you to merge new kubeconfig files into your existing kubeconfig,
    while maintaining backups and providing detailed information about the changes made.

    Features:
    - Automatic backup creation
    - Customizable number of backup files to keep
    - Automatic rollback on failure
    - Detailed merge information in verbose mode
    - Diff output to show exact changes
    '''

    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=CustomFormatter,
    )

    parser.add_argument(
        "-k", "--kubeconfig",
        help="Path to the kubeconfig file to update",
    )
    parser.add_argument(
        "-l", "--download-location",
        help="Directory containing the new kubeconfig files",
    )
    parser.add_argument(
        "-c", "--conf-name",
        help="Name pattern for the new kubeconfig files",
    )
    parser.add_argument(
        "-n", "--number-of-configs",
        type=int,
        default=1,
        help="Number of most recent config files to process",
    )
    parser.add_argument(
        "-vv",
        action="store_true",
        help="Increase output verbosity",
    )
    parser.add_argument(
        "--version",
        action=VersionAction,
        version=f"KubeZap v{__version__}",
    )
    parser.add_argument(
        "-b", "--backup",
        type=int,
        default=5,
        help="Number of backup files to keep",
    )
    parser.add_argument(
        "-d", "--diff",
        action="store_true",
        help="Show diff of changes",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making any changes",
    )

    argcomplete.autocomplete(parser)
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    print(args)





