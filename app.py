import os
import subprocess
import sys
import time
import pwd
import re

os.environ["PATH"] += ":/usr/games:/usr/lib/games"
def no_traceback(exctype, value, tb):
    print("Unknown: Try re-run again.")

sys.excepthook = no_traceback

def run(cmd, show_output=False):
    if show_output:
        print(f"Running: {cmd}")
        subprocess.run(cmd, shell=True, check=True)
    else:
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def optional_input(prompt, default="n"):
    try:
        return input(prompt).strip().lower() or default
    except:
        return default

def user_exists(username):
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        return False

def backup_user():
    # Kill all user processes first
    run("pkill -KILL -u user || true", show_output=True)
    
    if not os.path.ismount("/content/drive"):
        print("Drive not mounted. Skipping backup.")
        return
    print("\nMake sure you deleted old backup.tar.gz in drive first otherwise it will error")
    ans = optional_input("Do you want to back up /home/user? (y/n): ", "n")
    if ans == "y":
        print("Backing up to Google drive...(5-30m)")
        if not os.path.isdir("/home/user"):
            print("/home/user does not exist. Backup aborted.")
            sys.exit(1)
        backup_cmd = "tar -cf - -C /home/user ./ | pigz -9 > /content/drive/MyDrive/backup.tar.gz"
        ret = subprocess.run(backup_cmd, shell=True)
        if ret.returncode == 0:
            print("Backup completed successfully. It may take some time to appear in Google Drive.")
        else:
            print("Backup failed.")
            sys.exit(1)
    else:
        print("Backup cancelled.")

def restore_backup():
    if not os.path.ismount("/content/drive"):
        print("Drive not mounted. Skipping restore.")
        return
    if not os.path.exists("/content/drive/MyDrive/backup.tar.gz"):
        print("Backup file not found!")
        sys.exit(1)
    run("echo 'root:123456' | sudo chpasswd")
    if not user_exists("user"):
        run("sudo useradd -m user")
    run("echo 'user:123456' | sudo chpasswd")
    run("sudo chown -R user:user /home/user")
    run("pigz -dc /content/drive/MyDrive/backup.tar.gz | tar -xvf - -C /home/user")

def get_tailscale_ip():
    try:
        ip = subprocess.check_output("tailscale ip -4", shell=True, text=True).strip()
        print(f"Tailscale IP: {ip}")
    except subprocess.CalledProcessError:
        print("Failed to get Tailscale IP.")

def get_tailscale_nearest_region():
    try:
        output = subprocess.check_output("tailscale netcheck", shell=True, text=True)
        match = re.search(r"Nearest DERP:\s*(\S+)", output)
        if match:
            region = match.group(1)
            print(f"Connected Tailscale region: {region}")
            return region
        else:
            print("Could not find nearest DERP region.")
    except subprocess.CalledProcessError:
        print("Failed to run tailscale netcheck.")

