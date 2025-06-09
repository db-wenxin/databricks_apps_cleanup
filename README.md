# Databricks Apps Cleanup Script

This script helps manage Databricks applications by automatically stopping or deleting them based on their age and last update time. It supports exceptions for specific applications and can manage apps across multiple Databricks workspaces.

## Features

-   **Automated App Lifecycle Management**:
    -   Stops apps if they were created and last updated more than a configurable number of days (default: 3 days).
    -   Deletes apps if they are already in a stopped state and their last update was more than a configurable number of days ago (default: 7 days).
-   **Exception Handling**:
    -   Skips specified applications from stop/delete operations.
    -   Supports time-bound exceptions with expiration dates (YYYY-MM-DD format). An empty expiry date means the exception never expires.
-   **Multi-Workspace Support**:
    -   Manages apps across multiple Databricks workspaces using a JSON configuration file.
-   **Dry Run Mode**:
    -   Allows you to see which apps would be affected without actually performing any stop/delete operations.
-   **Secure Authentication**:
    -   Uses client ID and client secret for authentication, with secrets fetched from a specified Databricks secret scope.
-   **Detailed Logging**:
    -   Provides comprehensive logging of actions performed.

## Prerequisites

-   Python 3.x
-   Databricks SDK for Python (`databricks-sdk`)

## Configuration

### 1. Workspace Configuration File

Create a JSON file (e.g., `workspaces.json`) to define the Databricks workspaces to manage.

Example:
```json
[
  {
    "name": "Workspace_A_Prod",
    "endpoint": "https://your-workspace-A.cloud.databricks.com",
    "application_id": "client_id_for_workspace_A"
  },
  {
    "name": "Workspace_B_Dev",
    "endpoint": "https://your-workspace-B.cloud.databricks.com",
    "application_id": "client_id_for_workspace_B"
  }
]
```
The `application_id` will be used to fetch the corresponding client secret from the Databricks secret scope.

### 2. App Exception List File

Create a JSON file (e.g., `apps_exceptions.json`) to list applications that should be excluded from cleanup operations.

Example:
```json
[
  {
    "app_url": "https://app1-xxxx.aws.databricksapps.com",
    "expiry": "2025-12-31"
  },
  {
    "app_url": "https://app2-yyyy.gcp.databricksapps.com",
    "expiry": ""
  }
]
```
-   `app_url`: The unique URL of the Databricks application.
-   `expiry`: The expiration date for the exception in `YYYY-MM-DD` format. If empty, the exception never expires.

## Usage

The script is run using `new_apps_management.py`.

```bash
python databricks_apps_cleanup/new_apps_management.py \
    -c <path_to_workspace_config_file.json> \
    -e <path_to_app_exceptions_file.json> \
    [--max_app_age <days>] \
    [--max_age_before_stop <days>] \
    [--databricks_secret_scope_name <scope_name>] \
    [--dry_run]
```

### Command-Line Arguments

-   `-c, --config_file_workspace` (required): Path to the JSON file with workspace configurations.
-   `-e, --except_apps_file` (required): Path to the JSON file with the list of app exceptions.
-   `-a, --max_app_age` (optional): Maximum age in days an app can be (since last update, in stopped state) before it is deleted. Default is 7 days.
-   `-s, --max_age_before_stop` (optional): Maximum age in days an app can be (since last update, in active state) before it is stopped. Default is 3 days.
-   `-d, --dry_run` (optional): If set, the script will only log actions without performing them.
-   `--databricks_secret_scope_name` (required): The name of the Databricks secret scope to fetch client secrets. It is recommended to securely store your credentials using Databricks secret scope

## How it Works

1.  The script reads the workspace configurations and the app exception list.
2.  For each configured workspace:
    a.  It authenticates using the provided endpoint, client ID, and a client secret fetched from the specified secret scope.
    b.  It fetches all Databricks applications in the workspace.
    c.  It processes the exception list, identifying active and expired exceptions.
    d.  For each app:
        i.  If the app is in the active exception list, it's skipped.
        ii. If the app is `ACTIVE` and its last update time is older than `max_age_before_stop`, it will be stopped (unless in dry-run mode).
        iii. If the app is `STOPPED` and its last update time is older than `max_app_age`, it will be deleted (unless in dry-run mode).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.