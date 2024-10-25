# usb_wheel.py

import usb.core
import usb.util

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

            # Check if the data has changed from the previous read
            if data != self.previous_data:
                self.previous_data = data  # Update previous data
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
