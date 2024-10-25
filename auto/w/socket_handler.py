# socket_handler.py

import socket
import threading
import queue
from someip_message import SomeIPMessage, SomeIPData

class SomeIPSender(threading.Thread):
    """
    A thread class responsible for sending SOME/IP packets from a queue.
    """
    def __init__(self, send_queue: queue.Queue, send_ip: str, send_port: int, stop_event: threading.Event):
        super().__init__(daemon=True)
        self.send_queue = send_queue
        self.send_ip = send_ip
        self.send_port = send_port
        self.stop_event = stop_event

    def run(self):
        print("Sender thread started.")
        while not self.stop_event.is_set():
            try:
                packet = self.send_queue.get(timeout=1)  # Wait for a packet
                self.send_packet(packet)
                self.send_queue.task_done()
            except queue.Empty:
                continue  # No packet to send, loop again
            except Exception as e:
                print(f"Error in Sender thread: {e}")

    def send_packet(self, packet: bytes):
        """
        Sends a SOME/IP packet over UDP.

        Parameters:
            packet (bytes): Serialized SOME/IP message bytes.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
                sock.sendto(packet, (self.send_ip, self.send_port))
                print(f"Sent SOME/IP packet to {self.send_ip}:{self.send_port}")
        except Exception as e:
            print(f"Error sending packet: {e}")

class SomeIPReceiver(threading.Thread):
    """
    A thread class responsible for receiving SOME/IP packets over UDP.
    """
    def __init__(self, recv_ip: str, recv_port: int, received_packets: list, recv_lock: threading.Lock, stop_event: threading.Event):
        super().__init__(daemon=True)
        self.recv_ip = recv_ip
        self.recv_port = recv_port
        self.received_packets = received_packets
        self.recv_lock = recv_lock
        self.stop_event = stop_event
        self.sock = None

    def run(self):
        print(f"Receiver thread started. Listening on {self.recv_ip}:{self.recv_port}")
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.recv_ip, self.recv_port))
            self.sock.settimeout(1.0)  # Set timeout to allow periodic stop checks

            while not self.stop_event.is_set():
                try:
                    data, sender_address = self.sock.recvfrom(4096)  # Buffer size can be adjusted
                    print(f"Received packet from {sender_address}")

                    someip_data = SomeIPMessage.parse_message(data)
                    if someip_data:
                        with self.recv_lock:
                            self.received_packets.append(someip_data)
                    
                        # For demonstration, print the received data
                        self.print_someip_data(someip_data)
                except socket.timeout:
                    continue  # Timeout occurred, check stop_event
                except Exception as e:
                    print(f"Error receiving packet: {e}")
        except Exception as e:
            print(f"Failed to set up receiving socket: {e}")
        finally:
            if self.sock:
                self.sock.close()
            print("Receiver thread stopped.")

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
