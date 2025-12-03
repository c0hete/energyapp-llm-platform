import paramiko
import time

def debug_curl(hostname, username, password):
    print(f"Connecting to {hostname}...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username, password=password)
        
        # 1. Start service
        print("Starting service...")
        client.exec_command("systemctl start energyapp-web")
        time.sleep(5)
        
        # 2. Curl localhost
        print("Curling localhost:3000...")
        stdin, stdout, stderr = client.exec_command("curl -v http://127.0.0.1:3000")
        print(stdout.read().decode().strip())
        print(stderr.read().decode().strip())
        
        # 3. Get logs
        print("\nChecking logs...")
        stdin, stdout, stderr = client.exec_command("journalctl -u energyapp-web -n 50 --no-pager")
        print(stdout.read().decode().strip())
        
        client.close()
        
    except Exception as e:
        print(f"Debug failed: {e}")

if __name__ == "__main__":
    HOST = "184.174.33.249"
    USER = "root"
    PASS = "Jram1992@!"
    
    debug_curl(HOST, USER, PASS)
