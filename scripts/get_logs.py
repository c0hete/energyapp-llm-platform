import paramiko
import sys

def get_logs(hostname, username, password):
    print(f"Connecting to {hostname}...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username, password=password)
        
        cmd = "journalctl -u energyapp-web -n 50 --no-pager"
        print(f"\n--- Running: {cmd} ---")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode().strip())
        
        client.close()
        
    except Exception as e:
        print(f"Log fetch failed: {e}")

if __name__ == "__main__":
    HOST = "184.174.33.249"
    USER = "root"
    PASS = "Jram1992@!"
    
    get_logs(HOST, USER, PASS)
