"""This script will mount my router HDD to my orangepi on startup after 5 minutes"""
import os
import subprocess
import time

def run_smb_mount():
    """Main function to mount drive"""
    # Fetch the environment variables for SMB credentials and sudo password
    smb_username = os.getenv('SMB_USERNAME')
    smb_password = os.getenv('SMB_PASSWORD')
    sudo_password = os.getenv('MY_PASSWORD')

    # Ensure the required environment variables are set
    if not smb_username or not smb_password or not sudo_password:
        print("Error: Required environment variables are not set.")
        return

    # Construct the SMB mount command
    smb_mount_command = (
        f"sudo mount -t cifs -o username={smb_username},password={smb_password},vers=1.0 "
        f"//192.168.1.1/g /mnt/smbshare"
    )

    # Run the command using sudo
    try:
        _ = subprocess.run(f"echo {sudo_password} | sudo -S {smb_mount_command}",
                           shell=True, check=True)
        print("SMB share mounted successfully.")

        # Restart the Docker container
        docker_restart_command = "docker restart jellyfin"
        subprocess.run(docker_restart_command, shell=True, check=True)
        print("Docker container 'jellyfin' restarted successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed with exit status {e.returncode}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    i = 5
    while i > 0:
        print (f"\n\n\tWaiting for {i} minutes then mount the drive\n")
        i -= 1
        time.sleep(60)
    run_smb_mount()
