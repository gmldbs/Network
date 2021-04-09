import sys
import time
import threading
import socket

guarantee_send = -1
TIME_OUT = 1
duplicated_cnt = 0
AvgRTT = 0
sendRTT = {}
lock = threading.Lock()
send_number = 0
def make_packet(seq_num, data = b''):
    seq_bytes = seq_num.to_bytes(4, byteorder = 'little', signed = True)
    return seq_bytes + data

def recvAck(recvAddr, logFile, packets, num_packets, windowSize, sock, start):
    global guarantee_send, TIME_OUT, duplicated_cnt, AvgRTT, sendRTT, send_number
    devRTT = 0
    while True:
        if(guarantee_send == num_packets-1): break
        try:
            data, addr = sock.recvfrom(1024)
        except:
            print('sender len packets -1 loss break')
            break
        recieved_ACK = data.decode()
        isBuf = 0
        recieved_ACK = recieved_ACK.split('_')
        recieved_by_send_number = int(recieved_ACK[1])
        recieved_ACK=int(recieved_ACK[0])
        writeAck(logFile, time.time()-start,recieved_ACK,'received')
        if(recieved_ACK == num_packets-2):
            sock.settimeout(3)
        if(guarantee_send<recieved_ACK):
            sampleRTT = time.time()-sendRTT[recieved_by_send_number]
            AvgRTT = (0.875 * AvgRTT) + (0.125 * sampleRTT)
            devRTT = 0.75*devRTT + 0.25*abs(sampleRTT - AvgRTT)
            TIME_OUT = AvgRTT + (4*devRTT)
            if TIME_OUT < 0.1: TIME_OUT = 0.1
            duplicated_cnt = 0
            guarantee_send = recieved_ACK
            if(num_packets - 1 >= guarantee_send + windowSize):
                lock.acquire()
                send_number_bytes = send_number.to_bytes(8, byteorder = 'little',signed=True)
                send_msg = send_number_bytes + packets[guarantee_send+windowSize]
                sock.sendto(send_msg, (recvAddr, 10080))
                sendRTT[send_number] = time.time()
                send_number+=1
                writePkt(logFile, time.time()-start, guarantee_send+windowSize, 'sent')
                lock.release()
        elif(guarantee_send == recieved_ACK):
            duplicated_cnt += 1
            if(duplicated_cnt >=3):
                lock.acquire()
                send_number_bytes = send_number.to_bytes(8, byteorder = 'little',signed=True)
                send_msg = send_number_bytes + packets[guarantee_send+1]
                sock.sendto(send_msg, (recvAddr, 10080))
                sendRTT[send_number]=time.time()
                send_number+=1
                duplicated_cnt=0
                writePkt(logFile, time.time()-start, guarantee_send+1, 'retransmitted')
                lock.release()
    sock.sendto(str.encode('Fin'), (recvAddr, 10080))
    sock.settimeout(1)
    try:
        data, addr = sock.recvfrom(1024)
    except:
        print('settimeout in Fin!')
    throughPut = num_packets / (time.time() - start)
    writeEnd(logFile,throughPut,AvgRTT*1000)
    sock.close()
#"Use this method to write Packet log"
def writePkt(logFile, procTime, pktNum, event):
    logFile.write('{:1.3f} pkt: {} | {}\n'.format(procTime, pktNum, event))

#"Use this method to write ACK log"
def writeAck(logFile, procTime, ackNum, event):
    logFile.write('{:1.3f} ACK: {} | {}\n'.format(procTime, ackNum, event))

#"Use this method to write final throughput log"
def writeEnd(logFile, throughput, avgRTT):
    logFile.write('File transfer is finished.\n')
    logFile.write('Throughput : {:.2f} pkts/sec\n'.format(throughput))
    logFile.write('Average RTT : {:.1f} ms\n'.format(avgRTT))

def fileSender(recvAddr, windowSize, srcFilename, dstFilename):
    print('sender program starts...')
    global guarantee_send, duplicated_cnt, TIME_OUT, AvgRTT, send_number
    buf = 1024
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
    sock.bind(('', 10080))
    start = time.time()
    log_file_name = srcFilename+"_sending_log.txt"
    logFile = open(log_file_name,"w")
    f = open(srcFilename, "rb")
    packets = []
    pktNum = 0
    packets.append(make_packet(pktNum, str.encode(dstFilename)))
    pktNum+=1
    while True:
        data = f.read(buf)
        if not data:
            break
        packets.append(make_packet(pktNum, data))
        pktNum += 1
    packets.append(make_packet(pktNum,b''))
    num_packets = len(packets)
    print('number of packets : {}'.format(num_packets))
    th = threading.Thread(target=recvAck, args=(recvAddr, logFile, packets, num_packets, windowSize, sock, start))
    th.start()
    cur = 0
    while cur < windowSize:
        lock.acquire()
        send_number_bytes = send_number.to_bytes(8, byteorder = 'little',signed=True)
        send_msg = send_number_bytes + packets[cur]
        sock.sendto(send_msg, (recvAddr, 10080))
        sendRTT[send_number]=time.time()
        writePkt(logFile, time.time()-start, cur, 'sent')
        cur+=1
        send_number+=1
        lock.release()
    while True:
        if(guarantee_send == num_packets - 2):
            break
        if(time.time()-sendRTT[send_number-1]>TIME_OUT):
            lock.acquire()
            send_number_bytes = send_number.to_bytes(8, byteorder = 'little',signed=True)
            send_msg = send_number_bytes + packets[guarantee_send+1]
            sock.sendto(send_msg, (recvAddr, 10080))
            out_time = sendRTT[send_number-1] - start + TIME_OUT
            logFile.write('{:1.3f} pkt: {} | timeout since {:1.3f}(timeout value {:1.3f})\n'.format(time.time()-start, guarantee_send+1, out_time, TIME_OUT))
            writePkt(logFile, time.time()-start, guarantee_send+1, 'retransmitted')
            sendRTT[send_number]=time.time()
            send_number+=1
            lock.release()
            #time.sleep(TIME_OUT)
   
    print("sender end")
    f.close()

if __name__=='__main__':
    print("sender py")
    recvAddr = sys.argv[1]  #receiver IP address
    windowSize = int(sys.argv[2])   #window size
    srcFilename = sys.argv[3]   #source file name
    dstFilename = sys.argv[4]   #result file name
    fileSender(recvAddr, windowSize, srcFilename, dstFilename)
