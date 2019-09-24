import errno
import os
import signal
import socket
import datetime

def zombie_handler(signum, frame):
    while True:
        try:
            pid, status = os.waitpid(-1,os.WNOHANG )
        except OSError:
            return

        if pid == 0:
            return


def work(connectionSocket):
    request = connectionSocket.recv(1024).decode()
    split_request = request.split(' ')
    request_method = split_request[0]
    print("[METHOD]: ", request_method)
    print("[REQUEST]: ", request)


    try:
        if(request_method == 'GET'):
            file_name = split_request[1]
            if(file_name == '/'):
                http_response = 'HTTP/1.1 302 FOUND\r\nLocation:/index.html\r\n'
                connectionSocket.sendall(http_response.encode())

            elif file_name == '/index.html':
                f = open(file_name[1:], "rb")
                print("[FILE OPENED] : ", file_name)
                ext = file_name[file_name.rfind(".")+1:]
                data = f.read()
                header = ('HTTP/1.1 200 OK\r\nContent-Length: {}\r\nContent-Type:text/html\r\n\r\n').format(len(data)).encode()

                http_response = header + data
                connectionSocket.sendall(http_response)

            elif file_name == '/cookie.html':
                user_id_start = request.find('id=')
                if user_id_start == -1 :
                    header = ('HTTP/1.1 403 Forbidden\r\n') 
                    connectionSocket.sendall(header.encode())
                else:
                    user_id = request[user_id_start:]
                    user_id = user_id.split('=')[1]
                    user_id = user_id.split(';')[0]

                    expire_time_start = request.find('id_expires=')+11
                    expire_time = request[expire_time_start:].split('\r\n')[0]
                    expire_time = expire_time.split(';')[0].strip()

                    i=datetime.datetime.now()
                    cur_time = i.minute*60 + i.second

                    expires = 30 - (cur_time - int(expire_time))
                    header = 'HTTP/1.1 200 OK\r\nContent-Type:text/html\r\n\r\n'
                    data = '<html><head><title>Hello %s</title></head>' %user_id
                    data +='<body><p>%d seconds left until your cookie expires</p></body></html>' %expires

                    http_response = header + data
                    connectionSocket.sendall(http_response.encode())

            else:
                f = open(file_name[1:], "rb")
                user_id_start = request.find('id=')
                if user_id_start == -1 :
                    header = ('HTTP/1.1 403 Forbidden\r\n')
                    connectionSocket.sendall(header.encode())
                else:
                    user_id = request[user_id_start:]
                    user_id = user_id.split('=')[1]
                    user_id = user_id.split(';')[0]
                    print("[FILE OPENED] : ", file_name)
                    ext = file_name[file_name.rfind(".")+1:]
                    if ext == 'html':
                        header = ('HTTP/1.1 200 OK\r\nContent-Type:text/html\r\n\r\n').encode()
                        fdata = '<html><head><title>Welcome to %s</title><link rel="icon" href="data:,"></head>' %user_id
                        header = header + fdata.encode()
                    elif ext == 'jpg':
                        header = ('HTTP/1.1 200 OK\r\nContent-Type:Image/jpeg\r\n\r\n').encode()
                    elif ext == 'mp4':
                        header = ('HTTP/1.1 200 OK\r\nContent-Type:video/mp4\r\n\r\n').encode()
                    elif ext == 'pdf':
                        header = ('HTTP/1.1 200 OK\r\nContent-Type:application/pdf\r\n\r\n').encode()

                    http_response = header
                    connectionSocket.sendall(http_response)


                    data = f.read(1024)
                    while data:
                        connectionSocket.sendall(data)
                        data = f.read(1024)


        elif(request_method == 'POST'):
            print("POST method...")
            file_name = split_request[1]
            if file_name == '/index.html':
                id_start = request.find('login')+6
                id_fin = request.find('&password')
                login_id = request[id_start:id_fin]
                header = 'HTTP/1.1 302 FOUND\r\nLocation:/secret.html\r\nset-Cookie:id=%s;Max-age=30\r\n' % login_id

                i = datetime.datetime.now()
                cur_time = i.minute*60 + i.second
                header += 'set-Cookie:id_expires=%s\r\n\r\n' %cur_time

            http_response = header
            connectionSocket.sendall(http_response.encode())


        else:
            print("Unknown method...")

    except FileNotFoundError:
        print("File not exist, sending 404 error")
        http_response = 'HTTP/1.1 404 Not Found\r\n'
        connectionSocket.sendall(http_response.encode('utf-8'))


def serve_forever():
    serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serv_sock.bind(('',10080))
    serv_sock.listen(100)
    print('Serving HTTP on port 10080 ...')

    signal.signal(signal.SIGCHLD, zombie_handler)
    try:
        while True:
            try:
                connectionSocket, client_address = serv_sock.accept()
            except IOError as e:
                code, msg = e.args
                if code == errno.EINTR:
                    continue
                else:
                    raise

            pid = os.fork()
            if pid == 0: 
                serv_sock.close() 
                work(connectionSocket)
                connectionSocket.close()
                os._exit(0)
            else:
                connectionSocket.close()
    except KeyboardInterrupt:
        serv_sock.close()

if __name__ == '__main__':
    serve_forever()
