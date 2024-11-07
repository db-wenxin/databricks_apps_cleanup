# databricks_apps_cleanup

## Databricks App Cleanup Script 

This script helps manage and clean up old apps in a Databricks workspace based on their age. It provides flexibility to skip specific apps using an exception list and includes options to either delete or stop apps that meet certain criteria.

## Features
- **List all apps** in a Databricks workspace.
- **Delete apps** older than a specified age, while excluding apps on an exception list.
- **Stop apps** older than a specified age when deletion is not enabled, excluding apps on an exception list.

## Usage

### Prerequisites
- Make sure the  `databricks-sdk` version 0.36.0 or above is installed in your Python environment.

### Arguments

- `-e, --exception_file`: JSON file containing URLs of apps to exclude from stopping or deletion. Defaults to `apps_exception.json`.
- `-d, --enable_delete`: Enable deletion if set; otherwise, the script will stop apps that meet the criteria.
- `-a, --max_app_age`: Maximum age of apps to delete or stop in days. Defaults to 7 days.

### Behavior

- **With `--enable_delete` flag**: The script will **delete** apps older than the specified age that are not in the exception list.
- **Without `--enable_delete` flag**: The script will **stop** apps older than the specified age that are not in the exception list.


### Example
#### To delete apps older than 10 days:
```bash
python lakehouse_monitor_cleanup.py -e path/to/your/exception_file.json -d -a 10
```

#### To stop apps older than 7 days (default age):

```bash
python databricks_apps_cleanup.py -e path/to/your/exception_file.json
```

### Exception File Format
Apps listed in the exception_list_apps_url array will not be stopped or deleted, regardless of their age.The exception file should be a JSON file with the following structure:

```json
{
  "exception_list_apps_url": [
    "https://app1.url",
    "https://app2.url"
  ]
}
```
## Notes

1. **Exception List**: Apps whose URLs are listed in the exception file will not be stopped or deleted, regardless of their age.
2. **Logging**: The script provides informative print statements to indicate which apps are being stopped or deleted and which are being skipped.

---

## Troubleshooting

- Ensure that the `databricks-sdk` is correctly configured with the necessary permissions to list, stop, and delete apps in your workspace.
- Verify that the exception file is correctly formatted and accessible by the script.

---

## License

This project is licensed under the MIT License.