"""@package cheap_modbus_rtu
Lightweight control of cheap Modbus RTU components using Python
"""
from .modbus_rtu_master import ModbusRtuMaster

class CheapModbusRelayIOModule():
    """Control via RS-485 Modbus RTU for the affordable Modbus relay PCBs

    These come in one, two, four, eight or more channel variants and feature
    different numbers of additional digital IO pins.
    
    While the relay outputs are insulated for mains voltage application,
    the digital IO pins are only featuring functional or low-voltage isolation,
    some variants do not have isolated inputs at all.

    The detailed implementation varies slightly between variants,
    the difference (for the time being) is the number of input state values
    contained in the tuple returned from the "get_inputs()" method.

    All other methods are identical.

    ==> Please see documentation of the derived classes for details:
    * Relay1Ch
    * Relay2Ch
    * Relay4Ch
    * Relay8Ch

    Brand name is "bestep" among others.
    """
    DI_REGISTER = 10001
    SLAVE_ID_REGISTER = 40001

    def __init__(self, serial_device_name: str = None, slave_id: int = 255, **kwargs):
        self.master = ModbusRtuMaster(serial_device_name, **kwargs)
        self.slave_id = slave_id
    
    def set_output(self, output_no: int, active: bool = True):
        """Output number is 1 or 2 for the two-channel variant
        """
        self.master.set_discrete_output_register(self.slave_id, output_no, active)
    
    def clear_output(self, output_no: int):
        """Output number is 1 or 2 for the two-channel variant
        """
        self.master.set_discrete_output_register(self.slave_id, output_no, False)
    
    def get_input(self, input_no: int) -> bool:
        """Return the state of the specified digital input

        Input number is 1 or 2 for the two-channel variant
        """
        flags_8_ch = self.master.read_discrete_input_registers(
            self.slave_id, self.DI_REGISTER, 8
            )
        return flags_8_ch[input_no-1]
    
    def set_slave_id(self, slave_id_new: int):
        """Set the slave ID
        """
        self.master.set_analog_holding_registers(
            self.slave_id,
            self.SLAVE_ID_REGISTER,
            (slave_id_new,),
            expect_echo_response=True
        )
        self.slave_id = slave_id_new
    
    def get_broadcast_slave_id(self) -> int:
        """Sends a broadcast query to all devices on the bus
        
        Returns the first found slave ID.
        
        This likely only works when only one device is attached to the bus
        """
        slave_id, = self.master.read_analog_holding_registers(
            0, self.SLAVE_ID_REGISTER, 1
        )
        self.slave_id = slave_id
        return slave_id


class Relay1Ch(CheapModbusRelayIOModule):
    """Control via RS-485 Modbus RTU for:
    
    1x Serial RS-485 Modbus RTU relay PCB

    ==> This is for the one-channel variant.

    This variant has:
        - one relay output and
        - one NON-ISOLATED(!) digital input
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_inputs(self) -> tuple[bool]:
        """Returns the state of the digital inputs as a tuple of booleans
        """
        flags_8_ch = self.master.read_discrete_input_registers(
            self.slave_id, self.DI_REGISTER, 8
        )
        return flags_8_ch[0:1]


class Relay2Ch(CheapModbusRelayIOModule):
    """Control via RS-485 Modbus RTU for:
    
    1x Serial RS-485 Modbus RTU relay PCB

    ==> This is for the two-channel variant.

    This variant has:
        - two relay outputs and
        - two functionally isolated digital inputs
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_inputs(self) -> tuple[bool, bool]:
        """Returns the state of the digital inputs as a tuple of booleans
        """
        flags_8_ch = self.master.read_discrete_input_registers(
            self.slave_id, self.DI_REGISTER, 8
        )
        return flags_8_ch[0:2]


class Relay4Ch(CheapModbusRelayIOModule):
    """Control via RS-485 Modbus RTU for:
    
    1x Serial RS-485 Modbus RTU relay PCB

    ==> This is for the four-channel variant.

    This variant has:
        - four relay outputs and
        - four functionally isolated digital inputs
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_inputs(self) -> tuple[bool, bool]:
        """Returns the state of the digital inputs as a tuple of booleans
        """
        flags_8_ch = self.master.read_discrete_input_registers(
            self.slave_id, self.DI_REGISTER, 8
        )
        return flags_8_ch[0:4]


class Relay8Ch(CheapModbusRelayIOModule):
    """Control via RS-485 Modbus RTU for:
    
    1x Serial RS-485 Modbus RTU relay PCB

    ==> This is for the eight-channel variant.

    This variant has:
        - eight relay outputs and
        - eight functionally isolated digital inputs
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_inputs(self) -> tuple[bool, bool]:
        """Returns the state of the digital inputs as a tuple of booleans
        """
        flags_8_ch = self.master.read_discrete_input_registers(
            self.slave_id, self.DI_REGISTER, 8
        )
        return flags_8_ch