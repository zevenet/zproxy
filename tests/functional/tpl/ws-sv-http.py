#!/usr/bin/env python3

# Copyright (C) 2023  Zevenet S.L. <support@zevenet.com>
# Author: Ortega Froysa, Nicolás <nicolas.ortega@zevenet.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import signal
import socket
import sys
import ssl
from threading import Thread

SSL = int(sys.argv[1])

running = True

ws_resp = (
        b'HTTP/1.1 101 Switching Protocols\r\n'
        b'Upgrade: websocket\r\n'
        b'Connection: Upgrade\r\n'
        b'Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=\r\n\r\n'
        )

def handle_client(conn):
    buf = b""
    ws_mode = False
    global running
    while running:
        try:
            req_data = conn.recv(128)
        except:
            break

        if not req_data:
            break
        elif not ws_mode:
            buf += req_data
            if b"\r\n\r\n" in buf:
                print("Received: {!r}".format(buf))
                if b"Upgrade: websocket" in buf:
                    ws_mode = True
                    global ws_resp
                    conn.sendall(ws_resp)
                buf = b""
        else:
            print("WS Received: {!r}".format(req_data))
            conn.sendall(b"Hello from the server!")

    conn.close()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def handle_exit(signal, frame):
    print("Exit")
    global running
    running = False
    global sock
    sock.shutdown(socket.SHUT_RDWR)

signal.signal(signal.SIGINT, handle_exit)

if SSL > 0:
    serv_addr = ('', 8443)
else:
    serv_addr = ('', 8080)
print("Running on {}:{}".format(*serv_addr))
sock.bind(serv_addr)

sock.listen()

cl_threads = []

while running:
    try:
        if SSL > 0:
            raw_conn, cl_addr = sock.accept()
            conn = ssl.wrap_socket(raw_conn, server_side=True, certfile="nginx.pem",
                    keyfile="nginx.key")
        else:
            conn, cl_addr = sock.accept()
    except:
        # if exception is caused, this connection is from the zproxy
        # monitor
        continue

    cl_thr = Thread(target=handle_client, args=[conn,])
    cl_thr.start()
    cl_threads.append(cl_thr)

    cl_threads = [ t for t in cl_threads if t.is_alive() ]

for t in cl_threads:
    t.join()
