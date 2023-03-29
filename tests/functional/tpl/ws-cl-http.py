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

import socket
import time
import sys

HOST = sys.argv[1]
PORT = int(sys.argv[2])
PATH = sys.argv[3]

ws_req = (
        bytes('GET {} HTTP/1.1\r\n'.format(PATH), 'utf-8') +
        bytes('Host: {}:{}\r\n'.format(HOST, PORT), 'utf-8') +
        b'Upgrade: websocket\r\n'
        b'Connection: Upgrade\r\n'
        b'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n'
        b'Sec-WebSocket-Version: 13\r\n\r\n'
        )

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

serv_addr = (HOST, PORT)
print("Connecting to {}:{}".format(*serv_addr))
sock.connect(serv_addr)

try:
    sock.sendall(ws_req)

    is_done = False
    resp_msg = b""

    while not is_done:
        data = sock.recv(128)
        resp_msg += data
        if b'\r\n\r\n' in resp_msg:
            is_done = True

    print("Received: {!r}".format(resp_msg))

    for _ in range(10):
        sock.sendall(b"Hello from the client!")
        data = sock.recv(128)
        print("WS Received: {!r}".format(data))
        time.sleep(1)

    sock.sendall(b"close")

finally:
    sock.close()
