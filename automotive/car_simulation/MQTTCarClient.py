import paho.mqtt.client as mqtt
import time
import json
import asyncio

class MQTTCarClient:
    
    # Set up your broker details (hostname, port, etc.)
    #mqtt_host = "192.168.1.51"
    #mqtt_port = 1883
    
    #publish topics
    pubtopic = "pub/input_tab/fw_output"
 
    #subscribe topics
    sub_car_power = "sub/input_tab/car_power"
    sub_charging_state = "sub/input_tab/charging_state"
    sub_key_status = "sub/input_tab/key_status"
    sub_simulation_state = "sub/input_tab/simulation_state"
    sub_object_detected = "sub/input_tab/object_detected"
    sub_dust = "sub/input_tab/dust"
    sub_snow = "sub/input_tab/snow"
    sub_environment_temp = "sub/input_tab/environment_temp"
    sub_manual_door_state = "sub/input_tab/manual_door_state"
    
    car_power_state = False
    charging_state = False
    simulation_state = False
    key_status= "absent"
    snow_state= False 
    dust_state= False 
    environment_temp_val = 21
    manual_door_state="close"
    
    door_lock_state = False
    
    THRESHOLD_REDUCTION_BY_DUST_PC = 0.1
    THRESHOLD_REDUCTION_BY_SNOW_PC = 0.2
    NORMAL_OBJECT_DISTANCE_THRESHOLD= 50.0  #50 meters
    
    object_detected_threshold = NORMAL_OBJECT_DISTANCE_THRESHOLD
    object_detected = False
    
    def __init__(self,mqtt_host,mqtt_port):
        
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        
        # Create an MQTT client instance
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        #self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        self.client.message_callback_add(self.sub_car_power,self.on_car_power)
        self.client.message_callback_add(self.sub_charging_state,self.on_charging_state)
        self.client.message_callback_add(self.sub_key_status,self.on_key_status)
        self.client.message_callback_add(self.sub_simulation_state,self.on_simulation_state)
        self.client.message_callback_add(self.sub_object_detected,self.on_object_detected)
        self.client.message_callback_add(self.sub_dust,self.on_dust)
        self.client.message_callback_add(self.sub_snow,self.on_snow)
        self.client.message_callback_add(self.sub_environment_temp,self.on_environment_temp)
        self.client.message_callback_add(self.sub_manual_door_state,self.on_manual_door_state)
        
    #connection callback function
    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        print("Connected to MQTT broker!")
        self.client.subscribe(self.sub_car_power)
        self.client.subscribe(self.sub_charging_state)
        self.client.subscribe(self.sub_key_status)
        self.client.subscribe(self.sub_simulation_state)
        self.client.subscribe(self.sub_object_detected)
        self.client.subscribe(self.sub_dust)
        self.client.subscribe(self.sub_snow)
        self.client.subscribe(self.sub_environment_temp)
        self.client.subscribe(self.sub_manual_door_state)
        print("Subscribed!")
        
    #disconnect callback function
    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        print("Disconnected to MQTT broker!")
        #self.client.connect(self.mqtt_host, self.mqtt_port, keepalive=60)


    #Message receive callback function
    def on_car_power(self, client, userdata, message):
        if(not self.charging_state):
            try:
                json_string = message.payload.decode()                       #decoding the received message
                print(f"Received message: {json_string} on {message.topic}") #printing received message
                self.car_power_state = json.loads(json_string)["car_power"]
                print(self.car_power_state)
                if not self.car_power_state:
                    self.key_status = "absent"
            except Exception as e:
                print(f"Message Decoding error : {e}")
                #return 0
        
    def on_charging_state(self, client, userdata, message):
        if(not self.car_power_state):
            try:
                json_string = message.payload.decode()                       #decoding the received message
                print(f"Received message: {json_string} on {message.topic}") #printing received message
                self.charging_state = json.loads(json_string)["charging_state"]
                print(self.charging_state)
            except Exception as e:
                print(f"Message Decoding error : {e}")
            d
    def on_key_status(self, client, userdata, message):
        if(self.car_power_state):
            try:
                json_string = message.payload.decode()                       #decoding the received message
                print(f"Received message: {json_string} on {message.topic}") #printing received message
                self.key_status = json.loads(json_string)["key_status"]
                if self.key_status == 'absent':
                    self.key_status = 'present'
                print(self.key_status)
            except Exception as e:
                print(f"Message Decoding error : {e}")
            
    def on_simulation_state(self, client, userdata, message):
        if(self.car_power_state):
            try:
                json_string = message.payload.decode()                       #decoding the received message
                print(f"Received message: {json_string} on {message.topic}") #printing received message
                self.simulation_state = json.loads(json_string)["simulation_state"]
                print(self.simulation_state)
            except Exception as e:
                print(f"Message Decoding error : {e}")
            
    def on_object_detected(self, client, userdata, message):
        if(self.car_power_state and self.key_status == "present" and self.simulation_state):
            try:
                json_string = message.payload.decode()                       #decoding the received message
                print(f"Received message: {json_string} on {message.topic}") #printing received message
                object_distance = json.loads(json_string)["distance"]
                object_type = json.loads(json_string)["object_type"]

                print(object_distance)
                print(object_type)
                
                if(object_type == "car" or object_type == "pedestrian" or object_type == "red_signal"):
                    if(self.dust_state and self.snow_state):
                        self.object_detected_threshold = self.NORMAL_OBJECT_DISTANCE_THRESHOLD*(1-self.THRESHOLD_REDUCTION_BY_DUST_PC-self.THRESHOLD_REDUCTION_BY_SNOW_PC)
                    elif(self.snow_state):
                        self.object_detected_threshold = self.NORMAL_OBJECT_DISTANCE_THRESHOLD*(1-self.THRESHOLD_REDUCTION_BY_SNOW_PC)
                    elif(self.dust_state):
                        self.object_detected_threshold = self.NORMAL_OBJECT_DISTANCE_THRESHOLD*(1-self.THRESHOLD_REDUCTION_BY_DUST_PC)
                    else:
                        self.object_detected_threshold = self.NORMAL_OBJECT_DISTANCE_THRESHOLD
                    
                    self.object_detected = True 
                else:
                    self.object_detected = False 
                
            except Exception as e:
                print(f"Message Decoding error : {e}")
            
    def on_dust(self, client, userdata, message):
        if(self.car_power_state):
            try:
                json_string = message.payload.decode()                       #decoding the received message
                print(f"Received message: {json_string} on {message.topic}") #printing received message
                self.dust_state = json.loads(json_string)["dust"]
                print(self.dust_state)
            except Exception as e:
                print(f"Message Decoding error : {e}")
            
    def on_snow(self, client, userdata, message):
        if(self.car_power_state):
            try:
                json_string = message.payload.decode()                       #decoding the received message
                print(f"Received message: {json_string} on {message.topic}") #printing received message
                self.snow_state = json.loads(json_string)["snow"]
                print(self.snow_state)
            except Exception as e:
                print(f"Message Decoding error : {e}")
            
    def on_environment_temp(self, client, userdata, message):
        if(self.car_power_state):
            try:
                json_string = message.payload.decode()                       #decoding the received message
                print(f"Received message: {json_string} on {message.topic}") #printing received message
                self.environment_temp_val = json.loads(json_string)["environment_temp"]
                print(self.environment_temp_val)
            except Exception as e:
                print(f"Message Decoding error : {e}")
            
    def on_manual_door_state(self, client, userdata, message):
        if(self.car_power_state):
            try:
                json_string = message.payload.decode()                       #decoding the received message
                print(f"Received message: {json_string} on {message.topic}") #printing received message
                self.manual_door_state = json.loads(json_string)["manual_door_state"]
                print(self.manual_door_state)
                
            except Exception as e:
                print(f"Message Decoding error : {e}")
    
    #function to publish the data on publish topic
    def on_request_publish(self,pub_data):
        print(f"\nPublished {pub_data}")
        json_data = json.dumps(pub_data)
        self.client.publish(self.pubtopic, json_data,qos=0)
        
    def mqtt_connect(self):
        self.client.connect(self.mqtt_host, self.mqtt_port, keepalive=60)

        # Start the MQTT loop
        self.client.loop_start()
        
    def mqtt_disconnect(self):
        # Stop the MQTT client loop
        self.client.loop_stop()
        self.client.disconnect()
        

