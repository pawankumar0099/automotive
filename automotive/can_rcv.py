import can
import struct


class CANBusHandler:
    """Handles communication over the CAN bus."""

    def __init__(self, channel='can0', bustype='socketcan'):
        """Initialize the CAN bus interface."""
        self.bus = can.interface.Bus(channel=channel, bustype=bustype)

    def receive_message(self):
        """Receive a CAN message from the bus."""
        return self.bus.recv()

    def unpack_message(self, message):
        """Unpack the received message data."""
        # Unpack the data (big-endian format)
        brk, value, wheel = struct.unpack('>BhB', message.data[:4])  # Extract only 3 bytes
        return brk, value, wheel








