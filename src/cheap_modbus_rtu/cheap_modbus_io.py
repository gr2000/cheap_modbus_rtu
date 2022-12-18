"""@package cheap_modbus_rtu
Lightweight control of cheap Modbus RTU components using Python
"""
from .modbus_rtu_master import ModbusRtuMaster

class CheapModbusRelayIOModule():
    """Control affordable Modbus relay PCBs via RS-485 Modbus RTU

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
    """Control via RS-485 Modbus RTU:
    
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
    """Control via RS-485 Modbus RTU:
    
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
    """Control via RS-485 Modbus RTU:
    
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
    """Control via RS-485 Modbus RTU:
    
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


class PWM8A04():
    """Control PWM8A04 3-channel PWM output modules via RS-485 Modbus RTU

    The PWM8A04 seems to come with a pre-set slave ID of 1.

    Brand name is "eletechsup", available at https://www.eletechsup.com

    This is for the three-channel variant.
    """
    FREQ_REG_OFFSET = 40000
    DUTY_REG_OFFSET = 40112
    BROADCAST_SLAVE_ID = 0xFF # This is non-standard
    SLAVE_ID_REGISTER = 40254

    def __init__(self, serial_device_name: str = None, slave_id: int = 1, **kwargs):
        self.master = ModbusRtuMaster(serial_device_name, **kwargs)
        self.slave_id = slave_id

    def get_output_frequency(self, output_no: int) -> int:
        """Return the current frequency setpoint for output

        @param output_no: Output number, can be 1, 2 or 3
        @return: Frequency of PWM in Hz, valid range is 1...20000
        """
        frequency, = self.master.read_analog_holding_registers(
            self.slave_id,
            output_no + self.FREQ_REG_OFFSET
        )
        return frequency

    def set_output_frequency(self, output_no: int, frequency: int):
        """Set frequency for PWM output.

        @param output_no: Output number, can be 1, 2 or 3
        @param frequency: Frequency of PWM in Hz, valid range is 1...20000
        """
        self.master.set_analog_holding_register(
            self.slave_id,
            output_no + self.FREQ_REG_OFFSET,
            frequency
        )

    def get_output_duty(self, output_no: int) -> int:
        """Return the current PWM duty cycle setpoint value for output

        @param output_no: Output number, can be 1, 2 or 3
        @return: PWM duty cycle in percent, valid range is 0...100
        """
        duty, = self.master.read_analog_holding_registers(
            self.slave_id,
            output_no + self.DUTY_REG_OFFSET
        )
        return duty

    def set_output_duty(self, output_no: int, duty: int):
        """Set PWM duty cycle for output (high-active)

        @param output_no: Output number, can be 1, 2 or 3
        @param duty: PWM duty cycle in percent, valid range is 0...100
        """
        self.master.set_analog_holding_register(
            self.slave_id,
            output_no + self.DUTY_REG_OFFSET,
            duty
        )
    
    def set_slave_id(self, slave_id_new: int):
        """Set the slave ID
        """
        self.master.set_analog_holding_register(
            self.slave_id,
            self.SLAVE_ID_REGISTER,
            slave_id_new
        )
        self.slave_id = slave_id_new
    
    def get_broadcast_slave_id(self) -> int:
        """Sends a (nonstandard) broadcast query to all devices on the bus.
    
        These PWM modules seem to use 255 as a non-standard broadcast address..

        Returns the first found slave ID.
        
        This likely only works when only one device is attached to the bus
        """
        slave_id, = self.master.read_analog_holding_registers(
            self.BROADCAST_SLAVE_ID,
            self.SLAVE_ID_REGISTER
        )
        self.slave_id = slave_id
        return slave_id


class R4DIF08():
    """Control R4DIF08 8-channel digital input modules via RS-485 Modbus RTU

    The R4DIF08 seems to come with a pre-set slave ID of 1.

    Brand name is "eletechsup", available at https://www.eletechsup.com

    This is for the three-channel variant.
    """
    DI_REGISTER = 10001
    BROADCAST_SLAVE_ID = 0xFF # This is non-standard
    SLAVE_ID_REGISTER = 40255

    def __init__(self, serial_device_name: str = None, slave_id: int = 1, **kwargs):
        self.master = ModbusRtuMaster(serial_device_name, **kwargs)
        self.slave_id = slave_id

    # def get_inputs(self) -> tuple[bool, ...]:
    #     """Returns the state of the 8 digital inputs as a tuple of booleans
    #     """
    #     flags_8_ch = self.master.read_discrete_input_registers(
    #         self.slave_id, self.DI_REGISTER, 8
    #     )
    #     return flags_8_ch
    
    def set_slave_id(self, slave_id_new: int):
        """Set the slave ID
        """
        self.master.set_analog_holding_register(
            self.slave_id,
            self.SLAVE_ID_REGISTER,
            slave_id_new
        )
        self.slave_id = slave_id_new
    
    def get_broadcast_slave_id(self) -> int:
        """Sends a (nonstandard) broadcast query to all devices on the bus.
    
        These input modules seem to use 255 as a non-standard broadcast address..

        Returns the first found slave ID.
        
        This likely only works when only one device is attached to the bus
        """
        slave_id, = self.master.read_analog_holding_registers(
            self.BROADCAST_SLAVE_ID,
            self.SLAVE_ID_REGISTER
        )
        self.slave_id = slave_id
        return slave_id