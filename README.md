# cheap_modbus_rtu

## Lightweight control of cheap Modbus RTU components using Python

#### This is work-in-progress!

```
# This requires Python >= 3.9 
# and recent version of setuptools and pip
user@linux:~/mysrc$ python -m pip install --upgrade pip

# Install from local git sources:
user@linux:~/mysrc$ git clone https://github.com/ul-gh/cheap_modbus_rtu.git
user@linux:~/mysrc$ cd cheap_modbus_rtu
user@linux:~/mysrc$ pip install .
```

### Relay IO PCB, complete example: Toggle one relay on-off in a 1-second cycle

```python
import time
# Also works with the multi-channel variants
from cheap_modbus_rtu import Relay1Ch

# Slave ID for these modules is pre-set to 255
modbus_relay = Relay1Ch("/dev/ttyUSB0", slave_id=255)

while True:
    modbus_relay.set_output(1, True)
    time.sleep(0.5)
    modbus_relay.set_output(1, False)
    time.sleep(0.5)
```

### 3-Channel PWM output PCB, complete example: Set output 1 to 20 kHz, 33 % duty cycle

```python
from cheap_modbus_rtu import PWMOutput3Ch

# Slave ID for these PWM modules is pre-set to 1
pwm = PWMOutput3Ch("/dev/ttyUSB0", slave_id=1)

pwm.set_output_frequency(1, 20000)
pwm.set_output_duty(1, 33)
```


Nice documentation of the Modbus-RTU protocol (English):
[https://ipc2u.com Modbus Protocol Description and Examples](https://ipc2u.com/articles/knowledge-base/modbus-rtu-made-simple-with-detailed-descriptions-and-examples/)

(Same content in German) Beschreibung des Modbus-RTU Protokolls:
[https://ipc2u.de](https://ipc2u.de/artikel/wissenswertes/modbus-rtu-einfach-gemacht-mit-detaillierten-beschreibungen-und-beispielen/)


### Relay IO PCB: Read both inputs of the 2-Channel variant and write them directly to the relay outputs

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

Please also see:  
[API Documentation (Github Link)](https://ul-gh.github.io/cheap_modbus_rtu/html/classcheap__modbus__rtu_1_1cheap__modbus__io_1_1_cheap_modbus_relay_i_o_module.html)  
