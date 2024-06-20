from PySide2.QtWidgets import QApplication

from face     import FaceWidget
from wsserver import myWebSocketServer

import sys
import asyncio
import argparse  # Import the argparse module

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

async def main():
    args = parse_arguments()
    address = args.address.split(":")
    ip, port = address[0], int(address[1])

    app = QApplication(sys.argv)
    face_widget = FaceWidget(args.v1, args.v2, args.v3, args.v4, args.v5, args.stepsIn10s, args.delaytime)

    if test_mode:
        face_widget.show()
    else:
        face_widget.showFullScreen()

    server = myWebSocketServer(ip, port)

    server.listener.on_message.connect(face_widget.on_message_received)

    # Example sending a message
    server.send_message("Hello from QT Robot!")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    asyncio.run(main())