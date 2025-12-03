import paramiko
import time

def debug_manual_start(hostname, username, password):
    print(f"Connecting to {hostname}...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username, password=password)
        
        # 1. Stop service
        print("Stopping service...")
        client.exec_command("systemctl stop energyapp-web")
        time.sleep(2)
        
        # 2. Run npm start manually
        print("Running npm start manually...")
        # We use a timeout or read until we get some output
        stdin, stdout, stderr = client.exec_command("cd /root/energyapp-llm-platform/frontend && npm run start")
        
        # Read output for a few seconds
        start_time = time.time()
        while time.time() - start_time < 10:
            if stdout.channel.recv_ready():
                print(stdout.channel.recv(1024).decode(), end="")
            if stderr.channel.recv_ready():
                print(stderr.channel.recv(1024).decode(), end="")
            time.sleep(0.1)
            
            if stdout.channel.exit_status_ready():
                break
                
        client.close()
        
    except Exception as e:
        print(f"Debug failed: {e}")

if __name__ == "__main__":
    HOST = "184.174.33.249"
    USER = "root"
    PASS = "Jram1992@!"
    
    debug_manual_start(HOST, USER, PASS)
