import asyncio
import socket
import struct
from someip_message import SomeIPMessage, SomeIPData

class SomeIPSender:
    """
    A class responsible for sending SOME/IP packets from a queue.
    """
    def __init__(self, send_queue: asyncio.Queue, send_ip: str, send_port: int, stop_event: asyncio.Event):
        self.send_queue = send_queue
        self.send_ip = send_ip
        self.send_port = send_port
        self.stop_event = stop_event

    async def run(self):
        print("Sender coroutine started.")
        while not self.stop_event.is_set():
            try:
                packet = await asyncio.wait_for(self.send_queue.get(), timeout=1)  # Wait for a packet
                await self.send_packet(packet)
                self.send_queue.task_done()
            except asyncio.TimeoutError:
                continue  # No packet to send, loop again
            except Exception as e:
                print(f"Error in Sender coroutine: {e}")

    async def send_packet(self, packet: bytes):
        """
        Sends a SOME/IP packet over UDP.

        Parameters:
            packet (bytes): Serialized SOME/IP message bytes.
        """
        try:
            loop = asyncio.get_running_loop()
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
                await loop.sock_sendto(sock, packet, (self.send_ip, self.send_port))
                print(f"Sent SOME/IP packet to {self.send_ip}:{self.send_port}")
        except Exception as e:
            print(f"Error sending packet: {e}")

class SomeIPReceiver:
    """
    A class responsible for receiving SOME/IP packets over UDP.
    """
    def __init__(self, recv_ip: str, recv_port: int, received_packets: list, recv_lock: asyncio.Lock, stop_event: asyncio.Event):
        self.recv_ip = recv_ip
        self.recv_port = recv_port
        self.received_packets = received_packets
        self.recv_lock = recv_lock
        self.stop_event = stop_event
        self.sock = None

    async def run(self):
        print(f"SOMEIP receiver started. Listening on {self.recv_ip}:{self.recv_port}")
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            # self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 0)
            self.sock.bind((self.recv_ip, self.recv_port))
            # self.sock.settimeout(1.0)  # Set timeout to allow periodic stop checks
            self.sock.setblocking(False)
            
            loop = asyncio.get_running_loop()
            while True:
                await self.stop_event.wait()
                try:
            
                    data, sender_address = await loop.sock_recvfrom(self.sock, 4096)  # Buffer size can be adjusted
                    # print(f"Received packet from {sender_address}")

                    someip_data = self.from_bytes(data)
                    if someip_data:
                        async with self.recv_lock:
                            self.received_packets.append(someip_data)
                        # print(len(self.received_packets))
                        # For demonstration, print the received data
                        #self.print_someip_data(someip_data)
                # except socket.timeout:
                #     continue  # Timeout occurred, check stop_event
                except Exception as e:
                    print(f"Error receiving packet: {e}")
                await asyncio.sleep(0.01)
        except Exception as e:
            print(f"Failed to set up receiving socket: {e}")
        finally:
            if self.sock:
                self.sock.close()
            print("Receiver coroutine stopped.")

    def from_bytes(self, data):
        """
        Deserialize received packet (header + payload) into a SomeIPData object.
        """
        if len(data) < 16:
            print("Received data is too short to be a valid SOME/IP packet.")
            return None

        header = data[:16]
        message_id, length, client_session_id, version_type_code = struct.unpack('>4I', header)
        payload = data[16:]

        # Parse fields from the message
        service_id = (message_id >> 16) & 0xFFFF
        method_id = message_id & 0xFFFF
        client_id = (client_session_id >> 16) & 0xFFFF
        session_id = client_session_id & 0xFFFF
        protocol_version = (version_type_code >> 24) & 0xFF
        interface_version = (version_type_code >> 16) & 0xFF
        message_type = (version_type_code >> 8) & 0xFF
        return_code = version_type_code & 0xFF

        # Create SomeIPData object
        someip_data = SomeIPData()
        someip_data.service_id = service_id
        someip_data.method_id = method_id
        someip_data.length = length
        someip_data.client_id = client_id
        someip_data.session_id = session_id
        someip_data.protocol_version = protocol_version
        someip_data.interface_version = interface_version
        someip_data.message_type = message_type
        someip_data.return_code = return_code

        # Decode payload
        try:
            payload_list = list(someip_data.payload)
            someip_data.payload = payload.decode('utf-8')
        except UnicodeDecodeError:
            someip_data.payload = payload.hex()

        return someip_data

    def print_someip_data(self, someip_data: SomeIPData):
        """
        Print the details of a SomeIPData object.
        """
        if someip_data is None:
            return

        print("\n=== Received SOME/IP Packet ===")
        print(f"Service ID: 0x{someip_data.service_id:04X}")
        print(f"Method ID: 0x{someip_data.method_id:04X}")
        print(f"Length: {someip_data.length} bytes")
        print(f"Client ID: 0x{someip_data.client_id:04X}")
        print(f"Session ID: 0x{someip_data.session_id:04X}")
        print(f"Protocol Version: {someip_data.protocol_version}")
        print(f"Interface Version: {someip_data.interface_version}")
        print(f"Message Type: 0x{someip_data.message_type:02X}")
        print(f"Return Code: 0x{someip_data.return_code:02X}")
        print(f"Payload: {someip_data.payload}")
        print("================================\n")
