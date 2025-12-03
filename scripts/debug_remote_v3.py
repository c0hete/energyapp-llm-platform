import paramiko
import sys

def debug_server(hostname, username, password):
    print(f"Connecting to {hostname}...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username, password=password)
        
        commands = [
            "cd /root/energyapp-llm-platform/frontend && npm list next",
            "journalctl -u energyapp-web -n 50 --no-pager > /tmp/web_logs.txt",
            "cat /tmp/web_logs.txt"
        ]
        
        for cmd in commands:
            print(f"\n--- Running: {cmd} ---")
            stdin, stdout, stderr = client.exec_command(cmd)
            print(stdout.read().decode().strip())
            err = stderr.read().decode().strip()
            if err:
                print(f"[Stderr]: {err}")
                
        client.close()
        
    except Exception as e:
        print(f"Debug failed: {e}")

if __name__ == "__main__":
    HOST = "184.174.33.249"
    USER = "root"
    PASS = "Jram1992@!"
    
    debug_server(HOST, USER, PASS)
