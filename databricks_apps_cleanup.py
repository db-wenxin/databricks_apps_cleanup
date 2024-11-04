from databricks.sdk import WorkspaceClient
from datetime import datetime
import json
import argparse

def get_config_json(config_file):
    """Read and parse JSON config file."""
    with open(config_file, 'r') as file:
        config = json.load(file)
    return config

def get_apps(client):
    """Fetch and return all apps in the workspace."""
    try:
        all_apps = client.apps.list()
        return list(all_apps)  # Convert response to a list of apps
    except Exception as e:
        print(f"Error fetching apps: {e}")
        return []

def delete_app(client, app):
    """Delete the given app."""
    try:
        client.apps.delete(app.name)
        print(f"Deleted app with ID: {app.name}")
    except Exception as e:
        print(f"Error deleting app {app.name}: {e}")

def is_exception(app, exception_list):
    """Check if the app URL is in the exception list."""
    return app.url in exception_list

def delete_old_apps(client, max_app_age, enable_delete, exception_list):
    """Main function to handle app cleanup."""
    apps = get_apps(client=client)
    print(f"Found {len(apps)} apps.")

    if apps:
        for app in apps:
            print("\n")
            # Calculate the age of the app in days
            create_time = datetime.strptime(app.create_time, "%Y-%m-%dT%H:%M:%SZ")
            app_age = (datetime.now() - create_time).days
            print(app.url)
            print(f"App {app.name} was created {app_age} days ago.")
            # Delete app if it's older than max_app_age and not in exception list
            if app_age >= max_app_age and not is_exception(app, exception_list) and enable_delete:
                print(f"Deleting app: {app.name} older than {max_app_age} days.")
                delete_app(client=client, app=app)
            else:
                print(f"Skipping app: {app.name}. (age: {app_age} days)")

def main():
    """Parse arguments and initiate the app cleanup process."""
    parser = argparse.ArgumentParser(description="Delete old Databricks Apps")
    parser.add_argument('-e', '--exception_file', type=str,
                        help="JSON file with exception list for long running Apps",
                        default='apps_exception.json', required=False)
    parser.add_argument('-d', '--enable_delete', action='store_true',
                        help="Enable deletion if set. Else it will just print values.",
                        default=False, required=False)
    parser.add_argument('-a', '--max_app_age', type=int,
                        help="Maximum age of apps to delete in days",
                        default=7, required=False)
    args = parser.parse_args()

    enable_delete = args.enable_delete
    max_app_age = args.max_app_age
    exception_file = args.exception_file

    if not enable_delete:
        print("Deletion Disabled. Set -d to enable deletion.")

    # Load exception list from the specified JSON file
    exception_config = get_config_json(exception_file)
    exception_list = exception_config.get("exception_list_apps_url", [])

    # Create a Databricks Workspace client (update with your configs if needed)
    client = WorkspaceClient()

    # Perform app cleanup
    delete_old_apps(client=client, max_app_age=max_app_age,
                    enable_delete=enable_delete, exception_list=exception_list)

if __name__ == "__main__":
    main()