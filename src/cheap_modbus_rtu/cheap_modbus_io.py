"""@package cheap_modbus_rtu
Lightweight control of cheap Modbus RTU components using Python
"""
import time
from .modbus_rtu_master import ModbusRtuMaster


class ModbusModuleABC():
    """Base class for cheap Modbus IO modules.
    
    Configuration constants like register values are
    device-specific and implemented in the derived classes.
    """
    def __init__(self,
                 slave_id: int,
                 serial_device_name: str,
                 baudrate: int,
                 **kwargs
                 ):
        self.master = ModbusRtuMaster(serial_device_name, baudrate, **kwargs)
        self.slave_id = slave_id
    
    def get_slave_id(self) -> int:
        """Sends a broadcast query to all devices on the bus
        
        This only works when only one device is attached to the bus

        Returns:
            The first found slave ID.
        """
        slave_id, = self.master.read_holding_registers(
            self.BROADCAST_SLAVE_ID,
            self.SLAVE_ID_REGISTER
        )
        self.slave_id = slave_id
        return slave_id

    def set_slave_id(self, slave_id_new: int):
        """Set the slave ID

        Warning:
            While usually undocumented, it is possible that the device writes
            directly to FLASH, thus frequent writes could damage the chip!

        Args:
            slave_id_new:   New Modbus slave ID
        """
        self.master.set_holding_register(
            self.slave_id,
            self.SLAVE_ID_REGISTER,
            slave_id_new
        )
        self.slave_id = slave_id_new

    def set_baudrate(self, baudrate: int = 9600):
        """Set RS485 serial baud rate

        Most devices require cycling the power supply after running this command
        before the new baud rate applies.

        Warning:
            While usually undocumented, it is possible that the device writes
            directly to FLASH, thus frequent writes could damage the chip!
        
        Args:
            baudrate:  Can be 1200, 2400, 4800, 9600 (default) or 19200
        """
        try:
            reg_val = self.BAUDRATE_KEYS[baudrate]
        except KeyError:
            baudrates_str = ", ".join((str(i) for i in self.BAUDRATE_KEYS.keys()))
            raise ValueError(f"Invalid baud rate. Valid rates: {baudrates_str}")
        self.master.set_holding_register(
            self.slave_id,
            self.BAUDRATE_REGISTER,
            reg_val
        )

    def do_factory_reset(self):
        """Restore factory default settings.
        
        You must cycle the power supply after this command.

        Expect a CRC mismatch error when invoking this function,
        I don't know if this is always the case.
        """
        self.master.set_holding_register(
            self.slave_id,
            self.FACTORY_RESET_REGISTER,
            self.FACTORY_RESET_VALUE
        )


