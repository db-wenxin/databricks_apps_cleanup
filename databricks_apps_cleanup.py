# Stops apps if they were created and last updated more than <max_stop_age> days ago.
# Deletes apps if their last update was more than <max_app_age> days ago and they are already in a stopped state.
# Skips the apps in the exception list for both operations.

import json
import argparse
import sys
import logging
from datetime import datetime, timezone

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.apps import App 

def get_json_file_content(config_file: str):
    """Load and return the JSON file content."""
    try:
        with open(config_file, 'r') as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Error reading JSON file {config_file}: {e}")
        return []

def is_expired_exception(exception_entry):
    """
    Check if an app exception has expired.
    Returns (is_expired, app_url)
    """
    if not isinstance(exception_entry, dict) or "app_url" not in exception_entry:
        logger.error(f"Invalid exception entry format: {exception_entry}")
        return False, None
    
    app_url = exception_entry["app_url"]
    
    if "expiry" not in exception_entry:
        logger.error(f"Missing required 'expiry' field for app_url: {app_url}")
        return False, app_url
    
    # Empty expiry string means never expires
    if exception_entry["expiry"] == "":
        return False, app_url
    
    # Check if expiry date has passed
    try:
        expiry_date = datetime.strptime(exception_entry["expiry"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        current_date = datetime.now(timezone.utc)
        return current_date >= expiry_date, app_url
    except ValueError:
        logger.error(f"Invalid date format for {app_url}: {exception_entry['expiry']}. Use YYYY-MM-DD or empty string.")
        return False, app_url

def get_apps(client: WorkspaceClient):
    """Fetch and return all apps in the workspace."""
    try:
        return list(client.apps.list())
    except Exception as e:
        logger.info(f"Error fetching apps: {e}")
        return []

def stop_app(client: WorkspaceClient, app: App):
    """Stop the given app."""
    try:
        client.apps.stop_and_wait(app.name)
        logger.info(f"Stopped app: {app.name}")
    except Exception as e:
        logger.error(f"Error stopping app {app.name}: {e}")

def delete_app(client: WorkspaceClient, app: App):
    """Delete the given app."""
    try:
        client.apps.delete(app.name)
        logger.info(f"Deleted app: {app.name}")
    except Exception as e:
        logger.error(f"Error deleting app {app.name}: {e}")

def manage_apps(client: WorkspaceClient, max_stop_age: int, max_app_age: int, app_exceptions_list: list, dry_run: bool):
    """Manage app lifecycle based on last update time."""
    apps = get_apps(client=client)
    logger.info(f"Found {len(apps)} apps.")

    # Process app exception list
    active_exceptions = {}
    expired_exceptions = []
    
    for entry in app_exceptions_list:
        is_expired, app_url = is_expired_exception(entry)
        if app_url:
            if is_expired:
                expired_exceptions.append(app_url)
                logger.info(f"Exception for app {app_url} has expired")
            else:
                active_exceptions[app_url] = True
    
    if expired_exceptions:
        logger.info(f"Found {len(expired_exceptions)} expired app exceptions: {', '.join(expired_exceptions)}")

    if apps:
        for app in apps:
            if app.url in active_exceptions:
                logger.info(f"This App {app.url} is in the active exception list..Skipping exception app: {app.name}")
                continue
            try:
                create_time = datetime.strptime(app.create_time, "%Y-%m-%dT%H:%M:%SZ")
                update_time = datetime.strptime(app.update_time, "%Y-%m-%dT%H:%M:%SZ")
            except Exception as e:
                logger.error(f"Error parsing times for app {app.name}: {e}")
                continue
            
            app_age = (datetime.now() - create_time).days
            update_age = (datetime.now() - update_time).days
            logger.info(f"App {app.name};  URL: {app.url} was created {app_age} days ago and last updated {update_age} days ago.")

            # Stop apps that are active and haven't been updated in more than `max_stop_age` days
            if str(app.compute_status.state) == 'ComputeState.ACTIVE' and update_age >= max_stop_age:
                logger.info(f"Stopping app: {app.name} (last updated {update_age} days ago).")
                if not dry_run:
                    stop_app(client, app)
                continue  # Move to the next app after attempting stop
            
            # Delete apps that are stopped and haven't been updated in more than `max_app_age` days
            if str(app.compute_status.state) == 'ComputeState.STOPPED' and update_age >= max_app_age:
                logger.info(f"Deleting app: {app.name} (last updated {update_age} days ago).")
                if not dry_run:
                    delete_app(client, app)
                continue
            # Skip other apps
            logger.info(f"Skipping app {app.name}. (State: {app.compute_status.state}, Created {app_age} days ago, Last updated {update_age} days ago).")

def main():
    global logger
    logger = logging.getLogger(__name__)
    # Configure logger to write to stdout --- stream spark error log to script standard output.
    handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    local_dbutils = WorkspaceClient().dbutils
    
    parser = argparse.ArgumentParser(description="Manage old Databricks Apps")
    parser.add_argument('-a', '--max_app_age', type=int, default=7, help="Maximum age of apps to delete in days")
    parser.add_argument('-s', '--max_age_before_stop', type=int, default=3, help="Maximum age of apps before stop in days")
    parser.add_argument('-d', '--dry_run', action='store_true', help="Enable dry run mode. If omitted, deletions will be performed.")
    parser.add_argument('-c', '--config_file_workspace', type=str, required=True, help="JSON file with workspace configurations")
    parser.add_argument('-e', '--except_apps_file', type=str, required=True, help="JSON file with app names to skip")
    parser.add_argument('--databricks_secret_scope_name', type=str, default="<please_provide_the_secret_scope_name>")
    args = parser.parse_args()

    client_configs = get_json_file_content(args.config_file_workspace)
    app_exceptions_list = get_json_file_content(args.except_apps_file)

    for config in client_configs:
        logger.info(f"---- Databricks Apps Cleanup in {config['name']} ----\n")

        # if 'gcp.databricks.com' in config['endpoint']:  # Apps are not available in GCP
        #     continue
        ws_client = WorkspaceClient(host=config['endpoint'],
                                   client_id=config['application_id'],
                                   client_secret=local_dbutils.secrets.get(scope=args.databricks_secret_scope_name, key=config['application_id'])
                                   )
        secret_principal = ws_client.current_user.me()
        logger.info(f"Running Apps clean up script as {secret_principal.display_name}; dry_run status: {args.dry_run} \n")
        manage_apps(ws_client, args.max_age_before_stop, args.max_app_age, app_exceptions_list, args.dry_run)

if __name__ == "__main__":
    main()