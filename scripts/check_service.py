import paramiko
import sys

def check_service_file(hostname, username, password):
    print(f"Connecting to {hostname}...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username, password=password)
        
        cmd = "cat /etc/systemd/system/energyapp-web.service"
        print(f"\n--- Running: {cmd} ---")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode().strip())
        
        client.close()
        
    except Exception as e:
        print(f"Check failed: {e}")

if __name__ == "__main__":
    HOST = "184.174.33.249"
    USER = "root"
    PASS = "Jram1992@!"
    
    check_service_file(HOST, USER, PASS)