class RelayModule(ModbusModuleABC):
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
    BAUDRATE_REGISTER = 41002 #Index 0x03E9
    BROADCAST_SLAVE_ID = 0
    BAUDRATE_KEYS = {1200: 0, 2400: 1, 4800: 2, 9600: 3, 19200: 4}

    def __init__(self,
                 slave_id: int = 255,
                 serial_device_name: str = None,
                 baudrate: int = 9600,
                 **kwargs
                 ):
        super().__init__(slave_id, serial_device_name, baudrate, **kwargs)
    
    def set_output(self, output_no: int, active: bool = True):
        """Set specified output

        Args:
            output_no:  Output number, starts counting at 1
            active:     Enable output if active == True (default)
                        Disable output if active == False
        """
        if 1 > output_no or output_no > self.NUM_IOS:
            raise ValueError(f"Output number must be between 1 and {self.NUM_IOS}")
        self.master.set_discrete_output_register(self.slave_id, output_no, active)
    
    def clear_output(self, output_no: int):
        """Disable specified output

        Args:
            output_no:  Output number, starts counting at 1
        """
        if 1 > output_no or output_no > self.NUM_IOS:
            raise ValueError(f"Output number must be between 1 and {self.NUM_IOS}")
        self.master.set_discrete_output_register(self.slave_id, output_no, False)
    
    def get_input(self, input_no: int) -> bool:
        """Return the state of the specified digital input

        Args:
            input_no:   Input number, starts counting at 1

        Returns:
            True if input signal is active, False if inactive
        """
        if 1 > input_no or input_no > self.NUM_IOS:
            raise ValueError(f"Input number must be between 1 and {self.NUM_IOS}")
        flags = self.master.read_discrete_input_registers(
            self.slave_id,
            self.DI_REGISTER,
            # Only reading eight registers seems to be implemented..
            8
        )
        return flags[input_no-1]

    def get_inputs(self) -> tuple[bool, ...]:
        """Returns the state of the digital inputs

        Returns:
            Tuple of boolean flags, one for each input
        """
        flags = self.master.read_discrete_input_registers(
            self.slave_id,
            self.DI_REGISTER,
            # Only reading eight registers seems to be implemented..
            8
        )
        return flags[0:self.NUM_IOS]

    def set_slave_id(self, slave_id_new: int):
        """Set the slave ID

        Warning:
            While usually undocumented, it is possible that the device writes
            directly to FLASH, thus frequent writes could damage the chip!

        Args:
            slave_id_new:   New Modbus slave ID
        """
        self.master.set_holding_registers(
            self.slave_id,
            self.SLAVE_ID_REGISTER,
            (slave_id_new,),
            expect_echo_response=True
        )
        self.slave_id = slave_id_new

    def set_baudrate(self, baudrate: int = 9600):
        """Set RS485 serial baud rate

        Warning:
            While undocumented, it is possible that the device writes directly
            to FLASH, thus frequent writes could damage the chip!
        
        Args:
            FIXME: 1200 and 2400 are undocumented. Really possible?
            baudrate:  Can be 1200, 2400, 4800, 9600 (default) or 19200
        """
        try:
            reg_val = {1200: 0, 2400: 1, 4800: 2, 9600: 3, 19200: 4}[baudrate]
        except KeyError:
            raise ValueError("Baud rate must be 1200, 2400, 4800, 9600 or 19200")
        # These relay modules seem to only support function code 0x10 for setting
        # multiple holding registers and not fc 0x06 for setting one register only
        self.master.set_holding_registers(
            self.slave_id,
            self.BAUDRATE_REGISTER,
            (reg_val,)
        )

    def do_factory_reset(self):
        """Factory reset not implemented for the relay modules
        """
        raise NotImplementedError("Factory reset not implemented for the relay modules")


class Relay1Ch(RelayModule):
    """Control via RS-485 Modbus RTU:
    
    1x Serial RS-485 Modbus RTU relay PCB

    ==> This is for the one-channel variant.

    This variant has:
        - one relay output and
        - one NON-ISOLATED(!) digital input
    """
    NUM_IOS = 1

    def __init__(self,
                 slave_id: int = 255,
                 serial_device_name: str = None,
                 baudrate: int = 9600,
                 **kwargs
                 ):
        super().__init__(slave_id, serial_device_name, baudrate, **kwargs)


class Relay2Ch(RelayModule):
    """Control via RS-485 Modbus RTU:
    
    1x Serial RS-485 Modbus RTU relay PCB

    ==> This is for the two-channel variant.

    This variant has:
        - two relay outputs and
        - two functionally isolated digital inputs
    """
    NUM_IOS = 2

    def __init__(self,
                 slave_id: int = 255,
                 serial_device_name: str = None,
                 baudrate: int = 9600,
                 **kwargs
                 ):
        super().__init__(slave_id, serial_device_name, baudrate, **kwargs)

class Relay4Ch(RelayModule):
    """Control via RS-485 Modbus RTU:
    
    1x Serial RS-485 Modbus RTU relay PCB

    ==> This is for the four-channel variant.

    This variant has:
        - four relay outputs and
        - four functionally isolated digital inputs
    """
    NUM_IOS = 4

    def __init__(self,
                 slave_id: int = 255,
                 serial_device_name: str = None,
                 baudrate: int = 9600,
                 **kwargs
                 ):
        super().__init__(slave_id, serial_device_name, baudrate, **kwargs)

class Relay8Ch(RelayModule):
    """Control via RS-485 Modbus RTU:
    
    1x Serial RS-485 Modbus RTU relay PCB

    ==> This is for the eight-channel variant.

    This variant has:
        - eight relay outputs and
        - eight functionally isolated digital inputs
    """
    NUM_IOS = 8

    def __init__(self,
                 slave_id: int = 255,
                 serial_device_name: str = None,
                 baudrate: int = 9600,
                 **kwargs
                 ):
        super().__init__(slave_id, serial_device_name, baudrate, **kwargs)


