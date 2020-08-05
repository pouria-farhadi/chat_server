import datetime
import json
from concurrent import futures

import grpc

import chat_pb2 as chat
import chat_pb2_grpc as rpc
import redis

servers = []


class ChatServer(rpc.ChatServerServicer):

    def __init__(self):
        self.listening = redis.Redis(host='localhost', port=6379)
        self.listening = self.listening.pubsub()
        self.listening.subscribe('chat')
        self.sending = redis.Redis(host='localhost', port=6379, )

    # The stream which will be used to send new messages to clients
    def ChatStream(self, request_iterator, context):
        """
        This is a response-stream type call. This means the server can keep sending messages
        Every client opens this connection and waits for server to send new messages

        :param request_iterator:
        :param context:
        :return:
        """
        last_timestamp = ''
        for item in self.listening.listen():
            if item['data'] != 1:
                data = json.loads(item['data'])
                if data["timestamp"] <= last_timestamp:
                    continue
                n = chat.Note()
                n.name = data['user']
                n.message = data['message']
                yield n
                last_timestamp = data["timestamp"]
        # while True:
        #     item = self.listening.get_message()
        #     if item:
        #         if type(item['data']) != int:
        #             data = json.loads(item['data'])
        #             n = chat.Note()
        #             n.name = data['user']
        #             n.message = data['message']
        #             yield n
        #         else:
        #             yield chat.Empty()

    def SendNote(self, request: chat.Note, context):
        """
        This method is called when a clients sends a Note to the server.

        :param request:
        :param context:
        :return:
        """
        # Add it to the chat history
        self.sending.publish('chat', json.dumps(
            {'message': request.message, 'user': request.name, 'timestamp': str(datetime.datetime.now())}))
        return chat.Empty()


class MyServers:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379)
        ports = self.redis.get('ports')
        if not ports:
            self.ports = []
        else:
            self.ports = json.loads(ports)

    def server_initialize(self, address, port):
        try:
            server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

            # use the generated function `add_CalculatorServicer_to_server`
            # to add the defined class to the server
            rpc.add_ChatServerServicer_to_server(
                ChatServer(), server)
            while port in self.ports:
                port += 1
            server.add_insecure_port(address + ':' + str(port))
            server.start()
            servers.append(server)
            self.ports.append(port)
            self.redis.set('ports', json.dumps(self.ports))
            return address, port
        except:
            pass


myserver = MyServers()
