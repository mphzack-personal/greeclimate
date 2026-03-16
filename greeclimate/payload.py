
import base64
import json
import re

def generate_payload(power: bool, temperature: int, client_id: str) -> dict:
    """Generate a complete payload dict for device control.
    
    Args:
        power: True to turn on, False to turn off
        temperature: Temperature value as integer (e.g., 36 for 36 degrees)
        client_id: Client ID string (digits only, trailing non-digits will be removed)
    
    Returns:
        Dict with the complete payload (will be JSON-serialized by cipher)
    """
    # Remove trailing non-digit characters from client_id
    clean_client_id = re.sub(r'\D+$', '', client_id)
    
    # Generate encoded values
    hex6a = encode_protobuf_string(clean_client_id)
    hex01 = encode_command(power, temperature)
    pow_value = 1 if power else 0
    
    # Build payload - return dict, not JSON string (cipher handles serialization)
    payload = {
        "t": "binCmd",
        "hex01": hex01,
        "hex6A": hex6a,
        "fragment": [[1, 4, 2, pow_value]]
    }
    
    return payload


def encode_command(power: bool, temperature: int) -> str:
    """Generate a base64 encoded command string for power and temperature control.
    
    Args:
        power: True to turn on, False to turn off
        temperature: Temperature value as integer (e.g., 36 for 36 degrees)
    
    Returns:
        Base64 encoded string of the command bytes
    """
    # Fixed bytes: 7e 7e 0e 01 00 00 01 XX 12 YY 18 14 32 00 00 00 00 00
    # XX = 0x00 if power = False, 0x02 if power = True
    # YY = temperature value
    xx = 0x02 if power else 0x00
    yy = temperature
    
    packet = bytes([
        0x7e, 0x7e, 0x0e, 0x01, 0x00, 0x00, 0x01,
        xx,
        0x12,
        yy,
        0x18, 0x14, 0x32, 0x00, 0x00, 0x00, 0x00
    ])
    
    return base64.b64encode(packet).decode('utf-8')


def encode_protobuf_string(ascii_id):
    # 1. Convert the string into raw ASCII bytes
    payload_bytes = ascii_id.encode('ascii')
    
    # 2. Construct the packet: \x7e\x7e\x6a + payload + \x00
    full_packet = b'\x7e\x7e\x13\x6a' + payload_bytes + b'\x00'
    
    # 3. Base64 Encode
    return base64.b64encode(full_packet).decode('utf-8')




