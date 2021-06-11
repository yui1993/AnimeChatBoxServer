# AnimeChatBoxServer
A chat server using websockets and a way to verify emails and password recovery only if using self hosted email server
 
 # Must be run on linux
 its safe to run as root or with sudo
 
 
 # run
 ```shell
 python3 -m pip install -r requirements.txt
 root only required for ports 80/443
 sudo python3 webserver.py #techincally don't need to run as root unless you set a port that requires it
 sudo python3 server.py
 ```
 
