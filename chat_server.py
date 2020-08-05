import grpc
import chat_pb2 as chat
import chat_pb2_grpc as rpc
import threading
from server import myserver


class ChatClass:
    def __init__(self, address, port):
        channel = grpc.insecure_channel(address + ':' + str(port))
        self.conn = rpc.ChatServerStub(channel)
        self.username = input("Enter ypur name : ")

        threading.Thread(target=self.recive, daemon=True).start()

        self.send()

    def send(self):
        message = ''
        while message != 'exit':
            message = input()
            n = chat.Note()
            n.name = self.username  # set the username
            n.message = message
            self.conn.SendNote(n)

    def recive(self):
        for note in self.conn.ChatStream(chat.Empty()):  # this line will wait for new messages from the server!
            if note.name and note.name != self.username:
                print("{} : {}\n".format(note.name, note.message))


address, port = myserver.server_initialize(address='localhost', port=11912)

ChatClass(address, port)

while True:
    pass
