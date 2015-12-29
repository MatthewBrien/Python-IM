#!/usr/bin/env python2.7
import threading
import socket
import re
import signal
import sys
import time

class Server():
    def __init__(self, port):
        #create a socket and bint it to a port
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.bind(('', port))
        self.listener.listen(1)
        print "Listening on port {0}".format(port)
        #used to store all of the client sockets we have, and for echoing to them
        self.client_sockets = []
        #run the functin self.signal handler when Ctrl-C is pressed
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def run(self):
        while True:
            #listen for clients and create a new clientthre for each new client
            print "Listening for more clients"
            try:
                (client_socket, client_address) = self.listener.accept()
            except socket.error:
                sys.ext("Could not accept any more connections")
            self.client_sockets.append(client_socket)
            print "Starting Client thred for {0}".format(client_address)
            client_thread = ClientListener(self, client_socket, client_address)
            client_thread.start()
            time.sleep(0.1)

    def echo(self, data):
        print "Echoing: {0}".format(data)
        for socket in self.client_sockets:
            #try to echo to all cleints
            try:
                socket.sendall(data)
            except socket.error:
                print "Unable to send message"

    def remove_socket(self, socket):
        #remove the specified socked from the cllient sockets list
        self.client_sockets.remove(socket)

    def signal_handler(self, signal, frame):
        #print when CTRL-C is pressed
        print "Tidying up"
        self.listener.close()
        self.echo("QUIT")

class ClientListener(threading.Thread):
    def __init__(self, server, socket, address):
        super(ClientListener, self).__init__()
        self.server = server
        self.address = address
        self.socket = socket
        self.listening = True
        self.username = "No Username"

    def run(self):
        #the threads loop to recieve and process messages
        while self.listening:
            data = ""
            try:
                data = self.socket.recv(1024) #is this limiting the size of the message that can be received?
            except socket.error:
                "Unable to recieve data"
            self.handle_msg(data)
            time.sleep(0.1)
        #while loop complete
        print "Ending client thread for {0}".format(self.address)

    def quit(self):
    #tidy up at the end of the thread
        self.listening = False
        self.socket.close()
        self.server.remove_socket(self.socket)
        self.server.echo("{0} has quit.\n".format(self.username))

    def handle_msg(self, data):
        #print and then process the message weve recieved
        print "{0} sent: {1}".format(self.address, data)
        #use regualr expression to  test for specific messages
        username_result = re.search('^USERNAME (.*)$', data)
        if username_result:
            self.username = username_result.group(1)
            self.server.echo("{0} has joined.\n".format(self.username))
        elif data == "QUIT":
            self.quit()
        elif data == "":
            #the socket on the other end is porbably closed? hmmm
            self.quit()
        else:
            #normal message, echo to everyone
            self.server.echo(data)
if __name__ == "__main__":
    #star a server on port 59091
    server = Server(59091)
    server.run()
