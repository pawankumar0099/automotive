from can_rcv import CANBusHandler

class CANMessageProcessor:
    """Processes received CAN messages."""

    # Initialize variables
    speed = 0
    base_max_speed = 120  # Example base maximum speed
    base_acceleration_factor = 0.1  # Base factor to convert acceleration input to speed increment
    base_brake_factor = 0.05  # Base factor to convert brake input to speed decrement
    friction_factor = 0.01  # Factor to simulate friction
    prev_acceleration_input = 0
    prev_brake_input = 0

    break_counter = 0
    break_count_state = False



    def __init__(self, can_handler):
        """Initialize with a CANBusHandler instance."""
        self.can_handler = can_handler

    # Function to calculate dynamic max speed
    def calculate_max_speed(self,acceleration_input):
        return self.base_max_speed * (acceleration_input / 255)

    def acc_sim(self, acceleration_input):
        # Calculate rate of change
        acceleration_change = acceleration_input - self.prev_acceleration_input
        max_speed = self.calculate_max_speed(acceleration_input)
        # print(f"acc: {acceleration_change}")
     
        acceleration_factor = self.base_acceleration_factor * (1 + abs(acceleration_change) / 255)

        speed_increment = acceleration_input * acceleration_factor

        if acceleration_input>= self.prev_acceleration_input and self.speed < max_speed:
            self.speed += speed_increment
        
        self.speed -= self.speed * self.friction_factor
        
        
        if acceleration_input > self.prev_acceleration_input and acceleration_input !=0 and self.speed > max_speed:
            self.speed = max_speed
        if self.speed < 0:
            self.speed = 0
   
        self.prev_acceleration_input = acceleration_input
        # prev_brake_input = brake_input
        if self.speed > self.base_max_speed:
            self.speed = self.base_max_speed
        
        self.speed = round(self.speed,2)


    def brk_sim(self, brake_input):
   
        # Calculate rate of change
        brake_change = brake_input - self.prev_brake_input
    
        # Adjust brake factor based on rate of change
        brake_factor = self.base_brake_factor * (1 + abs(brake_change) / 255)
    
        # Calculate speed decrement
        speed_decrement = brake_input * brake_factor
    
        # Update speed
        self.speed -= speed_decrement
    
        # Update previous brake input
        self.prev_brake_input = brake_input

        if self.speed < 0:
            self.speed = 0

        self.speed = round(self.speed,2)


    def process_messages(self):
        """Main loop to receive and process CAN messages."""
        try:
            while True:
                # Wait until a message is received
                message = self.can_handler.receive_message()
                if message:
                    brk, acc, wheel = self.can_handler.unpack_message(message)
                    if 0 < wheel <= 127:
                            wheel = 'R'
                    elif 127 < wheel <= 255:
                            wheel = 'L'

                    if brk > 5 and self.break_count_state:
                        self.break_counter += 1
                        self.break_count_state = False
                    elif brk < 5:
                        self.break_count_state = True
                    print(f"Received message: break={brk}, acc={acc}, wheel={wheel},breakCount= {self.break_counter} ")
                    
                    self.acc_sim(acc)
                    self.brk_sim(brk)

                    print(f"Speed: {self.speed}")
            
        except KeyboardInterrupt:
            print("Stopped receiving CAN messages.")


if __name__ == "__main__":
    # Initialize the CAN bus handler and message processor
    can_handler = CANBusHandler(channel='can0', bustype='socketcan')
    message_processor = CANMessageProcessor(can_handler)

    # Start processing CAN messages
    message_processor.process_messages()