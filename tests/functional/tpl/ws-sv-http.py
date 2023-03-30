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

SSL = int(sys.argv[1])

def handle_exit(signal, frame):
    print("Exit")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)

ws_resp = (
        b'HTTP/1.1 101 Switching Protocols\r\n'
        b'Upgrade: websocket\r\n'
        b'Connection: Upgrade\r\n'
        b'Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=\r\n\r\n'
        )

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

if SSL > 0:
    serv_addr = ('', 8443)
else:
    serv_addr = ('', 8080)
print("Running on {}:{}".format(*serv_addr))
sock.bind(serv_addr)

sock.listen(1)

while True:
    if SSL > 0:
        raw_conn, cl_addr = sock.accept()
        try:
                conn = ssl.wrap_socket(raw_conn, server_side=True, certfile="nginx.pem",
                        keyfile="nginx.key")
        except:
                # if exception is caused, this connection is from the zproxy
                # monitor
                continue
    else:
        conn, cl_addr = sock.accept()

    try:
        req_data = b""
        while True:
            data = conn.recv(128)
            if data == b'':
                break

            req_data += data
            if b'\r\n\r\n' in req_data:
                break

        if not req_data:
            continue

        print("Received: {!r}".format(req_data))
        conn.sendall(ws_resp)

        while data != b"close":
            data = conn.recv(128)
            print("WS Received: {!r}".format(data))
            conn.sendall(b"Hello from the server!")

    finally:
        conn.close()
