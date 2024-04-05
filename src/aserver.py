import asyncio
import json
import websockets
import argparse
import random

def parse_arguments():
    parser = argparse.ArgumentParser(description='WebSocket server for robot control.')
    parser.add_argument('--address', type=str, default='0.0.0.0:8000', help='Server address in the format ip:port')
    return parser.parse_args()

connected_clients = set()


async def send_telemetry(websocket):
    switch = True

    while True:
        switch = not switch

        velocity = random.uniform(-6, 6)

        payload = {
            "position": 1.234,
            "velocity": velocity,
            "rotation": -0.004,
            "acceleration": 1.234,
            "cg_angle": 0.100,
            "cg_angular_velocity": -0.500,
            "battery": 11.1,
            "motor_amps": 0.4,
            "rawdata": {
                "accel": {
                    "x": 123.45,
                    "y": 456.78,
                    "z": 789.01
                },
                "gyro": {
                    "x": 123.45,
                    "y": 456.78,
                    "z": 789.01
                },
                "enc_left": {
                    "position": 12.3,
                    "velocity": 0.125
                },
                "enc_right": {
                    "position": 12.3,
                    "velocity": 0.121
                },
                "adc_battery": {
                    "voltage": 3.8
                },
                "adc_motor_left": {
                    "voltage": 1.2
                },
                "adc_motor_right": {
                    "voltage": 1.2
                }
            }
        }

        await websocket.send(json.dumps(payload))
        await asyncio.sleep(1)  # Send message every 1 second

async def handler(websocket, path):
    global connected_clients
    client_ip, client_port = websocket.remote_address
    print(f"New client connected: {client_ip}:{client_port}")
    connected_clients.add(websocket)

    try:

        payload = {"message": "Hello, world!"}

        await websocket.send(json.dumps(payload))

        hello_task = asyncio.create_task(send_telemetry(websocket))

        while True:
            message = await websocket.recv()
            print(message)

    finally:
        hello_task.cancel()  # Cancel the hello world task
        print(f"Client disconnected: {client_ip}:{client_port}")
        connected_clients.remove(websocket)

async def start_server(ip, port):
    async with websockets.serve(handler, ip, port):
        print(f"Server started on {ip}:{port}")
        await asyncio.Future()  # Run forever

async def main():
    args = parse_arguments()
    address = args.address.split(":")
    ip, port = address[0], int(address[1])
    await asyncio.gather(
        start_server(ip, port),
    )

if __name__ == "__main__":
    asyncio.run(main())