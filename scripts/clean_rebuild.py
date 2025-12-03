import paramiko
import sys
import time

def clean_rebuild(hostname, username, password):
    print(f"Connecting to {hostname}...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username, password=password)
        
        commands = [
            "systemctl stop energyapp-web",
            "cd /root/energyapp-llm-platform/frontend && rm -rf .next",
            "cd /root/energyapp-llm-platform/frontend && npm install",
            "cd /root/energyapp-llm-platform/frontend && npm run build",
            "systemctl start energyapp-web",
            "systemctl status energyapp-web --no-pager"
        ]
        
        for cmd in commands:
            print(f"\n--- Running: {cmd} ---")
            stdin, stdout, stderr = client.exec_command(cmd)
            
            # Stream output for build
            while True:
                line = stdout.readline()
                if not line:
                    break
                print(line.strip())
            
            error = stderr.read().decode().strip()
            if error:
                print(f"[Stderr]: {error}")
                
            if stdout.channel.recv_exit_status() != 0:
                print("Command failed!")
                # Don't break, try to continue or at least see status
        
        client.close()
        
    except Exception as e:
        print(f"Rebuild failed: {e}")

if __name__ == "__main__":
    HOST = "184.174.33.249"
    USER = "root"
    PASS = "Jram1992@!"
    
    clean_rebuild(HOST, USER, PASS)
