import asyncio
import signal
from MQTTCarClient import MQTTCarClient
from socket_handler import SomeIPReceiver
from CanReceiver import CanReceiver
import json
import pandas as pd



class CarSimulation:
    
    #loop_delay in seconds
    LOOP_DELAY = 0.1
    
    #time constant
    TIME_RATE = 30               #time simulation rate 1s simulate to 30mins
    MIN_IN_HOUR = 60
    TOTAL_HOUR_OF_SIMULATION = LOOP_DELAY * TIME_RATE/MIN_IN_HOUR
    
    #charging global variables
    MAX_BAT_PC = 100.0
    MIN_BAT_PC = 0.0
    LOW_BAT_PC = 5.0
    BAT_CHARGING_RATE = 1             #battery charging rate = 1 pc in 1min
    ENVIRONMENT_BAT_DCHG =  0.001     #discharge battery due to 1 degree change in temp
    
    distance_travelled = 0.0

    speed_val=0
    SPEED_BAT_DCHG_RATE = 0.1         #battery discharging pc due to 1km/h speed in 1h
    
    DOOR_LOCK_THRESHOLD=10
    door_lock_state = False
    
    battery_pc = 80.0
    estimated_range_val = 320.0
    EST_RANGE_FULL_BATTERY = 400.0

    break_counter = 0
    break_count_state = False

    BASE_MAX_SPEED = 120  # Example base maximum speed
    BASE_MIN_SPEED = 0
    BASE_car_ACCecar_acceeleration_valueELERATION_FACTOR = 0.1  # Base factor to convert car_acceeleration_valueeleration input to speed increment
    BASE_BREAK_FACTOR = 0.05  # Base factor to convert brake input to speed decrement
    FRICTION_FACTOR = 0.01  # Factor to simulate friction
    prev_car_acceeleration_valueeleration_input = 0
    prev_brake_input = 0

    battery_health = 0.0
    tyre_health = 0.0
    break_pads = 0.0

    
    #publish topic data dictionary
    pub_data = {
        "speed": 0.0,
        "battery": 0.0,
        "door_lock": False,
        "estimated_range": 0.0,
        "obstacle_object_status": "off",
        "crash_detected": False,
        "object_type": "pedestrian",
        "meter_reading": 0.0,
        "battery_health":0.0,
        "tyre_health":0.0,
        "break_pads":0.0
        }
    
    received_packets = []
    can_receive = {}
    recv_lock = asyncio.Lock()
    stop_event = asyncio.Event()


        
    def __init__(self,mqtt_host,mqtt_port,someIP_host,someIP_port):
        
        self.mCarClient = MQTTCarClient(mqtt_host,mqtt_port)
        self.receiver = SomeIPReceiver(recv_ip=someIP_host,recv_port=someIP_port,received_packets=self.received_packets,recv_lock=self.recv_lock,stop_event=self.stop_event)
        self.can_handler = CanReceiver(channel='can0', bustype='socketcan', received_packets=self.can_receive,recv_lock=self.recv_lock)
        
        self.read_parameters()     
        signal.signal(signal.SIGINT, self.shutdown)

    def read_parameters(self):
        df = pd.read_csv('car_parameters.csv')
        self.distance_travelled = float(df['Distance'].iloc[0])
        self.battery_pc = float(df['Battery'].iloc[0])
        self.break_counter = df['BreakCounter'].iloc[0] 

        self.battery_health = float(df['BatteryHealth'].iloc[0])
        self.tyre_health = float(df['TyreHealth'].iloc[0]) 
        self.break_pads = float(df['BreakPads'].iloc[0])

    def write_parameters(self):
        df = pd.DataFrame({'Distance': [0.0], 'Battery': [0.0], 'BreakCounter': [0], 'BatteryHealth':[0.0],'TyreHealth': [0.0], "BreakPads": [0.0] })
        df['Distance'].values[0] = self.distance_travelled
        df['Battery'].values[0] = self.battery_pc
        df['BreakCounter'].values[0] = self.break_counter
        df['BatteryHealth'].values[0] = self.battery_health
        df['TyreHealth'].values[0] = self.tyre_health
        df['BreakPads'].values[0] = self.break_pads

        df.to_csv("car_parameters.csv", index=False)

    #function to simulate charging    
    def battery_charge_simulation(self):
        if(self.mCarClient.charging_state):
            self.battery_pc = self.battery_pc + self.BAT_CHARGING_RATE*self.TOTAL_HOUR_OF_SIMULATION*self.MIN_IN_HOUR
            if self.battery_pc >=self.MAX_BAT_PC:
                self.battery_pc = self.MAX_BAT_PC
        else:
            if(self.mCarClient.car_power_state or self.speed_val != 0):
                self.battery_pc = self.battery_pc - (self.speed_val*self.SPEED_BAT_DCHG_RATE+abs(self.mCarClient.environment_temp_val)*self.ENVIRONMENT_BAT_DCHG)*self.TOTAL_HOUR_OF_SIMULATION
                
                if self.battery_pc <=self.MIN_BAT_PC:
                    self.battery_pc = self.MIN_BAT_PC

        self.battery_pc = round(self.battery_pc,2)
       
        
    
    #function to publish the data
    def publish_data(self):
        self.battery_charge_simulation()
        self.door_lock_simulation()
        self.estimated_range_simulation()
        self.pub_data[ "speed"] = self.speed_val 
        self.pub_data["battery"] =  self.battery_pc
        self.pub_data["door_lock"] = self.door_lock_state
        self.pub_data["estimated_range"] = self.estimated_range_data
        self.pub_data["meter_reading"] = self.distance_travelled
        self.mCarClient.on_request_publish(self.pub_data)

        self.write_parameters()

        
    #function to simulate door lock 
    def door_lock_simulation(self):
        if(self.mCarClient.car_power_state):
            if(self.speed_val>self.DOOR_LOCK_THRESHOLD):
                self.door_lock_state = True
            elif(self.speed_val==0 and self.mCarClient.manual_door_state=="open"):
                self.door_lock_state = False
        else:
            self.door_lock_state = False
     
    #function to simulate estimated range 
    def estimated_range_simulation(self):
        self.estimated_range_data = self.battery_pc * self.EST_RANGE_FULL_BATTERY/100
        
    def distance_simulation(self):
        self.distance_travelled = self.distance_travelled + self.speed_val * self.TOTAL_HOUR_OF_SIMULATION
        self.distance_travelled = round(self.distance_travelled,2)
        print(f"Distance simulation {self.distance_travelled}")


    def calculate_max_speed(self,car_acceeleration_valueeleration_input):
        return self.BASE_MAX_SPEED * (car_acceeleration_valueeleration_input / 255)

    def car_acceeleration_valueeleration_simulation(self, car_acceeleration_valueeleration_input):
        # Calculate rate of change
        car_acceeleration_valueeleration_change = car_acceeleration_valueeleration_input - self.prev_car_acceeleration_valueeleration_input
        max_speed = self.calculate_max_speed(car_acceeleration_valueeleration_input)
        # print(f"car_acceeleration_value: {car_acceeleration_valueeleration_change}")
     
        car_acceeleration_valueeleration_factor = self.BASE_car_ACCecar_acceeleration_valueELERATION_FACTOR * (1 + abs(car_acceeleration_valueeleration_change) / 255)

        speed_increment = car_acceeleration_valueeleration_input * car_acceeleration_valueeleration_factor

        if car_acceeleration_valueeleration_input>= self.prev_car_acceeleration_valueeleration_input and self.speed_val < max_speed:
            self.speed_val += speed_increment
        
        self.speed_val -= self.speed_val * self.FRICTION_FACTOR
        
        
        if car_acceeleration_valueeleration_input > self.prev_car_acceeleration_valueeleration_input and car_acceeleration_valueeleration_input !=0 and self.speed_val > max_speed:
            self.speed_val = max_speed
        if self.speed_val < self.BASE_MIN_SPEED:
            
            self.speed_val = self.BASE_MIN_SPEED
   
        self.prev_car_acceeleration_valueeleration_input = car_acceeleration_valueeleration_input
        # prev_brake_input = brake_input
        if self.speed_val > self.BASE_MAX_SPEED:

            self.speed_val = self.BASE_MAX_SPEED
        if self.battery_pc < self.LOW_BAT_PC:
            self.speed_val = self.BASE_MIN_SPEED

        self.speed_val = round(self.speed_val,2)


    def break_simulation(self, brake_input):
   
        # Calculate rate of change
        brake_change = brake_input - self.prev_brake_input
    
        # Adjust brake factor based on rate of change
        brake_factor = self.BASE_BREAK_FACTOR * (1 + abs(brake_change) / 255)
    
        # Calculate speed decrement
        speed_decrement = brake_input * brake_factor
    
        # Update speed
        self.speed_val -= speed_decrement
    
        # Update previous brake input
        self.prev_brake_input = brake_input

        if self.speed_val < 0:
            self.speed_val = 0
        
        if self.battery_pc < self.LOW_BAT_PC:
            self.speed_val = self.BASE_MIN_SPEED        

        self.speed_val = round(self.speed_val,2)

    def car_wheel_simulation(self,car_wheel_value):
        if 0 < car_wheel_value <= 127:
            car_wheel_value = 'R'
        elif 127 < car_wheel_value <= 255:
            car_wheel_value = 'L'

        return car_wheel_value
    
    def car_break_counter(self,car_break_value):
        if car_break_value > 5 and self.break_count_state and self.speed_val != 0:
            self.break_counter += 1
            self.break_count_state = False
        elif car_break_value < 5:
            self.break_count_state = True


    async def car_simulation(self):
        
                
        while True:    

            try:
                
                if self.mCarClient.car_power_state:

                    if self.mCarClient.key_status == "present":
                        self.stop_event.set()
                        
                        async with self.recv_lock:
                            
                            if self.can_receive:
                                car_break_value = self.can_receive['car_break']
                                car_acceeleration_value = self.can_receive['car_acceleration']
                                car_wheel_value = self.can_receive['car_wheel']
                            
                                car_wheel_value = self.car_wheel_simulation(car_wheel_value)
                                
                                self.car_break_counter(car_break_value)

                                print(f"\nCAN message:\nbreak: {car_break_value}\ncar_acceeleration_value: {car_acceeleration_value}\ncar_wheel_value: {car_wheel_value}\nbreakCount: {self.break_counter}\n ")

                                self.car_acceeleration_valueeleration_simulation(car_acceeleration_value)
                                self.break_simulation(car_break_value)
                                print(f"Speed: {self.speed_val}")
                                self.distance_simulation()
                            
                            if self.received_packets:
                                pkt = self.received_packets.pop(0)  # Get the first packet
                                print(f"\nData Received on SomeIP: {pkt.payload}\n")  # Shows the payload as a hex string

                                #json.loads(pkt.payload)
                                object_distance = json.loads(pkt.payload)["distance"]
                                object_type = json.loads(pkt.payload)["object_type"]

                                # print(object_distance)
                                # print(object_type)
                    self.publish_data()
                elif self.mCarClient.charging_state:
                    self.publish_data()
                    self.stop_event.clear()
                elif not self.mCarClient.car_power_state :
                    self.stop_event.clear()
            except Exception as e:
                print(f"\nERROR {e}")
            
            await asyncio.sleep(self.LOOP_DELAY)
    
    
    async def start_simulation(self):
        #Run all coroutines concurrently
        self.receiver_task = asyncio.create_task(self.receiver.run())
        self.receiver_can_task = asyncio.create_task(self.can_handler.receive_message())
        #await self.receiver_task
        # self.stop_event.set()
        await asyncio.gather(self.receiver_task, self.car_simulation(), self.receiver_can_task)

        
    def start(self):
        self.loop = asyncio.get_event_loop()
        
        try:
            self.mCarClient.mqtt_connect()
            self.loop.run_until_complete(self.start_simulation())
            # asyncio.run(self.start_simulation())
        except Exception as e:
            print(f"Terminating with error : {e}")
        finally:
            # Signal the receiver thread to stop
            self.stop_event.set()

            #Wait for the receiver thread to finish
            #await self.receiver_task

            print("Receiver thread stopped gracefully.")
            print(f"Total received packets: {len(self.received_packets)}")
            self.mCarClient.mqtt_disconnect()
            self.loop.close()


    #Function to handle keyboard interruption
    def shutdown(self, signal, frame):
        for task in asyncio.all_tasks(self.loop):
            task.cancel()
        self.loop.stop()

if __name__ == '__main__':
    
    mqtt_host = "192.168.1.9"
    someIP_host = "192.168.1.16"
    mqtt_port = 1884
    someIP_port = 30490
    car_sim = CarSimulation(mqtt_host,mqtt_port,someIP_host,someIP_port)
    
    car_sim.start()