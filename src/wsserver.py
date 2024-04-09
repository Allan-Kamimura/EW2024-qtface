from PySide2.QtWebSockets import QWebSocketServer
from PySide2.QtNetwork import QHostAddress
from PySide2.QtCore import QTimer, Slot, Signal, QObject

import json

class messageListener(QObject):
    # Define a signal for message received
    on_message = Signal(str)

    def __init__(self):
        super().__init__()
        
    def receive_message(self, message):
        # When a message is received, emit the signal
        self.on_message.emit(message)

class myWebSocketServer:
    def __init__(self, ip, port):
        self.websocket_server = QWebSocketServer("WebSocketServer", QWebSocketServer.NonSecureMode)
        self.websocket_server.listen(QHostAddress(ip), port)
        self.websocket_server.newConnection.connect(self.on_new_connection)
        self.connected_clients = []

        self.control_timer = QTimer()
        self.control_timer.timeout.connect(self.send_command)
        self.control_timer.start(7000)

        if self.websocket_server.isListening():
            print(self.websocket_server.serverUrl())
        else:
            print("Server not working")

        self.listener = messageListener()

    def on_new_connection(self):
        print("New connection")
        socket = self.websocket_server.nextPendingConnection()

        # Connect signals to handle messages and disconnections
        socket.textMessageReceived.connect(self.on_message_received)
        socket.disconnected.connect(lambda: self.handle_disconnect(socket))

        # Add the socket to the list of connected clients
        self.connected_clients.append(socket)

    def handle_disconnect(self, socket):
        print("Client disconnected", socket)

        # Remove the socket from the list of connected clients
        if socket in self.connected_clients:
            self.connected_clients.remove(socket)
    
    @Slot(str)
    def on_message_received(self, message):
        print("Received message:", message)

        self.listener.receive_message(message)

        # Process the received message here

    @Slot(str)
    def send_message(self, message):
        for socket in self.connected_clients:
            socket.sendTextMessage(message)
            print("Message sent:", message)

    def send_command(self):
        print("Sending control instructions to any connected robot...")
        control_message = {
            "command": "back",
            "args": {}
        }

        for socket in self.connected_clients:
            socket.sendTextMessage(json.dumps(control_message))

