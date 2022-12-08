import os
from serial import Serial
from .crc16_modbus import crc16

class ModbusRtuMaster():
    """Lightweight Modbus RTU master

    2022-12-07 Ulrich Lukas
    """
    def __init__(self,
                 device_name: str = None,
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
        self.serial_device = Serial(device_name, timeout=timeout, **kwargs)


    def read_discrete_input_registers(self,
                                      slave_id: int,
                                      start_register_no: int = 10001,
                                      n_registers: int = 8
                                      ) -> tuple[bool, ...]:
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


    def read_analog_holding_registers(self,
                                      slave_id: int,
                                      start_register_no: int = 40001,
                                      n_registers: int = 1
                                      ) -> tuple[int, ...]:
        # Frame starts with modbus address ("slave_id") and function code
        frame_out = bytes((slave_id, 0x03))
        # Discrete input register numbers have a register offset of 10001 which is subtracted.
        frame_out += int.to_bytes(start_register_no-40001, 2, "big")
        # Followed by the number of registers to read
        frame_out += int.to_bytes(n_registers, 2, "big")
        # Payload is grouped into bytes
        n_payload_bytes = n_registers * 2
        # We expect five bytes plus number of payload bytes
        frame_in = self._add_crc_transmit(frame_out, 5 + n_payload_bytes)
        payload_words = (frame_in[i:i+2] for i in range(3, 3+n_payload_bytes, 2))
        return tuple(int.from_bytes(word, "big") for word in payload_words)
    
    
    def set_discrete_output_register(self,
                                     slave_id: int,
                                     register_no: int,
                                     active: bool
                                     ):
        # Frame starts with modbus address ("slave_id") and function code
        frame_out = bytes((slave_id, 0x05))
        # Discrete output register numbers have a register offset of 1 which is subtracted.
        frame_out += int.to_bytes(register_no-1, 2, "big")
        # Followed by the data value which is 0xFF00 if coil is to be set and 0x0000 otherwise
        frame_out += b"\xFF\x00" if active else b"\x00\x00"
        self._add_crc_transmit(frame_out, 8)


    def set_analog_holding_register(self,
                                    slave_id: int,
                                    register_no: int = 40001,
                                    value: int = 0x0000
                                    ):
        # Frame starts with modbus address ("slave_id") and function code
        frame_out = bytes((slave_id, 0x06))
        # Analog holding register numbers have a register offset of 40001 which is subtracted.
        frame_out += int.to_bytes(register_no-40001, 2, "big")
        # Append data
        frame_out += int.to_bytes(value, 2, "big")
        self._add_crc_transmit(frame_out, 8)


    def set_analog_holding_registers(self,
                                     slave_id: int,
                                     start_register_no: int,
                                     values: tuple[int, ...],
                                     expect_echo_response: bool = False
                                     ):
        # Frame starts with modbus address ("slave_id") and function code
        frame_out = bytes((slave_id, 0x10))
        # Analog holding register numbers have a register offset of 40001 which is subtracted.
        frame_out += int.to_bytes(start_register_no-40001, 2, "big")
        # Followed by the number of registers to write
        n_registers = len(values)
        frame_out += int.to_bytes(n_registers, 2, "big")
        # Add (redundant information..) the number of bytes to follow
        frame_out += int.to_bytes(n_registers*2, 1, "big")
        # Append data
        for value in values:
            frame_out += int.to_bytes(value, 2, "big")
        # According to the standard, funciton code 16 should return 8 bytes,
        # omitting the originally sent values and number of bytes.
        # Some hardware devices however return an echo response with as many
        # bytes as were sent out originally.
        if expect_echo_response:
            self._add_crc_transmit(frame_out, 2+len(frame_out))
        else:
            self._add_crc_transmit(frame_out, 8)


    def _add_crc_transmit(self, frame_out: bytes, length_expected: int) -> bytes:
        # Append CRC
        frame_out += crc16(frame_out)
        # Discard unrelated data which might be in the read buffer
        self.serial_device.reset_input_buffer()
        self.serial_device.write(frame_out)
        # We expect and return the bytes read from the bus.
        frame_in = self.serial_device.read(length_expected)
        # Check length
        if len(frame_in) < length_expected:
            raise IOError(
                "Not enough modbus data received, maybe timeout issue..\n"
                f'Sent: "{frame_out.hex(" ")}"  Received: "{frame_in.hex(" ")}"'
            )
        # Check CRC
        if crc16(frame_in[:-2]) != frame_in[-2:]:
            raise IOError(
                "Read error: CRC mismatch..\n"
                f'Sent: "{frame_out.hex(" ")}"  Received: "{frame_in.hex(" ")}"'
            )
        if self.debug_active:
            print(f'Sent: "{frame_out.hex(" ")}"  Received: "{frame_in.hex(" ")}"')
        return frame_in
