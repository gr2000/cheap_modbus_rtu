import os
from typing import Union
from serial import Serial
from .crc16_modbus import crc16_lut

class ModbusException(Exception):
    def __init__(self, msg, exception_code=None):
        super().__init__(msg)
        self.exception_code = exception_code


class ModbusRtuMaster():
    """Lightweight Modbus RTU master

    2022-12-07 Ulrich Lukas
    """
    def __init__(self,
                 device_name: str = None,
                 baudrate: int = 9600,
                 timeout=1,
                 debug_active=False,
                 **kwargs
                 ):
        self.debug_active = debug_active
        if device_name is None:
            if os.name == "posix":
                device_name = "/dev/ttyUSB0"
            elif os.name == "nt":
                device_name = "COM1"
        self.serial_device = Serial(device_name, baudrate, timeout=timeout, **kwargs)


    def read_discrete_input_registers(self,
                                      slave_id: int,
                                      start_register_no: int = 10001,
                                      n_registers: int = 8
                                      ) -> tuple[bool, ...]:
        """Read one or more discrete (on/off) input registers ("coils")

        Args:
            slave_id:           Modbus Slave ID
            start_register_no:  First register number to read
            n_registers:        Number of registers to read

        Returns:
            Tuple of register values as boolean flag values
        """
        # Frame starts with modbus address ("slave_id") and function code
        frame_out = bytes((slave_id, 0x02))
        # Discrete input register numbers have a register offset of 10001 which is subtracted.
        frame_out += int.to_bytes(start_register_no-10001, 2, "big")
        # Followed by the number of digital inputs to read
        frame_out += int.to_bytes(n_registers, 2, "big")
        # Payload is grouped into bytes
        n_payload_bytes = (n_registers+7)//8
        # We expect five bytes plus number of payload bytes
        frame_in = self._add_crc_transmit(frame_out, 5 + n_payload_bytes)
        out_tuple = ()
        remaining_bits = n_registers
        for payload_byte in frame_in[3:-2]:
            out_tuple += tuple(
                bool(payload_byte & 0b1<<i)
                for i in range(min(8, remaining_bits))
            )
            remaining_bits -= 8
        return out_tuple


    def read_holding_registers(self,
                               slave_id: int,
                               start_register_no: int = 40001,
                               n_registers: int = 1,
                               dtype: str = "uint16"
# Since Python 3.10 typing can be:
#                               ) -> tuple[int, ...] | tuple[bytes, ...] | bytes:
                               ) -> Union[tuple[int, ...], tuple[bytes, ...], bytes]:
        """Read one or more value holding registers

        Args:
            slave_id:           Modbus Slave ID
            start_register_no:  First register number to read
            n_registers:        Number of registers to read
            dtype:              Configures format of return value, see below

        Returns:
            Tuple of register values interpreted as 16-bit integers
            if dtype == "uint16" (default)
        Returns:
            Tuple of register values interpreted as 16-bit signed integers
            if dtype == "int16"
        Returns:
            Tuple of register values each in a 16-bit bytes object
            if dtype == "words"
        Returns:
            bytes of register values if dtype == "raw"
        """
        # Frame starts with modbus address ("slave_id") and function code
        frame_out = bytes((slave_id, 0x03))
        # Holding register numbers have a register offset of 40001 which is subtracted.
        frame_out += int.to_bytes(start_register_no-40001, 2, "big")
        # Followed by the number of registers to read
        frame_out += int.to_bytes(n_registers, 2, "big")
        # Payload is grouped into bytes
        n_payload_bytes = n_registers * 2
        # We expect five bytes plus number of payload bytes
        frame_in = self._add_crc_transmit(frame_out, 5 + n_payload_bytes)
        if dtype == "raw":
            return frame_in[3:3+n_payload_bytes]
        elif dtype == "uint16":
            payload_words = (frame_in[i:i+2] for i in range(3, 3+n_payload_bytes, 2))
            return tuple(int.from_bytes(word, "big") for word in payload_words)
        elif dtype == "int16":
            payload_words = (frame_in[i:i+2] for i in range(3, 3+n_payload_bytes, 2))
            return tuple(int.from_bytes(word, "big", True) for word in payload_words)
        elif dtype == "words":
            return tuple(frame_in[i:i+2] for i in range(3, 3+n_payload_bytes, 2))


    def read_input_registers(self,
                             slave_id: int,
                             start_register_no: int = 30001,
                             n_registers: int = 1,
                             dtype: str = "uint16"
# Since Python 3.10 typing can be:
#                             ) -> tuple[int, ...] | tuple[bytes, ...] | bytes:
                             ) -> Union[tuple[int, ...], tuple[bytes, ...], bytes]:
        """Read one or more input read-out registers

        Args:
            slave_id:           Modbus Slave ID
            start_register_no:  First register number to read
            n_registers:        Number of registers to read
            dtype:              Configures format of return value, see below

        Returns:
            Tuple of register values interpreted as 16-bit unsigned integers
            if dtype == "uint16" (default)
        Returns:
            Tuple of register values interpreted as 16-bit signed integers
            if dtype == "int16"
        Returns:
            Tuple of register values each in a 16-bit bytes object
            if dtype == "words"
        Returns:
            bytes of register values if dtype == "raw"
        """
        # Frame starts with modbus address ("slave_id") and function code
        frame_out = bytes((slave_id, 0x04))
        # Input register numbers have a register offset of 30001 which is subtracted.
        frame_out += int.to_bytes(start_register_no-30001, 2, "big")
        # Followed by the number of registers to read
        frame_out += int.to_bytes(n_registers, 2, "big")
        # Payload is grouped into bytes
        n_payload_bytes = n_registers * 2
        # We expect five bytes plus number of payload bytes
        frame_in = self._add_crc_transmit(frame_out, 5 + n_payload_bytes)
        if dtype == "raw":
            return frame_in[3:3+n_payload_bytes]
        elif dtype == "uint16":
            payload_words = (frame_in[i:i+2] for i in range(3, 3+n_payload_bytes, 2))
            return tuple(int.from_bytes(word, "big") for word in payload_words)
        elif dtype == "int16":
            payload_words = (frame_in[i:i+2] for i in range(3, 3+n_payload_bytes, 2))
            return tuple(int.from_bytes(word, "big", True) for word in payload_words)
        elif dtype == "words":
            return tuple(frame_in[i:i+2] for i in range(3, 3+n_payload_bytes, 2))


    def set_discrete_output_register(self,
                                     slave_id: int,
                                     register_no: int,
                                     active: bool
                                     ):
        """Set one discrete (on/off) output register ("coil")

        Args:
            slave_id:       Modbus Slave ID
            register_no:    Register number to set
            active:         Set output enabled if active == True,
                            otherwise disable output
        """
        # Frame starts with modbus address ("slave_id") and function code
        frame_out = bytes((slave_id, 0x05))
        # Discrete output register numbers have a register offset of 1 which is subtracted.
        frame_out += int.to_bytes(register_no-1, 2, "big")
        # Followed by the data value which is 0xFF00 if coil is to be set and 0x0000 otherwise
        frame_out += b"\xFF\x00" if active else b"\x00\x00"
        self._add_crc_transmit(frame_out, 8)


    def set_holding_register(self,
                             slave_id: int,
                             register_no: int = 40001,
                             value: int = 0x0000
                             ):
        """Set one (analog or general-purpose) 16-bit value holding register

        Args:
            slave_id:       Modbus Slave ID
            register_no:    Register number to set
            value:          Integer value to be written into 16-bit big-endian
                            register.
        """
        # Frame starts with modbus address ("slave_id") and function code
        frame_out = bytes((slave_id, 0x06))
        # Holding register numbers have a register offset of 40001 which is subtracted.
        frame_out += int.to_bytes(register_no-40001, 2, "big")
        # Append data
        frame_out += int.to_bytes(value, 2, "big", signed=value<0)
        self._add_crc_transmit(frame_out, 8)


    def set_holding_registers(self,
                              slave_id: int,
                              start_register_no: int,
                              values: tuple[int, ...],
                              expect_echo_response: bool = False
                              ):
        """Set one or more (analog or general-purpose) 16-bit value holding registers

        Args:
            slave_id:           Modbus Slave ID
            start_register_no:  First register number to read
            values:             Tuple of integer values to write into registers
            expect_echo_response: If set to True, expect a device response which
                                  is a copy of the original query, which is not
                                  standard Modbus behaviour.
        """
        # Frame starts with modbus address ("slave_id") and function code
        frame_out = bytes((slave_id, 0x10))
        # Holding register numbers have a register offset of 40001 which is subtracted.
        frame_out += int.to_bytes(start_register_no-40001, 2, "big")
        # Followed by the number of registers to write
        n_registers = len(values)
        frame_out += int.to_bytes(n_registers, 2, "big")
        # Add (redundant information..) the number of bytes to follow
        frame_out += int.to_bytes(n_registers*2, 1, "big")
        # Append data
        for value in values:
            frame_out += int.to_bytes(value, 2, "big", signed=value<0)
        # According to the standard, funciton code 16 should return 8 bytes,
        # omitting the originally sent values and number of bytes.
        # Some hardware devices however return an echo response with as many
        # bytes as were sent out originally.
        if expect_echo_response:
            self._add_crc_transmit(frame_out, 2+len(frame_out))
        else:
            self._add_crc_transmit(frame_out, 8)


    def _add_crc_transmit(self, frame_out: bytes, length_expected: int) -> bytes:
        exception_code = None
        # Append CRC
        frame_out += crc16_lut(frame_out)
        # Discard unrelated data which might be in the read buffer
        self.serial_device.reset_input_buffer()
        self.serial_device.write(frame_out)
        # We expect and return the bytes read from the bus.
        # Read first five bytes and check if this is an exception
        frame_in = self.serial_device.read(5)
        if len(frame_in) == 5:
            if frame_in[1] & 0x80:
                length_expected = 5
                exception_code = frame_in[2]
            else:
                frame_in += self.serial_device.read(length_expected - 5)
        # Check length again
        if len(frame_in) < length_expected:
            raise ModbusException(
                "Not enough modbus data received, maybe timeout issue.\n"
                "Check communication settings, wire connection and polarity..\n"
                f'Sent: "{frame_out.hex(" ")}"  Received: "{frame_in.hex(" ")}"'
            )
        # Check CRC
        if crc16_lut(frame_in[:-2]) != frame_in[-2:]:
            raise ModbusException(
                "Read error: CRC mismatch..\n"
                f'Sent: "{frame_out.hex(" ")}"  Received: "{frame_in.hex(" ")}"'
            )
        if exception_code is not None:
            raise ModbusException(
                f"Received Modbus exception code: 0x{exception_code:x}",
                exception_code
            )
        if self.debug_active:
            print(f'Sent: "{frame_out.hex(" ")}"  Received: "{frame_in.hex(" ")}"')
        return frame_in
