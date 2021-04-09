import sys
import time
import threading
import socket

serverIP = '10.0.0.3'
serverPort = 10080
clientPort = 10081
clients = {}
isExit = False
def sendServer(sock, clientID, serverIP, serverPort):
    global isExit
    while True:
        time.sleep(10)
        if isExit: break
        sock.sendto(str.encode("alive" +' '+clientID), (serverIP, serverPort))

def recvServer(sock,serverIP, serverPort):
    global clients, isExit
    while True:
        Msg, addr = sock.recvfrom(2000)
        #print(Msg.decode())
        if isExit: break
        Msg = str(Msg.decode())
        find_idx = Msg.index(' ')
        kind = Msg[:find_idx]
        Msg = Msg[find_idx+1:]
        if kind == 'registration':
            clientID_idx = Msg.index(' ')
            clientID = Msg[:clientID_idx]
            Msg = Msg[clientID_idx+1:]
            clientInfo_idx = Msg.index(' ')
            clientInfo = Msg[:clientInfo_idx]
            client_priInfo = Msg[clientInfo_idx+1:]
            if clientID not in clients :
                #print("#{} is registered.".format(clientID))
                new = {}
                client_pubIp_idx = clientInfo.index(":")
                client_pubIp = clientInfo[:client_pubIp_idx]
                client_pubPort = clientInfo[client_pubIp_idx+1:]
                client_priIp_idx = client_priInfo.index(":")
                client_priIp = client_priInfo[:client_priIp_idx]
                client_priPort = client_priInfo[client_priIp_idx+1:]
                new["public_ip"] = client_pubIp
                new["public_port"] = client_pubPort
                new["private_ip"] = client_priIp
                new["private_port"] = client_priPort
                clients[clientID] = new
        elif kind == 'deregistration':
            #print("#{} is deregistered.".format(Msg))
            del(clients[Msg])
        elif kind == 'message':
            clientID_idx = Msg.index(' ')
            clientID = Msg[:clientID_idx]
            Message = Msg[clientID_idx+1:]
            print("From {} [{}]".format(clientID, Message))
        elif kind == 'disappear':
            #print("#{} is disappeared.".format(Msg))
            del(clients[Msg])

def client(serverIP, serverPort, clientID):
    global clients, isExit
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
    sock.connect((serverIP,serverPort))
    my_ip = sock.getsockname()[0]
    my_port = sock.getsockname()[1]
    sock.close()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('',clientPort))
    #print(sock.getsockname())
    #print("clientID : {}".format(clientID))
    th1 = threading.Thread(target=sendServer, args=(sock, clientID, serverIP, serverPort))
    th1.start()
    th2 = threading.Thread(target=recvServer, args=(sock, serverIP, serverPort))
    th2.start()
    sock.sendto(str.encode('registration '+clientID+' '+str(my_ip)+' '+str(my_port)),(serverIP, serverPort))
    while True:
        cli_input = input("")
        cli_input = cli_input.split(" ")
        if cli_input[0]=="@chat":
            to_cli = cli_input[1]
            cli_sendMSG = ' '.join(cli_input[2:])
            if to_cli not in clients:
                print("Recevier doesn't exist. ({})".format(to_cli))
                continue
            if clients[to_cli]["public_ip"] == clients[clientID]["public_ip"]:
                sock.sendto(str.encode('message '+clientID+" "+cli_sendMSG), (clients[to_cli]["private_ip"],clientPort))
            else:
                sock.sendto(str.encode('message '+clientID+" "+cli_sendMSG), (clients[to_cli]["public_ip"],int(clients[to_cli]["public_port"])))
        elif cli_input[0]=="@exit":
            isExit = True
            sock.sendto(str.encode('exit'+' '+clientID), (serverIP, serverPort))
            break
        elif cli_input[0]=="@show_list":
            for client in clients:
                print("{}\t {}:{}".format(client, clients[client]["public_ip"], clients[client]["public_port"]))
    print("Exit successfully.")
"""
Don't touch the code below!
"""
if  __name__ == '__main__':
    clientID = str(input("Enter ID: "))
    client(serverIP, serverPort, clientID)


