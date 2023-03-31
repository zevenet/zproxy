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

# Usage: ws-cl-http.py <host> <port> <ssl> <path>

import socket
import time
import sys
import ssl
from threading import Thread

HOST = sys.argv[1]
PORT = int(sys.argv[2])
SSL = int(sys.argv[3])
PATH = sys.argv[4]

running = True

ws_req = (
        bytes('GET {} HTTP/1.1\r\n'.format(PATH), 'utf-8') +
        bytes('Host: {}:{}\r\n'.format(HOST, PORT), 'utf-8') +
        b'Upgrade: websocket\r\n'
        b'Connection: Upgrade\r\n'
        b'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n'
        b'Sec-WebSocket-Version: 13\r\n\r\n'
        )

if SSL > 0:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    context = ssl._create_unverified_context()
    sock = context.wrap_socket(s)
else:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def handle_recv():
    global running
    global sock

    while running:
        try:
            resp_msg = sock.recv(128)
        except:
            break

        if not resp_msg:
            break

        print("WS Received: {!r}".format(resp_msg))

serv_addr = (HOST, PORT)
print("Connecting to {}:{}".format(*serv_addr))
sock.connect(serv_addr)

recv_thread = Thread(target=handle_recv)
try:
    # Upgrade protocols
    sock.sendall(ws_req)

    resp_msg = b""
    while True:
        data = sock.recv(128)
        resp_msg += data
        if b"\r\n\r\n" in resp_msg:
            break

    print("Received: {!r}".format(resp_msg))
    if not b"101 Switching Protocols" in resp_msg:
        print("ERROR: Didn't upgrade protocols")
        raise Exception("Server didn't upgrade protocols")

    # in WebSocket mode
    recv_thread.start()

    for _ in range(10):
        sock.sendall(b"Hello from the client!")
        time.sleep(0.1)

    sock.sendall(b"close")

    running = False
    time.sleep(0.5)
finally:
    sock.shutdown(socket.SHUT_RDWR)
    recv_thread.join()
    sock.close()
