import os
import subprocess
import time
import logging

# Configure logging
LOG_FILE = "/home/orangepi/Desktop/projects/orangepi/logs/mount.log"  # Change path if needed
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def run_mounts():
    """Mounts all drives and restarts the Jellyfin Docker container."""
    logging.info("Starting the mount process...")

    smb_username = os.getenv('SMB_USERNAME')
    smb_password = os.getenv('SMB_PASSWORD')
    sudo_password = os.getenv('MY_PASSWORD')

    if not all([smb_username, smb_password, sudo_password]):
        logging.error("Missing required environment variables.")
        return

    drives = [
        {"type": "smb", "source": "//192.168.1.1/g", "target": "/mnt/smbshare"},
        {"type": "local", "source": "/dev/sda1", "target": "/mnt/wd", "fs_type": "exfat"}
    ]

    for drive in drives:
        try:
            mount_command = []
            if drive["type"] == "smb":
                mount_command = [
                    "sudo", "mount", "-t", "cifs",
                    f"-o=username={smb_username},password={smb_password},vers=1.0",
                    drive["source"], drive["target"]
                ]
            elif drive["type"] == "local":
                mount_command = [
                    "sudo", "mount", "-t", drive["fs_type"],
                    drive["source"], drive["target"]
                ]

            subprocess.run(
                ["sudo", "-S"] + mount_command,
                input=f"{sudo_password}\n", text=True, check=True
            )
            logging.info(f"Mounted {drive['source']} to {drive['target']} successfully.")

        except subprocess.CalledProcessError as error:
            logging.error(f"Mounting {drive['source']} failed with exit status {error.returncode}")
        except FileNotFoundError:
            logging.error(f"Mount command not found for {drive['source']}.")
        except PermissionError:
            logging.error(f"Permission denied while mounting {drive['source']}.")

    try:
        subprocess.run(["docker", "restart", "jellyfin"], check=True)
        logging.info("Docker container 'jellyfin' restarted successfully.")
    except subprocess.CalledProcessError as error:
        logging.error(f"Docker restart failed with exit status {error.returncode}.")
    except FileNotFoundError:
        logging.error("Docker command not found. Is Docker installed?")
    except PermissionError:
        logging.error("Permission denied while restarting Docker.")

if __name__ == "__main__":
    logging.info("Waiting 5 minutes before starting mount process...")
    time.sleep(300)
    run_mounts()
