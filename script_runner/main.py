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
from logging.handlers import RotatingFileHandler
from typing import List, Tuple, Union
from datetime import datetime

#Configure logging with rotation
log_handler = RotatingFileHandler('service_runner.log', maxBytes=5*1024*1024, backupCount=3)
log_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
log_handler.setFormatter(log_formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

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
        logger.error("Environment file not found: %s", env_file_path)
        logger.exception(e)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("An error occurred while loading the environment file.")
        logger.exception(e)

def read_config(file_path: str) -> List[Union[Tuple[int, str, str], Tuple[int, None, str]]]:
    """Read configuration file and return a list of tuples (line_number, directory, command)."""
    commands = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()
                if line.startswith('#') or not line:  # Ignore comments and empty lines
                    continue
                parts = line.split(':', 1)
                if len(parts) == 2:
                    commands.append((line_number, parts[0], parts[1]))
                else:
                    commands.append((line_number, None, parts[0]))
    except FileNotFoundError as e:
        logger.error("Configuration file not found: %s", file_path)
        logger.exception(e)
    except Exception as e: # pylint: disable=W0718
        logger.error("An error occurred while reading the configuration file.")
        logger.exception(e)
    return commands

def run_command(line_number: int, directory: Union[str, None], command: str):
    """Run a command, optionally in a given directory, and log with command identification."""
    original_dir = os.getcwd()
    try:
        if directory:
            os.chdir(directory)
        subprocess.run(command, shell=True, check=True, env=os.environ)
        logger.info("\n  Line %d - Successfully ran command '%s' in directory '%s'\n",
                    line_number, command, directory if directory else 'current directory')
    except FileNotFoundError as e:
        logger.error("\n Line %d - Directory not found: %s\n", line_number, directory)
        logger.exception(e)
    except subprocess.CalledProcessError as e:
        logger.error("\n Line %d - Command failed: %s\n", line_number, command)
        logger.exception(e)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("\nLine %d - An error occurred while running the command.\n", line_number)
        logger.exception(e)
    finally:
        os.chdir(original_dir)  # Restore the original directory

def main():
    """Main function to read the configuration and run commands as services."""
    # Add a separator for each script run
    separator = "\n \n \n " + "=" * 50 + "\n"
    timestamp = f"\n \n \n Script Run at: {datetime.now()}\n"
    logger.info("%s%s%s", separator, timestamp, separator)

    env_file_path = '/home/orangepi/Desktop/projects/orangepi/serial_communication/web/.env'
    config_file_path = 'commands.txt'

    # Load environment variables from the .env file
    load_env_file(env_file_path)

    commands = read_config(config_file_path)

    threads = []

    for item in commands:
        line_number, directory, command = item
        thread = threading.Thread(target=run_command, args=(line_number, directory, command))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
