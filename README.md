# databricks_apps_cleanup

## Databricks App Cleanup Script Readme

This script helps manage and delete old apps in a Databricks workspace based on their age. It provides flexibility to skip specific apps using an exception list and includes an option to enable or disable deletion.

## Features
- **List all apps** in a Databricks workspace.
- **Delete apps** older than a specified age, while excluding apps on an exception list.
- **Dry run mode**: Print apps that would be deleted without actually performing the deletion.

## Usage

### Prerequisites
- Make sure the `databricks-sdk` is installed in your Python environment.

### Arguments
- `-e, --exception_file`: JSON file containing URLs of apps to exclude from deletion. Defaults to `apps_exception.json`.
- `-d, --enable_delete`: Enable deletion if set; otherwise, the script will only print values.
- `-a, --max_app_age`: Maximum age of apps to delete in days. Defaults to 7 days.

### Example
```bash
python lakehouse_monitor_cleanup.py -e path/to/your/exception_file.json -d -a 10