class PWM8A04(ModbusModuleABC):
    """Control PWM8A04 3-channel PWM output modules via RS-485 Modbus RTU

    The PWM8A04 seem to come with a pre-set slave ID of 1.

    Brand name is "eletechsup", available at https://www.eletechsup.com

    This is for the three-channel variant.
    """
    FREQ_REG_OFFSET = 40000
    DUTY_REG_OFFSET = 40112
    SLAVE_ID_REGISTER = 40254
    BAUDRATE_REGISTER = 40255
    FACTORY_RESET_REGISTER = 40252
    FACTORY_RESET_VALUE = 0
    BROADCAST_SLAVE_ID = 0xFF # This is non-standard
    BAUDRATE_KEYS = {
        1200: 0, 2400: 1, 4800: 2, 9600: 3, 19200: 4, 38400: 5, 57600: 6, 115200: 7
    }

    def __init__(self,
                 slave_id: int = 1,
                 serial_device_name: str = None,
                 baudrate: int = 9600,
                 **kwargs
                 ):
        super().__init__(slave_id, serial_device_name, baudrate, **kwargs)

    def get_output_frequency(self, output_no: int) -> int:
        """Return the current frequency setpoint for output

        Args:
            output_no:  Output number, can be 1, 2 or 3

        Returns:
            Frequency of PWM in Hz, valid range is 1...20000
        """
        if 1 > output_no or output_no > 3:
            raise ValueError("Output number must be 1, 2 or 3")
        frequency, = self.master.read_holding_registers(
            self.slave_id,
            output_no + self.FREQ_REG_OFFSET
        )
        return frequency

    def set_output_frequency(self, output_no: int, frequency: int):
        """Set frequency for PWM output.

        Args:
            output_no:  Output number, can be 1, 2 or 3
            frequency:  Frequency of PWM in Hz, valid range is 1...20000
        """
        if 1 > output_no or output_no > 3:
            raise ValueError("Output number must be 1, 2 or 3")
        self.master.set_holding_register(
            self.slave_id,
            output_no + self.FREQ_REG_OFFSET,
            frequency
        )

    def get_output_duty(self, output_no: int) -> int:
        """Return the current PWM duty cycle setpoint value for output

        Args:
            output_no:  Output number, can be 1, 2 or 3

        Returns:
            PWM duty cycle in percent, valid range is 0...100
        """
        if 1 > output_no or output_no > 3:
            raise ValueError("Output number must be 1, 2 or 3")
        duty, = self.master.read_holding_registers(
            self.slave_id,
            output_no + self.DUTY_REG_OFFSET
        )
        return duty

    def set_output_duty(self, output_no: int, duty: int):
        """Set PWM duty cycle for output (high-active)

        Args:
            output_no:  Output number, can be 1, 2 or 3
            duty:       PWM duty cycle in percent, valid range is 0...100
        """
        if 1 > output_no or output_no > 3:
            raise ValueError("Output number must be 1, 2 or 3")
        self.master.set_holding_register(
            self.slave_id,
            output_no + self.DUTY_REG_OFFSET,
            duty
        )


