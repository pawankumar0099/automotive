# someip_message.py

import struct

class SomeIPData:
    """
    A class to hold deserialized SOME/IP message data.
    """
    def __init__(self):
        self.service_id = 0
        self.method_id = 0
        self.length = 0
        self.client_id = 0
        self.session_id = 0
        self.protocol_version = 0
        self.interface_version = 0
        self.message_type = 0
        self.return_code = 0
        self.payload = ""

class SomeIPMessage:
    """
    A class for forming and parsing SOME/IP messages.
    """
    HEADER_FORMAT = '>4I'  # Big-endian, 4 unsigned integers
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    @staticmethod
    def create_message(service_id, method_id, client_id, session_id,
                      protocol_version, interface_version, message_type,
                      return_code, payload):
        """
        Serialize the SOME/IP message fields into bytes.

        Parameters:
            service_id (int): Service Identifier.
            method_id (int): Method Identifier.
            client_id (int): Client Identifier.
            session_id (int): Session Identifier.
            protocol_version (int): Protocol Version.
            interface_version (int): Interface Version.
            message_type (int): Message Type.
            return_code (int): Return Code.
            payload (str): Payload data.

        Returns:
            bytes: Serialized SOME/IP message.
        """
        message_id = (service_id << 16) | (method_id & 0xFFFF)
        client_session_id = (client_id << 16) | (session_id & 0xFFFF)
        version_type_code = ((protocol_version & 0xFF) << 24) | \
                            ((interface_version & 0xFF) << 16) | \
                            ((message_type & 0xFF) << 8) | \
                            (return_code & 0xFF)
        payload_bytes = bytearray()
        for item in payload:
            if isinstance(item, int):
                payload_bytes.append(item)  # Append byte if it's an integer
            elif isinstance(item, str):
                payload_bytes.extend(item.encode('utf-8'))  # Convert string to bytes
            else:
                raise ValueError("Unsupported payload item type")
        print(payload_bytes)
        length =8 + len(payload_bytes)
        header_bytes = struct.pack('>4I',message_id, length, client_session_id, version_type_code)
        packet = header_bytes + payload_bytes
        return packet
    
    def to_bytes(self, message_id, length, client_session_id, version_type_code):
        """
        Serialize the header fields into bytes.
        """
        return struct.pack('>4I', message_id, length, client_session_id, version_type_code)

    @staticmethod
    def parse_message(data):
        """
        Deserialize received SOME/IP message bytes into a SomeIPData object.

        Parameters:
            data (bytes): Received SOME/IP message bytes.

        Returns:
            SomeIPData: Deserialized SOME/IP message data.
        """
        if len(data) < SomeIPMessage.HEADER_SIZE:
            print("Received data is too short to be a valid SOME/IP packet.")
            return None

        header = data[:SomeIPMessage.HEADER_SIZE]
        message_id, length, client_session_id, version_type_code = struct.unpack(
            SomeIPMessage.HEADER_FORMAT, header)
        payload = data[SomeIPMessage.HEADER_SIZE:]

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
            someip_data.payload = payload.decode('utf-8')
        except UnicodeDecodeError:
            someip_data.payload = "Payload is not a valid UTF-8 string."

        return someip_data
