"""This script will mount my router HDD and local drives
to my Orange Pi on startup after 5 minutes"""
import os
import subprocess
import time

def run_mounts():
    """Main function to mount all drives"""
    # Fetch the environment variables for SMB credentials and sudo password
    smb_username = os.getenv('SMB_USERNAME')
    smb_password = os.getenv('SMB_PASSWORD')
    sudo_password = os.getenv('MY_PASSWORD')

    # Ensure required environment variables are set
    if not smb_username or not smb_password or not sudo_password:
        print("Error: Required environment variables are not set.")
        return

    # List of drives to mount (Add more as needed)
    drives = [
        {"type": "smb", "source": "//192.168.1.1/g", "target": "/mnt/smbshare"},
        {"type": "local", "source": "/dev/sda1", "target": "/mnt/wd", "fs_type": "exfat"}
    ]

    for drive in drives:
        try:
            mount_command = ""
            if drive["type"] == "smb":
                mount_command = (
                    f"sudo mount -t cifs -o username={smb_username},"
                    f"password={smb_password},vers=1.0 {drive['source']} {drive['target']}"
                )
            elif drive["type"] == "local":
                mount_command = (
                    f"sudo mount -t {drive['fs_type']} {drive['source']} {drive['target']}"
                )

            # Execute the mount command
            _ = subprocess.run(
                f"echo {sudo_password} | sudo -S {mount_command}",
                shell=True, check=True
            )
            print(f"Mounted {drive['source']} to {drive['target']} successfully.")

        except subprocess.CalledProcessError as e:
            print(f"Error: Mounting {drive['source']} failed with exit status {e.returncode}")
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"An unexpected error occurred while mounting {drive['source']}: {e}")

    # Restart the Docker container
    try:
        docker_restart_command = "docker restart jellyfin"
        subprocess.run(docker_restart_command, shell=True, check=True)
        print("Docker container 'jellyfin' restarted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error: Docker restart failed with exit status {e.returncode}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"An unexpected error occurred while restarting Docker: {e}")

if __name__ == "__main__":
    for i in range(5, 0, -1):
        print(f"\n\n\tWaiting for {i} minutes then mount the drives\n")
        time.sleep(60)

    run_mounts()