class R4DIF08(ModbusModuleABC):
    """Control R4DIF08 8-channel digital input modules via RS-485 Modbus RTU

    The R4DIF08 seem to come with a pre-set slave ID of 1.

    Brand name is "eletechsup", available at https://www.eletechsup.com

    This is for the three-channel variant.
    """
    INPUT_REG_OFFSET = 40129
    INPUT_CONF_REGISTER = 40253
    SLAVE_ID_REGISTER = 40255
    BAUDRATE_REGISTER = 40256
    FACTORY_RESET_REGISTER = 40256
    FACTORY_RESET_VALUE = 5
    BROADCAST_SLAVE_ID = 0xFF # This is non-standard
    BAUDRATE_KEYS = {1200: 0, 2400: 1, 4800: 2, 9600: 3, 19200: 4}

    def __init__(self,
                 slave_id: int = 1,
                 serial_device_name: str = None,
                 baudrate: int = 9600,
                 **kwargs
                 ):
        super().__init__(slave_id, serial_device_name, baudrate, **kwargs)

    def get_input(self, input_no: int) -> bool:
        """Return the state of the specified digital input

        Args:
            input_no:   Input number, starts counting at 1

        Returns:
            True if input signal is active, False if inactive
        """
        if 1 > input_no or input_no > 8:
            raise ValueError("Input number must be between 1 and 8")
        reg_val = self.master.read_holding_registers(
            self.slave_id,
            self.INPUT_REG_OFFSET + input_no,
            1,
            dtype="raw"
        )
        return bool(reg_val[1])

    def get_inputs(self) -> tuple[bool, ...]:
        """Returns the state of the 8 digital inputs

        Returns:
            Tuple of 8 boolean flags, one for each input
        """
        reg_vals = self.master.read_holding_registers(
            self.slave_id,
            self.INPUT_REG_OFFSET + 1,
            8,
            dtype="words"
        )
        return tuple(bool(reg_val[1]) for reg_val in reg_vals)

    def set_input_level(self, active_high=False, delay_enabled=True):
        """Set input inverters, or voltage level for boolean True output

        The module only supports setting all inputs at once, so this
        applies to all eight inputs.

        There seems to be a delay necessary in order for the module to be
        re-configured and ready to answer queries after setting this register.

        This is why a 0.2 second blocking delay is activated by default.

        Warning:
            While undocumented, it is possible that the device writes directly
            to FLASH, thus frequent writes could damage the chip!

        
        Args:
            active_high:    If set to False (default), Report True for low-level input (0 V, GND).
                            If set to True, Report True for high-level input (> VCC/2).
            delay_enabled:  Enable 0.2 second delay if set to True (default)
        """
        self.master.set_holding_register(
            self.slave_id, self.INPUT_CONF_REGISTER, 0x0001 if active_high else 0x0000
        )
        if delay_enabled:
            time.sleep(0.2)


class N4AIA04(ModbusModuleABC):
    """Control N4AIA04 4-channel 0..5V / 0..10V / 0..20mA analog input modules
    (ADC) via RS-485 Modbus RTU

    The N4AIA04 seem to come with a pre-set slave ID of 1.

    Brand name is "eletechsup", available at https://www.eletechsup.com
    """
    INPUT_REG_OFFSET = 40000
    INPUT_CAL_REG_OFFSET = 40007
    SLAVE_ID_REGISTER = 40015
    BAUDRATE_REGISTER = 40016
    FACTORY_RESET_REGISTER = 40016
    FACTORY_RESET_VALUE = 5
    BROADCAST_SLAVE_ID = 0xFF # This is non-standard
    BAUDRATE_KEYS = {1200: 0, 2400: 1, 4800: 2, 9600: 3, 19200: 4}

    def __init__(self,
                 slave_id: int = 1,
                 serial_device_name: str = None,
                 baudrate: int = 9600,
                 **kwargs
                 ):
        super().__init__(slave_id, serial_device_name, baudrate, **kwargs)

    def get_voltage(self, input_no: int) -> float:
        """Read and return the value of the specified analog input voltage

        Input no. 1 is 0..5 V,
        Input no. 2 is 0..10 V

        Args:
            input_no:   Input number, can be 1 or 2.

        Returns:
            Analog input voltage read-out value in volts
        """
        if 1 > input_no or input_no > 2:
            raise ValueError("Input no. must be 1 or 2")
        reg_val, = self.master.read_holding_registers(
            self.slave_id,
            input_no + self.INPUT_REG_OFFSET
        )
        return reg_val * 0.01

    def get_current(self, input_no: int) -> float:
        """Read and return the value of the specified analog input current

        Input numbers are 3 and 4 and these are both 0..20 mA inputs.

        Args:
            input_no:   Input number, can be 3 or 4.

        Returns:
            Analog input current read-out value in mA
        """
        if 3 > input_no or input_no > 4:
            raise ValueError("Input no. must be 3 or 4")
        reg_val, = self.master.read_holding_registers(
            self.slave_id,
            input_no + self.INPUT_REG_OFFSET
        )
        return reg_val * 0.1

    def get_cal_factor(self, input_no: int) -> float:
        """Get currently set hardware calibration / correction factor for input

        A factor of 1.000 means no correction.
        
        Args:
            input_no:   Input number, valid range is 1...4

        Returns:
            Hardware calibration factor for input
        """
        if 1 > input_no or input_no > 4:
            raise ValueError("Input no. must be 1, 2, 3 or 4")
        reg_val, = self.master.read_holding_registers(
            self.slave_id,
            input_no + self.INPUT_CAL_REG_OFFSET
        )
        return reg_val * 0.001

    def set_cal_factor(self, input_no: int, cal_factor: float = 1.000):
        """Set analog calibration / correction factor for specified input

        A factor of 1.000 means no correction.
    
        This does not factor in any previously set value.
        The currently set value can be queried using get_cal_factor().

        Warning:
            While undocumented, it is possible that the device writes directly
            to FLASH, thus frequent writes could damage the chip!
        
        Args:
            input_no:   Input number, valid range is 1...4
            cal_factor: Calibration value. Valid range is 0.0 ... 65.535
        """
        if 1 > input_no or input_no > 4:
            raise ValueError("Input no. must be 1, 2, 3 or 4")
        reg_val = round(cal_factor * 1000.0)
        if 0 > reg_val or reg_val > 65535:
            raise ValueError("Valid range for cal_factor is 0.0 ... 65.535")
        self.master.set_holding_register(
            self.slave_id,
            input_no + self.INPUT_CAL_REG_OFFSET,
            reg_val
        )


