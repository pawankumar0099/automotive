import can
import struct
import asyncio
import socket


class CanReceiver:
    """Handles communication over the CAN bus."""

    def __init__(self, received_packets: dict, recv_lock: asyncio.Lock, channel='can0', bustype='socketcan'):
        """Initialize the CAN bus interface."""
        self.received_packets = received_packets
        self.recv_lock = recv_lock
        self.bus = can.interface.Bus(channel=channel, bustype=bustype)

        # Set socket options directly for socketcan
        if bustype == 'socketcan':
            # Get the file descriptor from the CAN bus socket
            sock = self.bus.socket  # Direct access to the CAN socket

            # Disable receive buffer by setting SO_RCVBUF to 0
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 0)

    async def receive_message(self):
            """Receive a CAN message asynchronously from the bus."""
            # Using asyncio.to_thread to avoid blocking the main thread
            
            while True:
                try:
                    
                    message = await asyncio.to_thread(self.bus.recv)
                    if message:
                        car_break_value, car_acceleration_value, car_wheel_value = self.unpack_message(message)
                        async with self.recv_lock:
                            self.received_packets['car_break'] = car_break_value
                            self.received_packets['car_acceleration'] = car_acceleration_value
                            self.received_packets['car_wheel'] = car_wheel_value

                    await asyncio.sleep(0.1)

                    
                except Exception as e:
                    print(f"Error: {e}")



    def unpack_message(self, message):
        """Unpack the received message data."""
        # Unpack the data (big-endian format)
        brk, value, wheel = struct.unpack('>BhB', message.data[:4])  # Extract only 3 bytes
        return brk, value, wheel