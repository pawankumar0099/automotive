# main.py

import threading
import time
import queue  
from someip_message import SomeIPMessage
from socket_handler import SomeIPSender, SomeIPReceiver
#from usb_wheel import USBDeviceHandler
import sys
import json

# Constants for USB Device
#VENDOR_ID = 0x0079
#PRODUCT_ID = 0x189C

'''def usb_listener(usb_handler: USBDeviceHandler, send_queue: queue.Queue, stop_event: threading.Event):
    """
    Listens for changes from the USB device and enqueues SOME/IP packets for sending.

    Parameters:
        usb_handler (USBDeviceHandler): The USB device handler instance.
        send_queue (queue.Queue): The queue to enqueue SOME/IP packets.
        stop_event (threading.Event): Event to signal the thread to stop.
    """
    while not stop_event.is_set():
        try:
            data = usb_handler.listen_for_changes()
            if data:
                # Process the data as needed
                # For example, convert the byte data to a hexadecimal string
                payload =data #''.join([f"{byte:02X}" for byte in data])
                print(f"USB data changed: {payload} {len(payload)} ")
                
                # Create the SOME/IP message
                packet = SomeIPMessage.create_message(
                    service_id=0x1234,
                    method_id=0x5678,
                    client_id=0x4321,
                    session_id=0x8765,
                    protocol_version=1,
                    interface_version=1,
                    message_type=0x01,  # request
                    return_code=0x00,    # no error
                    payload=payload
                )
                
                # Enqueue the packet for sending
                send_queue.put(packet)
        except Exception as e:
            print(f"Error in USB listener: {e}")
        time.sleep(0.1)  # Adjust as needed
'''
def get_data(send_queue: queue.Queue):
    while True:
        try:
            #data = bytearray([1,2,3,4])
            data = {
                "object_type": "pedestrian",
                "distance": 30
            }
            json_data = json.dumps(data)
            if data:
                # Process the data as needed
                # For example, convert the byte data to a hexadecimal string
                payload =json_data#''.join([f"{byte:02X}" for byte in data])
                print(f"USB data changed: {payload} {len(payload)} ")
                
                # Create the SOME/IP message
                packet = SomeIPMessage.create_message(
                    service_id=0x1234,
                    method_id=0x5678,
                    client_id=0x4321,
                    session_id=0x8765,
                    protocol_version=1,
                    interface_version=1,
                    message_type=0x01,  # request
                    return_code=0x00,    # no error
                    payload=payload
                )
                
                # Enqueue the packet for sending
                send_queue.put(packet)
        except Exception as e:
            print(f"Error in USB listener: {e}")
        time.sleep(0.1)  # Adjust as needed

def main():
    import queue  # Importing here to avoid circular imports

    # Initialize the USB handler
    #usb_handler = USBDeviceHandler(VENDOR_ID, PRODUCT_ID)
    '''try:
        usb_handler.initialize_device()
        print("USB device initialized successfully.")
    except ValueError as e:
        print(f"USB Initialization Error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"USB Initialization Runtime Error: {e}")
        sys.exit(1)
    '''
    # Create a send queue
    send_queue = queue.Queue()

    # Create a lock and list to store received packets
    received_packets = []
    recv_lock = threading.Lock()

    # Create a stop event
    stop_event = threading.Event()

    # Configure sending IP and port
    send_ip = "192.168.1.16"  # Replace with your target IP
    send_port = 30490            # Replace with your target port

    # Configure receiving IP and port
    recv_ip = "0.0.0.0"          # Listen on all interfaces
    recv_port = 30490            # Replace with your listening port

    # Initialize the sender and receiver
    sender = SomeIPSender(send_queue, send_ip, send_port, stop_event)
    receiver = SomeIPReceiver(recv_ip, recv_port, received_packets, recv_lock, stop_event)

    # Start the sender and receiver threads
    sender.start()
    receiver.start()

    data_thread=threading.Thread(target=get_data, args= (send_queue,))
    data_thread.start()
    # Start the USB listener thread
    #usb_thread = threading.Thread(target=usb_listener, args=(usb_handler, send_queue, stop_event), daemon=True)
    #usb_thread.start()
    #print("USB listener thread started.")

    try:
        # Main thread can perform other tasks or simply wait
        #while usb_thread.is_alive():
        #    usb_thread.join(timeout=1)
        time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Exiting...")
    

    '''try:
        # Main thread can perform other tasks or simply wait
        while usb_thread.is_alive():
            usb_thread.join(timeout=1)
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Exiting...")
    finally:
        # Signal all threads to stop
        stop_event.set()

        # Wait for sender and receiver threads to finish
        sender.join()
        receiver.join()

        # Cleanup USB device
        usb_handler.cleanup()
    '''
    # Optionally, retrieve and process received packets
    with recv_lock:
        received = list(received_packets)

    print(f"\nTotal received packets: {len(received)}")
    for idx, pkt in enumerate(received, 1):
        print(f"\n--- Packet {idx} ---")
        print(f"Service ID: 0x{pkt.service_id:04X}")
        print(f"Method ID: 0x{pkt.method_id:04X}")
        print(f"Length: {pkt.length} bytes")
        print(f"Client ID: 0x{pkt.client_id:04X}")
        print(f"Session ID: 0x{pkt.session_id:04X}")
        print(f"Protocol Version: {pkt.protocol_version}")
        print(f"Interface Version: {pkt.interface_version}")
        print(f"Message Type: 0x{pkt.message_type:02X}")
        print(f"Return Code: 0x{pkt.return_code:02X}")
        print(f"Payload: {pkt.payload}")

if __name__ == "__main__":
    main()
