#!/usr/bin/env python3

import sys
import os
import importlib
import traceback

from utils import cliparser
from core import checks
from core.interactive import InteractiveShell
from utils.loggers import log
from utils.config import config_args, version


def check_python_version():
    major_version = sys.version_info.major
    minor_version = sys.version_info.minor

    version_string = f"{major_version}.{minor_version}"

    if major_version != 3:
        print(f"\033[91m[!]\033[0m SSTImap requires Python 3.6 or above. Detected version: {version_string}")
        sys.exit(1)

    if minor_version < 6:
        print(f"\033[91m[!]\033[0m Python {version_string} is not supported. Please upgrade to Python 3.6 or higher.")
        sys.exit(1)

    if minor_version > 13:
        print(f"\033[33m[!]\033[0m SSTImap was not tested with Python {version_string}. Proceeding with caution...")


def display_welcome_banner(colour_mode):
    from utils.loggers import formatter, no_colour

    formatter.colour = colour_mode

    banner_text = cliparser.banner()

    if colour_mode:
        print(banner_text)
    else:
        print(no_colour(banner_text))


def scan_plugin_folder():
    plugin_directory = f"{sys.path[0]}/plugins"
    if not os.path.exists(plugin_directory):
        print(f"[!] Plugin directory not found: {plugin_directory}")
        return []

    group_list = list(os.scandir(plugin_directory))
    valid_groups = [group for group in group_list if group.is_dir()]
    return valid_groups


def import_plugins():
    importlib.invalidate_caches()
    plugin_groups = scan_plugin_folder()

    for group in plugin_groups:
        group_name = group.name
        group_path = os.path.join(sys.path[0], "plugins", group_name)
        module_entries = list(os.scandir(group_path))

        for entry in module_entries:
            module_name = entry.name
            if module_name.endswith(".py") and not module_name.startswith("_"):
                import_path = f"plugins.{group_name}.{module_name[:-3]}"
                importlib.import_module(import_path)


def import_data_types():
    importlib.invalidate_caches()

    data_types_path = os.path.join(sys.path[0], "data_types")
    if not os.path.exists(data_types_path):
        print("[!] data_types directory missing!")
        return

    files = list(os.scandir(data_types_path))

    for file_entry in files:
        file_name = file_entry.name
        if file_name.endswith(".py") and not file_name.startswith("_"):
            module_name = file_name[:-3]
            full_module_path = f"data_types.{module_name}"
            importlib.import_module(full_module_path)


def print_plugin_summary():
    from core.plugin import loaded_plugins
    plugin_summary = []

    for category, plugin_list in loaded_plugins.items():
        count = len(plugin_list)
        plugin_summary.append(f"{category}: {count}")

    summary_str = "; ".join(plugin_summary)
    log.log(26, f"Loaded plugins by categories: {summary_str}")


def print_data_type_summary():
    from core.data_type import loaded_data_types
    count = len(loaded_data_types)
    log.log(26, f"Loaded request body types: {count}\n")


def show_usage_hint():
    log.log(22,
            "SSTImap requires at least one of the following options:\n"
            "  - Target URL (-u, --url)\n"
            "  - Load URLs from file (--load-urls)\n"
            "  - Load forms from file (--load-forms)\n"
            "  - Interactive mode (-i, --interactive)\n"
            "  - Specific module (--module)\n"
            "Use --help for more details.")


def handle_module_option(module_option):
    if module_option == 'list':
        checks.module_info("")
    else:
        checks.module_info(module_option)


def start_interactive_shell(configured_args):
    log.log(23, "Starting SSTImap in interactive mode. Type 'help' for available commands.")
    shell = InteractiveShell(configured_args)
    shell.cmdloop()


def launch_scan(configured_args):
    log.log(23, "Starting SSTI scan using predefined configuration...")
    checks.scan_website(configured_args)


def main():
    # Step 1: CLI arguments
    cli_args = cliparser.options
    args_dict = vars(cli_args)

    # Step 2: Inject defaults
    configured_args = config_args(args_dict)

    # Step 3: Version
    configured_args['version'] = version

    # Step 4: Banner
    colour_enabled = configured_args.get("colour", True)
    display_welcome_banner(colour_enabled)

    # Step 5: Plugin + Data type loading
    import_plugins()
    print_plugin_summary()

    import_data_types()
    print_data_type_summary()

    # Step 6: Route logic
    no_input_provided = not (
        configured_args.get('url') or
        configured_args.get('interactive') or
        configured_args.get('load_urls') or
        configured_args.get('load_forms') or
        configured_args.get('module')
    )

    if no_input_provided:
        show_usage_hint()

    elif configured_args.get('module'):
        selected_module = configured_args['module']
        handle_module_option(selected_module)

    elif configured_args.get('interactive'):
        start_interactive_shell(configured_args)

    else:
        launch_scan(configured_args)


if __name__ == '__main__':
    try:
        check_python_version()
        main()
    except KeyboardInterrupt:
        print()
        log.log(22, "User interruption. Exiting SSTImap...")
    except EOFError:
        print()
        log.log(22, "Received EOF. Exiting SSTImap...")
    except Exception as err:
        log.critical("An unexpected error occurred!")
        log.critical(f"Error: {err}")
        log.debug(traceback.format_exc())
        raise err

