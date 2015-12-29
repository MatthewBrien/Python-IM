#!/usr/bin/env python3.5
#client side of an instant messaging application, copied from a book that copied it from Liam Fraser or something

import threading
import gtk
import gobject
import socket
import re
import time
import datetime

#tell objects to expect calls from multiple threads,
#whatever that means

gobject.threads_init()

class MainWindow(gtk.window):
    def __init__(self):
        super(MainWindow, self).__init__()
        #create main controls
        self.set_title("IM-Client")
        vbox = gtk.VBox()
        hbox = gtk.HBox()
        self.username_label = gtk.Label()
        self.text_entry = gtk.Entry()
        self.text_buffer = gtk.TextBuffer()
        text_view = gtk.TextView(self.text_buffer)
        #connect events
        self.connect("destroy",self.graceful_quit)
        send_button.connect("clicked", self.send_message)
        #activate when user presses enter
        self.text_entry.connect("activate", self.send_message)
        #do layout why don't you
        vbox.pack_start(text_view)
        hbox.pack_start(self.username_label, expand = False)
        hbox.pack_start(self.text_entry)
        hbox.pack_end(send_button, expand = False)
        vbox.pack_end(hbox, expand = False)
        #reveal ourselves (or the window probably)
        self.add(vbox)
        self.show_all()
        #go through the configuration process
        self.configure()
    def ask_for_info(self, question):
        dialog = gtk.MessageDialog(parent = self,
            type = gtk.MESSAGE_QUESTION,
            flags = gtk.DIALOG_MODAL |
            gtk.DIALOG_DESTROY_WITH_PARENT,
            buttons = gtk.BUTTONS_OK_CANCEL,
            message_format = question)
        entry = gtk.Entry()
        dialog.vbox.pack_end(entry)
        response = dialog.run()
        response_text = entry.get_text()
        dialog.destroy()
        if response == gtk.RESPONSE_OK:
            return response_text
        else:
            return None

    def configure(self):
    #performs the steps to connect to the serve
    #show a dialog box prompting the user for a server address followed by a port number
        server = self.ask_for_info("server_address:port")
    #regex to crudely match an IP address and port number
        regex = re.search('^(\d+\.\d+\.\d+\.\d+):(\d+)$',server)
        address  = regex.group(1).strip()
        port = regex.group(2).strip()

    #ask for a username
        self.username = self.ask_for_info("username")
    #attempt to connect to the sever and then start listening
        self.network = Networking(self, self.username, address, int(port))
        self.network.listen()


    def add_text(self, new_text):
        text_with_timestamp = "{0}{1}".format(datetime.datetime.now(), new_text)

        #get the position of the end of the txt buffer so we know where to insert new text
        end_itr = self.text_buffer.get_end_iter()
        #add new text to end of buffer
        self.text_buffer.insert(end_itr, text_with_timestamp)

    def send_message(self, widget):
        #clear the text entry and send message to the server,
        #message doesn't need to be displayed here as it is diplayed when echoed back from server
        new_text = self.text_entry.get_text()
        self.text_entry.set_text("")
        message = "{0} says: {1}\n".format(self.username, new_text)
        self.network.send(message)

    def graceful_quit(self, widget):
        #when the application is closed, tell GTK to quit, then tell the sever we are guiting and tidy up the network
        gtk.main_quit()
        self.network.send("QUIT")
        self.network.tidy_up()

class Networking():
    def __init__(self, window, username, server, port):
        #setup the networking class
        self.window = window
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((server, port))
        self.listening = True
        #tell the server a new user has joined
        self.send("USERNAME {0}".format(username))

    def listener(self):
        #a function run as a thread that listens for new messages
        while self.listening:
            data = ""
            try:
                data = self.socket.recv(1024)
            except seocket.error:
                "Unable to recieve data"
            self.handle_msg(data)
            #slow down the while loop
            time.sleep(0.1)

    def listen(self):
        #start the listening thread
        self.listen_thread = threading.Thread(target=self.listener)
        #prevent child thread from keeping the application open
        self.listen_thread.daemon = True
        self.listen_thread.start()

    def send(self, message):
        #send a message to the server
        print( "Sending: {0}".format(message) )
        try:
            self.socket.sendall(message)
        except socket.error:
            print ("Unable to send message")

    def tidy_up(self):
        #well  be tidying  up if either we are quiting or the server is quitting
        self.listening = False
        self.socket.close()
        #we won't have the pleasure of seeing this if we're the one quitting
        gobject.idle_add(self.window.add_text, "Server has quit.\n")

    def handle_msg(self, data):
        if data == "QUIT":
        #server is quitting
            self.tidy_up()
        else:
            #tell the GTK thread to add some text when it is ready
            goject.idle_add(self.window.add_text, data)

if __name__ == "__main__":
    MainWindow()
    gtk.main()