def main():
    print("Colab GPU Gaming")
    print("Preparing installation files. Please wait...")
    run("wget -qO- https://github.com/OkamuraYuji/Colab-Gaming/releases/download/1.0.0/packages.tar.gz | pigz -dc | tar -xv -C /")
    run('echo -e \'#!/bin/sh\\nexport PATH="$PATH:/usr/games:/usr/lib/games"\' | sudo tee /etc/profile.d/custom_path.sh > /dev/null && sudo chmod +x /etc/profile.d/custom_path.sh')

    #run("curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/focal.noarmor.gpg | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null")
    #run("curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/focal.tailscale-keyring.list | sudo tee /etc/apt/sources.list.d/tailscale.list")
    #run("apt-get install -y tailscale")
    run("curl -L https://pkgs.tailscale.com/stable/tailscale_1.84.0_amd64.tgz | sudo tar --strip-components=1 -xzv -C /usr/local/bin")
    run("mkdir -p /var/lib/tailscale")
    run("nohup bash -c \"while true; do TS_DEBUG_ALWAYS_USE_DERP=true tailscaled --tun=userspace-networking --socket=/run/tailscale/tailscaled.sock --port 41641 ; sleep 1; done\" &")
    run("tailscale up", show_output=True)
    get_tailscale_ip()
    get_tailscale_nearest_region()

    print("User and root pass are 123456.")

    if os.path.exists("/content/drive"):
        if optional_input("Do you want to restore the backup? (y/n): ", "n") == "y":
            print("Restoring backup...")
            restore_backup()
        else:
            print("Skipped restore.")
    else:
        print("Not mounting. Skipping restore.")

    try:
        run("nvidia-smi")
    except subprocess.CalledProcessError:
        print("nvidia-smi not found or not working. Exiting.")
        sys.exit(1)

    print("Sit back and relax. Installing... (2m)")
    
    run('dpkg --add-architecture i386; apt update')
    run('rm -rf /usr/share/doc/libc6/changelog.Debian.gz')
    run('dpkg --add-architecture i386 && sudo DEBIAN_FRONTEND=noninteractive dpkg -i /packages/*.deb ; sudo DEBIAN_FRONTEND=noninteractive apt-get install --fix-broken -y -o Dir::Cache::archives="/packages"')
    run('apt install tint2 -y')

   #run("DEBIAN_FRONTEND=noninteractive apt install -y xvfb x11-xserver-utils libvulkan1 dbus-x11 mesa-utils pulseaudio xorg xserver-xorg x11-utils x11-apps ")
    run("echo \"mode: off\" > ~/.xscreensaver")
    run("chmod +x /packages/NVIDIA*.run && echo 1 | /packages/NVIDIA*.run --no-kernel-module --ui=none")
    #run("ver=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader) && url=\"https://us.download.nvidia.com/tesla/${ver}/NVIDIA-Linux-x86_64-${ver}.run\" && curl -fSL -o nvidia.run \"$url\" && chmod +x nvidia.run && echo 1 | ./nvidia.run --no-kernel-module --ui=none")
   # run("apt-get update")
   # run("sudo apt install -y x11vnc")
    run("mkdir -p ~/.config/sunshine")
   # run("sudo apt remove -y xscreensaver")
    run("echo \"mode: off\" > ~/.xscreensaver")
    run("echo 'root:123456' | sudo chpasswd")

    if not user_exists("user"):
        run("sudo useradd -m user")
    run("echo 'user:123456' | sudo chpasswd")
    run("sudo usermod -aG root user")

    run("nvidia-xconfig -a --allow-empty-initial-configuration --virtual=1920x1080 --busid PCI:0:4:0")
    run("nohup sudo Xorg :1 -seat seat-1 -allowMouseOpenFail -novtswitch -nolisten tcp &")
   # run("nohup x11vnc -display :1 -wait 1000 -defer 1000 -rfbport 5900 -shared -forever &")
    run("sleep 2")

    run("DISPLAY=:1 xhost +local:")

    # Clone noVNC repo only if folder doesn't exist
  #  if not os.path.isdir("/tmp/noVNC"):
  #     run("git clone https://github.com/novnc/noVNC.git /tmp/noVNC")
  #     run("cd /tmp/noVNC && git fetch && git checkout v1.6.0")

  #  run("ln -sf vnc.html /tmp/noVNC/index.html")
    #run("chmod +x /tmp/noVNC/utils/novnc_proxy")

     # Launch noVNC via novnc_proxy directly
  #  no_vnc_cmd = 'nohup bash -c "while true; do /tmp/noVNC/utils/novnc_proxy --vnc localhost:5900 --listen 0.0.0.0:80; sleep 2; done" > /tmp/noVNC/novnc.log 2>&1 &'
  #  run(no_vnc_cmd, show_output=False)
    
    run("DISPLAY=:1 xrandr --output DVI-D-0 --mode 1920x1080")
    run("DISPLAY=:1 xrandr --output DVI-D-0 --rate 60")
  #  run("DISPLAY=:1 xrandr --verbose")

   # run("sudo add-apt-repository universe -y")
   # run("sudo add-apt-repository multiverse -y")
   # run("sudo apt update")
   # run("dpkg --add-architecture i386; apt update")
  #  run("apt install -y libc6:amd64 libc6:i386 libegl1:amd64 libegl1:i386 libgbm1:amd64 libgbm1:i386 libgl1-mesa-dri:amd64 libgl1-mesa-dri:i386 libgl1:amd64 libgl1:i386")
  #  run("apt install steam openbox thunar htop nvtop pciutils xvkbd feh p7zip-full p7zip-rar xfce4-terminal -y")
     
   # run("wget https://github.com/LizardByte/Sunshine/releases/download/v0.23.1/sunshine-ubuntu-22.04-amd64.deb -O sunshine.deb && sudo apt install -y ./sunshine.deb")
   # run("wget https://github.com/Heroic-Games-Launcher/HeroicGamesLauncher/releases/download/v2.17.0/Heroic-2.17.0-linux-amd64.deb; apt install -f ./Heroic-2.17.0-linux-amd64.deb")
   # run('sudo wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && sudo dpkg -i google-chrome-stable_current_amd64.deb && sudo apt --fix-broken install -y', show_output=False)
    run("cp /packages/wallpaper.jpg /home/user/")
    run("su - user -c \"nohup pulseaudio --exit-idle-time=-1 &\"")
    run("su - user -c \"DISPLAY=:1 nohup openbox &\"")
    run("su - user -c \"DISPLAY=:1 feh --bg-scale ~/wallpaper.jpg\"")
    run("su - user -c \"rm -rf ~/.config/sunshine ;DISPLAY=:1 nohup sunshine &\"")
    run('su - user -c "DISPLAY=:1 nohup google-chrome &"')
    run("su - user -c \"DISPLAY=:1 nohup thunar &\"")
    run("su - user -c \"DISPLAY=:1 nohup heroic &\"")

   
    
    pin = input("Enter Moonlight PIN: ").strip()
    curl_passwd = f'curl -u admin:admin -X POST -k https://localhost:47990/api/password -H "Content-Type: application/json" -d \'{{"currentUsername":"admin","currentPassword":"admin","newUsername":"admin","newPassword":"admin","confirmNewPassword":"admin"}}\''
    curl_pin = f'curl -u admin:admin -X POST -k https://localhost:47990/api/pin -H "Content-Type: application/json" -d \'{{"pin":"{pin}","name":"my-moonlight-device"}}\''
    run(curl_passwd, show_output=True)
    run(curl_pin, show_output=True)

    print("Setup completed. Press pause colab to initiate backup or exit.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCtrl+C detected.")
        backup_user()
        print("Exiting.")
        sys.exit(0)