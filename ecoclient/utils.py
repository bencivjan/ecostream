import time
from datetime import datetime
import socket
import subprocess

MIN_CPU_FREQ = 1500000
MAX_CPU_FREQ = 2400000
CPU_FREQ_DELTA = 300000

def connect_socket(sock: socket.socket, args):
    while True:
        try:
            sock.connect((args.server_ip, args.server_port))
            break
        except OSError:
            print("Unable to connect to server socket, retrying...")
            datetime_obj = datetime.fromtimestamp(time.time())
            readable_time = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
            with open("errors.out", "a") as err_file:
                err_file.write(f'{readable_time}: Unable to connect to server at {args.server_ip}\n')
            time.sleep(5)

# Scaling governor must be set to userspace
# `sh -c 'sudo cpufreq-set -g userspace'`
def set_cpu_freq(cpu_freq):
    with open('/sys/devices/system/cpu/cpufreq/policy0/scaling_governor', 'r') as file:
        assert file.read().strip() == 'userspace', 'Scaling governor must be set to userspace\n`sudo cpufreq-set -g userspace`'
    
    cpu_freq = str(cpu_freq)
    print(f'Setting cpu freqency to {cpu_freq} KHz')

    command = f"echo {cpu_freq} | sudo tee /sys/devices/system/cpu/cpufreq/policy0/scaling_setspeed"
    result = subprocess.run(command, shell=True, text=True, capture_output=True)

    if result.returncode == 0:
        print("Successfully set cpu frequency")
    else:
        print("Failed to set cpu frequency")
        print(f"Error: {result.stderr}")

def throttle(target_fps, start_time):
    if target_fps == 0:
        raise ArithmeticError
    # Calculate the time to wait between frames
    frame_time = 1.0 / target_fps

    elapsed_time = time.time() - start_time
    time_to_wait = frame_time - elapsed_time
    if time_to_wait > 0:
        time.sleep(time_to_wait)
        return True
    else:
        return False

def recalibrate(goal_fps, actual_fps):
    return max(goal_fps + (goal_fps - actual_fps), 1)