class N4DAC02(ModbusModuleABC):
    """Control N4DAC02 2-channel 0..5V / 0..10V analog output modules
    (DAC) via RS-485 Modbus RTU

    The N4DAC02 seem to come with a pre-set slave ID of 1.

    Brand name is "eletechsup", available at https://www.eletechsup.com
    """
    OUTPUT_REG_OFFSET = 40000
    OUTPUT_CAL_REG_OFFSET = 40007
    SLAVE_ID_REGISTER = 40015
    BAUDRATE_REGISTER = 40016
    FACTORY_RESET_REGISTER = 40016
    FACTORY_RESET_VALUE = 5
    BROADCAST_SLAVE_ID = 0xFF # This is non-standard
    BAUDRATE_KEYS = {1200: 0, 2400: 1, 4800: 2, 9600: 3, 19200: 4}

    def __init__(self,
                 slave_id: int = 1,
                 serial_device_name: str = None,
                 baudrate: int = 9600,
                 **kwargs
                 ):
        super().__init__(slave_id, serial_device_name, baudrate, **kwargs)

    def set_voltage(self, output_no: int, voltage: float):
        """Set setpoint for the analog output voltage

        Output no. 1 is 0..5 V,
        Output no. 2 is 0..10 V

        Args:
            output_no:  Output number, can be 1 or 2.
            voltage:    Setpoint for output voltage in volts.
        """
        if 1 > output_no or output_no > 2:
            raise ValueError("Output no. must be 1 or 2")
        reg_val = round(voltage * 100.0)
        if 0 > reg_val or reg_val > 65535:
            raise ValueError("Valid range for cal_factor is 0.0 ... 65.535")
        self.master.set_holding_register(
            self.slave_id,
            output_no + self.OUTPUT_REG_OFFSET,
            reg_val
        )

    def get_cal_factor(self, output_no: int) -> float:
        """Get currently set hardware calibration / correction factor for output

        A factor of 1.000 means no correction.
        
        Args:
            output_no:   Output number, can be 1 or 2.

        Returns:
            Hardware calibration factor for output
        """
        if 1 > output_no or output_no > 2:
            raise ValueError("Output no. must be 1 or 2")
        reg_val, = self.master.read_holding_registers(
            self.slave_id,
            output_no + self.OUTPUT_CAL_REG_OFFSET
        )
        return reg_val * 0.001

    def set_cal_factor(self, output_no: int, cal_factor: float = 1.000):
        """Set analog calibration / correction factor for specified output

        A factor of 1.000 means no correction.
    
        This does not factor in any previously set value.
        The currently set value can be queried using get_cal_factor().

        Warning:
            While undocumented, it is possible that the device writes directly
            to FLASH, thus frequent writes could damage the chip!
        
        Args:
            output_no:  Output number, can be 1 or 2.
            cal_factor: Calibration value. Valid range is 0.0 ... 32.767
        """
        if 1 > output_no or output_no > 2:
            raise ValueError("Output no. must be 1 or 2")
        reg_val = round(cal_factor * 1000.0)
        if 0 > reg_val or reg_val > 32767:
            raise ValueError("Valid range for cal_factor is 0.0 ... 32.767")
        self.master.set_holding_register(
            self.slave_id,
            output_no + self.OUTPUT_CAL_REG_OFFSET,
            reg_val
        )