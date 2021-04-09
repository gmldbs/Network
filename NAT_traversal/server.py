import sys
import threading
import socket
import time
serverPort = 10080
clients = {}
lock = threading.Lock()

def checkCli(sock):
    global clients
    while True:
        lock.acquire()
        for client in clients:
            if clients[client]["live_time"]+30 < time.time():
                print("{} is disappeared".format(client))
                for info in clients:
                    sock.sendto(str.encode('disappear '+client),(clients[info]["public_ip"],clients[info]["public_port"]))
                del clients[client]
                break
        lock.release()

def server():
    global clients
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
    sock.bind(('', serverPort))
    th = threading.Thread(target = checkCli, args = (sock,))
    th.start()
    while True:
        Msg, addr = sock.recvfrom(2000)
        Msg = str(Msg.decode())
        kind_idx = Msg.index(' ')
        kind = Msg[:kind_idx]
        Msg = Msg[kind_idx+1:]
        if kind == 'exit':
            print("{} is deregistered\t{}:{}".format(Msg, clients[Msg]["public_ip"],clients[Msg]["public_port"]))
            for client in clients:
                sock.sendto(str.encode('deregistration '+Msg),(clients[client]["public_ip"],clients[client]["public_port"]))
            lock.acquire()
            del(clients[Msg])
            lock.release()
            #print("Delete {} from clients list.".format(Msg))
        elif kind == 'registration':
            cli_ID_idx = Msg.index(' ')
            cli_ID = Msg[:cli_ID_idx]
            Msg = Msg[cli_ID_idx+1:]
            pri_ip_idx = Msg.index(' ')
            pri_ip = Msg[:pri_ip_idx]
            pri_port = Msg[pri_ip_idx+1:]
            new = {}
            new["public_ip"] = addr[0]
            new["public_port"] = addr[1]
            new["private_ip"] = pri_ip
            new["private_port"] = pri_port
            new["live_time"] = time.time()
            lock.acquire()
            clients[cli_ID] = new
            lock.release()
            print("{}\t{}:{}".format(cli_ID,addr[0],addr[1]))
            for client in clients:
                for info in clients:
                    sock.sendto(str.encode("registration "+info+" "+str(clients[info]["public_ip"])+':'+str(clients[info]["public_port"])+" "+str(clients[info]["private_ip"])+':'+str(clients[info]["private_port"])),(clients[client]["public_ip"],clients[client]["public_port"]))
                #print("socket send to {}".format(client))
            #print("Create {} from clients list.".format(cli_ID))
        elif kind == 'alive':
            clients[Msg]["live_time"] = time.time()
            #print("{} is alive.".format(Msg))
    """
    Write your code!!!
    """
    pass


"""
Don't touch the code below
"""
if  __name__ == '__main__':
    server()


