# cheap_modbus_rtu

## Lightweight control of cheap Modbus RTU components using Python

### Currently supported hardware

### "bestep" brand:
* 2-CH Digital IN + Relay module  
  ![2-CH Relay PCB](./docs/img/relay_2_ch.jpg)

* 4-CH Digital IN + Relay module  
  ![4-CH Relay PCB](./docs/img/relay_4_ch.jpg)

* (untested) 8-CH Digital IN + Relay module  
  (no image)

### "eletechsup" brand:
* PWM8A04 3-CH PWM OUT PCB  
  ![PWM8A04 PCB](./docs/img/PWM8A04.jpg)

* R4DIF08 8-CH Digital IN module  
  ![R4DIF08 PCB](./docs/img/R4DIF08.jpg)

* N4AIA04 4-CH 0..5V / 0..10V / 0..20mA analog input module  
  ![N4AIA04 PCB](./docs/img/N4AIA04.jpg)

* N4DAC02 2-CH 0..5V / 0..10V analog output module  
  ![N4DAC02](./docs/img/N4DAC02.jpg)

```
# This requires Python >= 3.9 
# and recent version of setuptools and pip
user@linux:~/mysrc$ python -m pip install --upgrade pip

# Install from local git sources:
user@linux:~/mysrc$ git clone https://github.com/ul-gh/cheap_modbus_rtu.git
user@linux:~/mysrc$ cd cheap_modbus_rtu
user@linux:~/mysrc$ pip install .
```

## Documentation Link:  
[API Documentation (Github Link)](https://ul-gh.github.io/cheap_modbus_rtu/html/annotated.html) 

### R4DIF08, 8-Channel digital input PCB: Read all eight inputs

```python
from cheap_modbus_rtu import R4DIF08

# Slave ID for these modules is pre-set to 1
input_module = R4DIF08(slave_id=1, serial_device_name="/dev/ttyUSB0")

inputs = input_module.get_inputs()
print(inputs)
```

### Relay IO PCB: Toggle one relay on-off in a 1-second cycle

```python
import time
# Also works with the other multi-channel variants
from cheap_modbus_rtu import Relay2Ch

# Slave ID for these modules is pre-set to 255
modbus_relay = Relay2Ch(slave_id=255, serial_device_name="/dev/ttyUSB0")

while True:
    modbus_relay.set_output(1, True)
    time.sleep(0.5)
    modbus_relay.set_output(1, False)
    time.sleep(0.5)
```

### PWM8A04, 3-Channel PWM output PCB: Set output 1 to 20 kHz, 33 % duty cycle

```python
from cheap_modbus_rtu import PWM8A04

# Slave ID for these PWM modules is pre-set to 1
pwm = PWM8A04(slave_id=1, serial_device_name="/dev/ttyUSB0")

pwm.set_output_frequency(1, 20000)
pwm.set_output_duty(1, 33)
```

#### Relay IO PCB: Read both inputs of the 2-Channel variant and write them directly to the relay outputs

```python
while True:
    input_1 = modbus_relay.get_input(1)
    input_2 = modbus_relay.get_input(2)
    modbus_relay.set_output(1, input_1)
    modbus_relay.set_output(2, input_2)
    print(f"\rInput 1: {input_1}  Input 2: {input_2}  ", end="")
    time.sleep(0.1)
```

    Input 1: False  Input 2: False  


#### Relay IO PCB: Set Slave ID from 255 to 1
This must only be done once, not at every device start, otherwise flash wear might be an issue. Once a different Slave ID is configured, invoke the constructor of this library with the new ID as an argument.

```python
modbus_relay.get_broadcast_slave_id()
>>>     255

modbus_relay.set_slave_id(1)
modbus_relay.get_broadcast_slave_id()
>>>     1
```


Nice documentation of the Modbus-RTU protocol (English):
[https://ipc2u.com Modbus Protocol Description and Examples](https://ipc2u.com/articles/knowledge-base/modbus-rtu-made-simple-with-detailed-descriptions-and-examples/)

(Same content in German) Beschreibung des Modbus-RTU Protokolls:
[https://ipc2u.de](https://ipc2u.de/artikel/wissenswertes/modbus-rtu-einfach-gemacht-mit-detaillierten-beschreibungen-und-beispielen/) 
