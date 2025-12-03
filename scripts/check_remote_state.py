import paramiko
import sys

def check_server(hostname, username, password):
    print(f"Connecting to {hostname}...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username, password=password)
        
        commands = [
            "uptime",
            "df -h | grep '/$'",
            "free -m",
            "systemctl status energyapp-api energyapp-web --no-pager",
            "cd /root/energyapp-llm-platform && git status"
        ]
        
        for cmd in commands:
            print(f"\n--- Running: {cmd} ---")
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if output:
                print(output)
            if error:
                print(f"Error/Stderr: {error}")
                
        client.close()
        print("\nConnection closed.")
        
    except Exception as e:
        print(f"Failed to connect or execute commands: {e}")

if __name__ == "__main__":
    # Credentials provided by user
    HOST = "184.174.33.249"
    USER = "root"
    PASS = "Jram1992@!"
    
    check_server(HOST, USER, PASS)
