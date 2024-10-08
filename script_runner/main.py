"""
This script will load environment variables from a specified .env file and execute a series
of commands defined in a configuration file.

Each command can be run in a specified directory, and the execution is handled
concurrently using threads.

Logging is implemented to track the success or failure
of each command, providing insights into the script's operations.

Usage:
1. Specify the path to the .env file and the configuration file containing commands.
2. The script loads the environment variables and executes the commands in parallel.
3. Logs are generated for monitoring the execution process.
"""
import os
import subprocess
import logging
import threading
from typing import List, Tuple, Union

# Configure logging
logging.basicConfig(filename='service_runner.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

def load_env_file(env_file_path: str):
    """Load environment variables from a .env file."""
    try:
        with open(env_file_path, encoding='utf-8') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    except FileNotFoundError as e:
        logging.error("Environment file not found: %s", env_file_path)
        logging.exception(e)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.error("An error occurred while loading the environment file.")
        logging.exception(e)

def read_config(file_path: str) -> List[Union[Tuple[str, str], str]]:
    """Read configuration file and return a list of tuples (directory, command) or just commands."""
    commands = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        commands.append((parts[0], parts[1]))
                    else:
                        commands.append(parts[0])
    except FileNotFoundError as e:
        logging.error("Configuration file not found: %s", file_path)
        logging.exception(e)
    except Exception as e:  # pylint: disable=W0718
        logging.error("An error occurred while reading the configuration file.")
        logging.exception(e)
    return commands

def run_command(directory: Union[str, None], command: str):
    """Run a command, optionally in a given directory."""
    try:
        if directory:
            os.chdir(directory)
        subprocess.run(command, shell=True, check=True, env=os.environ)
        logging.info("Successfully ran command '%s' in directory '%s'",
                     command, directory if directory else 'current directory')
    except FileNotFoundError as e:
        logging.error("Directory not found: %s", directory)
        logging.exception(e)
    except subprocess.CalledProcessError as e:
        logging.error("Command failed: %s", command)
        logging.exception(e)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.error("An error occurred while running the command.")
        logging.exception(e)

def main():
    """Main function to read the configuration and run commands as services."""
    env_file_path = '/home/orangepi/Desktop/projects/orangepi/serial_communication/web/.env'
    config_file_path = 'commands.txt'

    # Load environment variables from the .env file
    load_env_file(env_file_path)

    commands = read_config(config_file_path)

    threads = []

    for item in commands:
        if isinstance(item, tuple):
            thread = threading.Thread(target=run_command, args=(item[0], item[1]))
        else:
            thread = threading.Thread(target=run_command, args=(None, item))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
