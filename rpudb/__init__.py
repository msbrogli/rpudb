import sys
import socket
import struct
import fcntl
import termios
import pty
import os
import select
import sys
import signal
import atexit

import pudb

def run_telnet_server(addr, port):
    # Open a 'reusable' socket to let the webapp reload on the same port
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    skt.bind((addr, port))
    skt.listen(1)

    # Writes to stdout are forbidden in mod_wsgi environments
    try:
        sys.stderr.write("pudb is running on %s:%d\n" % skt.getsockname())
    except IOError:
        pass

    (clientsocket, address) = skt.accept()

    # Create pseudo-terminal
    (term_master, term_slave) = pty.openpty()
    # Create file descriptor for stdin
    (stdin_master, stdin_slave) = os.pipe()

    # Telnet control characters (http://www.cs.cf.ac.uk/Dave/Internet/node141.html)
    SE = 240
    SB = 250
    WILL = 251
    WONT = 252
    DO = 253
    DONT = 254
    IAC = 255
    ECHO = 1
    SUPPRESS_GO_AHEAD = 3
    LINEMODE = 34
    NAWS = 31

    # Telnet Linemode Option (http://tools.ietf.org/html/rfc1184)
    clientsocket.sendall(bytearray([IAC, WILL, ECHO, IAC, WILL, SUPPRESS_GO_AHEAD, IAC, WONT, LINEMODE]))
    buf = clientsocket.recv(3)
    buf = struct.unpack('BBB', buf)
    assert(buf == (IAC, DO, ECHO))
    buf = clientsocket.recv(3)
    buf = struct.unpack('BBB', buf)
    assert(buf == (IAC, DO, SUPPRESS_GO_AHEAD))

    # Telnet Window Size Option (https://www.ietf.org/rfc/rfc1073.txt)
    clientsocket.sendall(bytearray([IAC, DO, NAWS]))
    buf = clientsocket.recv(3)
    buf = struct.unpack('BBB', buf)
    assert(buf == (IAC, WILL, NAWS))

    pid = os.fork()
    if pid == 0:
        strIAC = struct.pack('BBB', IAC, SB, NAWS)
        inputs = [clientsocket, term_master]
        print 'Mainloop'
        while True:
            readable, _, _ = select.select(inputs, [], [])
            s = readable[0]
            if s == term_master:
                buf = os.read(term_master, 1000)
                clientsocket.sendall(buf)

            elif s == clientsocket:
                buf = clientsocket.recv(1000)
                idx = buf.find(strIAC)
                if idx >= 0:
                    # Window size: IAC SB NAWS 0 80 0 24 IAC SE
                    cmd = struct.unpack('BBBBBBBBB', buf[idx:idx+9])
                    buf = buf[:idx] + buf[idx+9:]
                    assert(cmd[3] == 0)
                    assert(cmd[5] == 0)
                    assert(cmd[7:] == (IAC, SE))
                    width = cmd[4]
                    height = cmd[6]
                    #print 'Window size:', width, height
                    winsize = struct.pack("HHHH", height, width, 0, 0)
                    fcntl.ioctl(term_master, termios.TIOCSWINSZ, winsize)
                if len(buf) > 0:
                    assert(os.write(stdin_slave, buf) == len(buf))

    return pid, os.fdopen(term_slave, 'w'), os.fdopen(stdin_master, 'r')

def set_trace(addr='127.0.0.1', port=4444):
    # Backup stdin and stdout before replacing them by the socket handle
    old_stdout = sys.stdout
    old_stdin = sys.stdin

    # Run telnet server and get the new fds
    (pid, stdout, stdin) = run_telnet_server(addr, port)
    sys.stdout = stdout
    sys.stdin = stdin

    # Kill children on exit.
    def cleanup():
        print 'Killing server...'
        os.kill(pid, signal.SIGKILL)
    atexit.register(cleanup)
    def signal_handler(signal, frame):
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    # Finally, run pudb
    pudb.set_trace()


if __name__ == '__main__':
    set_trace()

