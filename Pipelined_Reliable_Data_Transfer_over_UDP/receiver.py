import sys
import time
import threading
import socket

def unpack_packet(packet):
    send_num = int.from_bytes(packet[0:8], byteorder = 'little', signed = True)
    pkt_num = int.from_bytes(packet[8:12], byteorder = 'little', signed = True)
    return send_num, pkt_num, packet[12:]

#"Use this method to write Packet log"
def writePkt(logFile, procTime, pktNum, event):
    logFile.write('{:1.3f} pkt: {} | {}\n'.format(procTime, pktNum, event))

#"Use this method to write ACK log"
def writeAck(logFile, procTime, ackNum, event):
    logFile.write('{:1.3f} ACK: {} | {}\n'.format(procTime, ackNum, event))

#"Use this method to write final throughput log"
def writeEnd(logFile, throughput):
    logFile.write('File transfer is finished.\n')
    logFile.write('Throughput : {:.2f} pkts/sec\n'.format(throughput))

def writeLog(logfile, contain):
    logfile.write(contain)

def fileReceiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
    sock.bind(('', 10080))
    sock.settimeout(3)
    expected_ACK = 0
    write_file = ''
    log_file_name = ''
    buf = []
    start = time.time()
    print('receiver start!')
    while True:
        packet, addr = sock.recvfrom(2000)
        send_number, ACK, data = unpack_packet(packet)
        if(ACK == 0):
            write_file_name = data.decode()
            write_file = open(write_file_name,"wb")
            log_file_name = write_file_name+"_receiving_log.txt"
            logFile = open(log_file_name,'w')
            writePkt(logFile, time.time()-start,ACK,'received')
            expected_ACK += 1
            sock.sendto(str.encode(str(ACK)+'_'+str(send_number)), (addr[0], 10080))
            writeAck(logFile,time.time()-start,ACK,'sent')
            break
    print('receive file name!')
    finish_idx=-1
    while True:
        try:
            packet, addr = sock.recvfrom(2000)
        except:
            break
        send_number, ACK, data = unpack_packet(packet)
        writePkt(logFile, time.time()-start,ACK,'received')
        if(ACK == expected_ACK):
            sock.sendto(str.encode(str(ACK)+'_'+str(send_number)), (addr[0], 10080))
            writeAck(logFile,time.time()-start,ACK,'sent')
            if(data == b'' or ACK==finish_idx):
                break
            write_file.write(data)
            expected_ACK += 1
            isEmpty = 0
            if(len(buf)>0):
                last = 0
                for i in range(len(buf)):
                    if(buf[i][0]==expected_ACK):
                        sendMesg = str(expected_ACK)+'_'+str(send_number)
                        sock.sendto(str.encode(sendMesg), (addr[0], 10080))
                        writeAck(logFile,time.time()-start,expected_ACK,'sent')
                        if(buf[i][1] == b''):
                            isEmpty = 1
                            break
                        write_file.write(buf[i][1])
                        expected_ACK+=1
                        last=i
                del buf[:last]
            if(isEmpty==1):
                break
        elif(ACK > expected_ACK):
            inserted = 0
            for unit_idx in range(len(buf)):
                if (buf[unit_idx][0]==ACK):
                    inserted = 1
                    break
                elif (buf[unit_idx][0]>ACK):
                    buf.insert(unit_idx,(ACK, data))
                    if(data == b''):
                        finish_idx = ACK
                    inserted = 1
                    break
            if(inserted == 0):
                buf.append((ACK, data))
            sock.sendto(str.encode(str(expected_ACK-1)+'_'+str(send_number)), (addr[0], 10080))
            writeAck(logFile,time.time()-start,expected_ACK-1,'sent')
        else:
            sock.sendto(str.encode(str(expected_ACK-1)+'_'+str(send_number)), (addr[0], 10080))
            writeAck(logFile,time.time()-start,expected_ACK-1,'sent')
    sock.settimeout(1)
    try:
        sock.sendto(str.encode('Fin'),(addr[0], 10080))
        data, addr = sock.recvfrom(1024)
        if(data == 'Fin'):
            sock.sendto(str.encode('Fin'),(addr[0], 10080))
    except:
        print('Fin settimeout!')
    ThroughPut = (expected_ACK) / (time.time()-start)
    writeEnd(logFile, ThroughPut)
    print("end recieve function")
    write_file.close()
    sock.close()

if __name__=='__main__':
    print("start receiver.py")
    fileReceiver()
