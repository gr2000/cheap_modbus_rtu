# cheap_modbus_rtu

## Lightweight control of cheap Modbus RTU components using Python

### Incomplete, work-in-progress!

```
This requires Python >= 3.9 and recent version of setuptools and pip
python -m pip install --upgrade pip

Install from local git sources:
git clone https://github.com/ul-gh/cheap_modbus_rtu.git
cd cheap_modbus_rtu
pip install .
```

```python
import time
from cheap_modbus_rtu import Relay2Ch
```


```python
modbus_relay = Relay2Ch("/dev/ttyUSB0", slave_id=255)
```

Slave ID ist bei diesen Platinen voreingestellt auf 255.

Hier ändern wir das nun auf 1: Das darf natürlich nur einmal in der Konfiguration gemacht werden, um den Flash nicht zu zerstören.

In allen folgenden Initialisierungen wird man dann den Konstruktor mit der neuen slave_id aufrufen.

Beschreibung des Modbus-RTU Protokolls:
[https://ipc2u.de](https://ipc2u.de/artikel/wissenswertes/modbus-rtu-einfach-gemacht-mit-detaillierten-beschreibungen-und-beispielen/)


```python
modbus_relay.get_broadcast_slave_id()
>>>     255

modbus_relay.set_slave_id(1)
modbus_relay.get_broadcast_slave_id()
>>>     1
```

Hier werden in der Endlossschleife beide Optokopplereingänge gelesen und sofort auf die Relaisausgänge zurückgeschrieben.


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
