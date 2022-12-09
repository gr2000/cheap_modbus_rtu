def crc16(data: bytes, poly: int = 0xA001) -> bytes:
    """CRC-16 MODBUS HASHING ALGORITHM
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (
                (crc >> 1) ^ poly
                if (crc & 0x0001)
                else crc >> 1
            )
    return crc.to_bytes(2, "little")
