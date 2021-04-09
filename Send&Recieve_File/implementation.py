from threading import Thread
import time
start = time.time()
log_file = open('log.txt','w')
log_file.close()
def copy_process(origin, copy):
    log_file = open('log.txt','a')
    log_file.write('{:.2f}\tStart copying {} to {}\n'.format(time.time()-start,origin,copy))
    log_file.close()
    f1 = open(origin,'rb')
    f2 = open(copy,'wb')
    while True:
        s = f1.read(10000)
        len = f2.write(s)
        if(len<10000): break
    f1.close()
    f2.close()
    log_file = open('log.txt','a')
    log_file.write('{:.2f}\t{} is copied completely\n'.format(time.time()-start,copy))
    log_file.close()
    return

while True:
    origin_filename = input("Input the file name: ")
    if(origin_filename=='exit'): break
    copy_filename = input('Input the new name: ')
    th = Thread(target=copy_process, args=(origin_filename,copy_filename))
    th.start()



