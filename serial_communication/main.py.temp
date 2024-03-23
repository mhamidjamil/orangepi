import subprocess
# this script is responsible for running multiple python scripts in parallel
result = subprocess.run(
    ['python', 'ip_detail/ip_fetcher.py'], capture_output=True, text=True)
print(result.stdout)
