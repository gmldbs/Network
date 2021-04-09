import socket
import os
import time
from threading import Thread
RESPONSE_TEMPLATE = """HTTP/1.1 200 OK
{headers}

{content}"""

def parse_headers(request):
    headers = {}
    for line in request.split('\n')[1:]:
        if line == '\r':
            break
        header_line = line.partition(':')
        headers[header_line[0].lower()] = header_line[2].strip()
    return headers

def join_response(status, content_type, contents):
    response_joined = b'\r\n'.join([
        bytes("HTTP/1.1 %s" % status,'utf-8'),
        b"Connection: keep-alive",
        bytes("Content-Type %s" % content_type,'utf-8'),
        bytes("Content-Length: %s" % len(contents),'utf-8'),
        b'', contents
    ])
    return response_joined
def join_response_setCookie(status, head,content_type, contents):
    response_joined = b'\r\n'.join([
        bytes("HTTP/1.1 %s" % status,'utf-8'),
        head,
        b"Connection: keep-alive",
        bytes("Content-Type %s" % content_type,'utf-8'),
        bytes("Content-Length: %s" % len(contents),'utf-8'),
        b'', contents
    ])
    return response_joined
def Web_conn(connSock, connAddr):
    try:
        while True:
            request = connSock.recv(5000)
            if not request: break
            request = request.decode()
            headers = parse_headers(request)
            data = request.split('\n')
            data_info = data[0].split(' ')
            filename = ''
            if data_info[1]=='/':
                if 'cookie' in headers: filename = 'secret.html'
                else: filename = 'index.html'
                with open(filename, 'rb') as file_handle:
                    file_contents = file_handle.read()
                    HTTP_RESPONSE = join_response("200 OK","text/html; charset=utf-8",file_contents)
                    connSock.sendall(HTTP_RESPONSE)
                    file_handle.close()
            elif 'login.php' in data_info[1]:
                filename = 'secret.html'
                idx=data_info[1].find('&')
                id = data_info[1][14:idx]
                lease = 30
                end_time = time.time() + lease
                end = time.gmtime(end_time)
                expires = time.strftime("%a, %d-%b-%Y %T GMT", end)
                head = 'Set-Cookie: id = '+id+'; max-age=30'+';\nSet-Cookie: end_time='+str(end_time)+'; max-age=30;'
                head = str.encode(head)
                with open(filename, 'r') as file_handle:
                    file_contents = file_handle.read()
                    file_contents = file_contents.encode()
                    HTTP_RESPONSE = join_response_setCookie("200 OK",head,"text/html; charset=utf-8",file_contents)
                    connSock.sendall(HTTP_RESPONSE)
                    file_handle.close()
            else:
                if 'cookie' in headers:
                    filename = data_info[1][1:]
                    type_info = filename.split('.')
                    if filename == 'cookie.html':
                        left_time_idx = headers['cookie'].find('end_time=')
                        id = headers['cookie'][3:left_time_idx-2]
                        left_time = float(headers['cookie'][left_time_idx+9:])-time.time()
                        content = '<html><head><title>'+'Welcome '+id+'</title></head><body><center><h1>Hello '+id+'</h1><p>'+str(int(left_time))+'seconds left until your cookie expires</p></center></body></html>'
                        content = str.encode(content)
                        HTTP_RESPONSE = join_response("200 OK","text/html; charset=utf-8",content)
                        connSock.sendall(HTTP_RESPONSE)
                    elif not os.path.exists(filename): 
                        content = ''
                        content = str.encode(content)
                        HTTP_RESPONSE = join_response("404 Not Found","text/html; charset=utf-8",content)
                        connSock.sendall(HTTP_RESPONSE)
                    elif type_info[-1] == 'jpg' or type_info[-1] == 'jpeg' or type_info[-1] == 'png':
                        image_file = open(filename, 'rb')
                        data = image_file.read()
                        HTTP_RESPONSE = join_response("200 OK","image/jpg",data)
                        connSock.sendall(HTTP_RESPONSE)
                        image_file.close()
                    elif type_info[-1] == 'html':
                        with open(filename) as file_handle:
                            file_contents = file_handle.read()
                            HTTP_RESPONSE = join_response("200 OK","text/html; charset=utf-8",file_contents)
                            connSock.sendall(HTTP_RESPONSE)
                            file_handle.close()
                else: 
                    content = ''
                    content = str.encode(content)
                    HTTP_RESPONSE = join_response("403 Forbidden","text/html; charset=utf-8",content)
                    connSock.sendall(HTTP_RESPONSE)
    except :
        print('out of loop by except' + connAddr[0]+ ' addr : '+str(connAddr[1]))
    print('out of loop by timeout' + connAddr[0]+ ' addr : '+str(connAddr[1]))
    connSock.close()
            

host = ''
port = 10080
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
sock.bind((host, port))
sock.listen(5)

while True:
    connSock, connAddr = sock.accept()
    print('client connectioned'+ connAddr[0]+ ' addr : '+str(connAddr[1]))
    th = Thread(target=Web_conn, args=(connSock,connAddr))
    th.start()