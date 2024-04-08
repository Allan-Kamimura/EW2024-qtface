from PySide2.QtWidgets import QApplication

from face import FaceWidget

import sys
import asyncio
import argparse  # Import the argparse module
import threading
import asyncio, websockets, json

test_mode = False

connected_clients = set()

# Function to parse command-line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="WebSocket server for robot control.")
    parser.add_argument("--address"   , type = str  , default = "0.0.0.0:8000", help = "Server address in the format ip:port")
    parser.add_argument("--v1"        , type = float, default = -7            , help = "--|v1|v2|v3|v4|v5|--")
    parser.add_argument("--v2"        , type = float, default = -5            , help = "--|v1|v2|v3|v4|v5|--")
    parser.add_argument("--v3"        , type = float, default = -0            , help = "--|v1|v2|v3|v4|v5|--")
    parser.add_argument("--v4"        , type = float, default =  5            , help = "--|v1|v2|v3|v4|v5|--")
    parser.add_argument("--v5"        , type = float, default =  7            , help = "--|v1|v2|v3|v4|v5|--")
    parser.add_argument("--stepsIn10s", type = int  , default =  10           , help = "--|v1|v2|v3|v4|v5|--")
    parser.add_argument("--delaytime" , type = float, default =  8000         , help = "--|v1|v2|v3|v4|v5|--")
    return parser.parse_args()

class Signal:
    def __init__(self):
        self.__subscribers = []

    def connect(self, slot):
        self.__subscribers.append(slot)

    def emit(self, *args, **kwargs):
        for subscriber in self.__subscribers:
            subscriber(*args, **kwargs)

my_signal = Signal()

def my_slot_function(message, additional_info=None):
    print(f"Signal received with message: {message}")


async def send_control_instructions():
    print("Sending control instructions to any connected robot...")
    control_message = {
        "command": "back",
        "args": {}
    }
    for client in connected_clients:
        asyncio.create_task(client.send(json.dumps(control_message)))

async def handler(websocket, path):
    global connected_clients
    client_ip, client_port = websocket.remote_address
    print(f"New client connected: {client_ip}:{client_port}")

    # Connect the slot to the signal   
    connected_clients.add(websocket)
    try:
        while True:
            message = await websocket.recv()
            my_signal.emit(message)
            #print(f"Received telemetry message from {client_ip}: {message}")
    finally:
        print(f"Client disconnected: {client_ip}:{client_port}")
        connected_clients.remove(websocket)

async def start_server(ip, port):
    async with websockets.serve(handler, ip, port):
        print(f"Server started on {ip}:{port}")
        await asyncio.Future()  # Run forever

async def send_command():
    while True:
        await asyncio.sleep(7)
        await send_control_instructions() 

async def main():
    args = parse_arguments()
    address = args.address.split(":")
    ip, port = address[0], int(address[1])

    await asyncio.gather(
        start_server(ip, port),
        send_command(),
    )

    app = QApplication(sys.argv)
    face_widget = FaceWidget(args.v1, args.v2, args.v3, args.v4, args.v5, args.stepsIn10s, args.delaytime)

    if test_mode:
        face_widget.show()
    else:
        face_widget.showFullScreen()

    client = face_widget
    client.startConnection(f"ws://{ip}:{port}")
    my_signal.connect(my_slot_function)
    # Example sending a message
    client.send_message("Hello from QT Robot!")
        
    sys.exit(app.exec_())

if __name__ == "__main__":
    asyncio.run(main())