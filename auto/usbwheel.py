# usb_wheel.py

import usb.core
import usb.util
import threading
import time
import can
import struct
VENDOR_ID = 0x0079
PRODUCT_ID = 0x189C


class CANHandler:
    """Handles CAN communication, sending messages over the CAN bus."""
    
    def __init__(self, channel, bustype, arb_id):
        self.channel = channel
        self.bustype = bustype
        self.arb_id = arb_id
        self.can_bus = can.interface.Bus(channel=self.channel, bustype=self.bustype)

    def _update_bus(self):
        """Reinitialize the CAN bus with the current settings."""
        self.can_bus = can.interface.Bus(channel=self.channel, bustype=self.bustype)

    def send_message(self, brk, acc, wheel):
        """Sends a CAN message with the given code and value."""
        data_bytes = struct.pack('>BhB', brk, acc,wheel)  # Big-endian, B = unsigned byte, h = signed short
        message = can.Message(
            arbitration_id=self.arb_id,
            data=data_bytes.ljust(4, b'\x00'),  # Pad to 4 bytes if necessary
            is_extended_id=False
        )

        try:
            self.can_bus.send(message)
            # print(f"Sent: code={code}, value={value}")
        except can.CanError as e:
            print(f"Failed to send CAN message: {e}")


class USBDeviceHandler:
    def __init__(self, vendor_id, product_id):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.device = None
        self.previous_data = [0] * 64  # Adjust buffer size based on your requirements

    def initialize_device(self):
        """
        Initializes the USB device by finding it, detaching any active kernel drivers,
        setting the active configuration, and claiming the interface.
        """
        # Find the USB device
        self.device = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id)

        if self.device is None:
            raise ValueError("Cannot open USB device")

        # Detach kernel driver if necessary
        if self.device.is_kernel_driver_active(0):
            try:
                self.device.detach_kernel_driver(0)
                print("Kernel driver detached.")
            except usb.core.USBError as e:
                raise RuntimeError(f"Failed to detach kernel driver: {e}")

        # Set the active configuration
        self.device.set_configuration()
        print("USB configuration set.")

        # Claim the interface
        usb.util.claim_interface(self.device, 0)
        print("USB interface claimed.")

    def listen_for_changes(self, endpoint_address=0x81, packet_size=64, timeout=1000):
        """
        Reads data from the USB device and checks for changes compared to the previous read.

        Parameters:
            endpoint_address (int): The endpoint address to read from.
            packet_size (int): The size of the data packet to read.
            timeout (int): Timeout for the read operation in milliseconds.

        Returns:
            list or None: The new data if changed, else None.
        """
        try:
            # Read from the device
            data = self.device.read(endpoint_address, packet_size, timeout=timeout)
            data = list(data)
            return data

        except usb.core.USBError as e:
            if e.errno == 110:  # Timeout
                return None
            else:
                raise RuntimeError(f"Error reading data: {e}")

    def cleanup(self):
        """
        Releases the USB interface and re-attaches the kernel driver.
        """
        # Release the interface
        usb.util.release_interface(self.device, 0)
        print("USB interface released.")

        # Re-attach the kernel driver
        try:
            self.device.attach_kernel_driver(0)
            print("Kernel driver re-attached.")
        except usb.core.USBError as e:
            print(f"Failed to re-attach kernel driver: {e}")

def usb_listener(usb_handler: USBDeviceHandler, can_handler: CANHandler):

    while True:
        try:
            data = usb_handler.listen_for_changes()

            if data:
                print(data[5])
                can_handler.send_message(data[4],data[5],data[7])


        except Exception as e:
            print(f"Error in USB listener: {e}")
        time.sleep(0.1)  # Adjust as needed

if __name__ == "__main__":
    # Initialize the CAN bus handler and message processor
    usb_handler = USBDeviceHandler(VENDOR_ID, PRODUCT_ID)
    try:
        usb_handler.initialize_device()
        print("USB device initialized successfully.")
    except ValueError as e:
        print(f"USB Initialization Error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"USB Initialization Runtime Error: {e}")
        sys.exit(1)
    can_handler = CANHandler(channel='can0', bustype='socketcan', arb_id=0x123)

    usb_thread = threading.Thread(target=usb_listener, args=(usb_handler,can_handler,))
    usb_thread.start()