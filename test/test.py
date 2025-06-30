# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0


import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, FallingEdge
from cocotb.utils import get_sim_time

@cocotb.test()
async def test_baud_tick(dut):
    dut._log.info(f"Simulating with BAUD_DIV = 651 (expected tick every 13 us at 50 MHz)")

    # Correct clock for @ 50 MHz
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())

    # Reset
    dut.ena.value = 1
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    dut._log.info("Reset released")

    # Observe uo_out[0]
    baud_tick_count = 0
    prev = 0
    max_cycles = 10_000  # Timeout after 10k cycles to avoid infinite loop

    for i in range(max_cycles):
        await RisingEdge(dut.clk)
        tick = (dut.uo_out.value.integer >> 1) & 0x01  # uo_out[1]
        if tick and not prev:
            baud_tick_count += 1
            dut._log.info(f"Tick {baud_tick_count} seen at cycle {i}")
            if baud_tick_count >= 10:
                break
        prev = tick

    assert baud_tick_count >= 10, f"Expected 10 baud ticks, got {baud_tick_count}"

@cocotb.test()
async def test_baud_tick_tx(dut):
    """Test baud_tick_tx (BAUD_DIV = 5208 @ 50 MHz) on uo_out[1]"""
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())  # 50 MHz

    dut._log.info("Testing baud_tick_tx (BAUD_DIV = 5208, ~9600 baud) on uo_out[1]")

    # Reset
    dut.ena.value = 1
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    dut._log.info("Reset released")

    # Observe baud_tick_tx from uo_out[1]
    baud_tick_count = 0
    prev = 0
    max_cycles = 60_000  # Allow for ~10 full baud ticks (5208 * 10)

    for i in range(max_cycles):
        await RisingEdge(dut.clk)
        tick = (dut.uo_out.value.integer >> 2) & 0x01  # uo_out[2]
        if tick and not prev:
            baud_tick_count += 1
            dut._log.info(f"TX Tick {baud_tick_count} seen at cycle {i}")
            if baud_tick_count >= 10:
                break
        prev = tick

    assert baud_tick_count >= 10, f"Expected 10 TX baud ticks, got {baud_tick_count}"
    



def uart_encode(byte):
    """Returns UART frame as a list of bits: start + data (LSB first) + stop"""
    return [0] + [(byte >> i) & 1 for i in range(8)] + [1]


@cocotb.test()
async def test_uart_tx(dut):
    """Send 'MARCO' to RX and check if '\\n\\rPOLO!\\n\\r' is transmitted"""

    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())  # 50 MHz

    # Reset
    dut.rst_n.value = 0
    dut.ui_in.value = 0xFF  # All lines high (idle)
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    dut._log.info("Reset released")

    # Keep RX line idle high before transmission
    dut.ui_in[0].value = 1
    await ClockCycles(dut.clk, 100)

    # Constants for timing
    oversample_tick_cycles = 651
    bits_per_uart_bit = 8
    bit_duration = oversample_tick_cycles * bits_per_uart_bit

    # Send "MARCO" to trigger UART TX response
    for ch in "MARCO":
        bits = uart_encode(ord(ch))

        for bit in bits:
            dut.ui_in[0].value = bit
            await ClockCycles(dut.clk, bit_duration)

        # Hold line idle for stop bit and inter-byte delay (2 bit times)
        dut.ui_in[0].value = 1
        await ClockCycles(dut.clk, bit_duration * 2)

        dut._log.info(f"Sent char: {ch}")

    # Wait for trigger_send signal (uo_out[3])
    dut._log.info("Sent all bytes, checking for trigger and RX activity")
    for _ in range(10000):
        await RisingEdge(dut.clk)
        if dut.uo_out.value[3]:  # trigger_send
            dut._log.info("TRIGGER MATCHED! TX should start soon.")
            break
    else:
        assert False, "Trigger match never happened"

    # Wait for TX to start (uo_out[4] = tx_busy)
    timeout = 200000
    cycles_waited = 0
    while cycles_waited < timeout:
        await RisingEdge(dut.clk)
        if (dut.uo_out.value.integer >> 4) & 1:  # tx_busy
            dut._log.info("TX started (tx_busy is high)")
            break
        cycles_waited += 1
    else:
        assert False, "TX never started (tx_busy never went high)"

    # Wait for first falling edge on tx line (start bit)
    await RisingEdge(dut.clk)
    while ((dut.uo_out.value.integer >> 0) & 1) == 1:
        await RisingEdge(dut.clk)

    # Now capture bits on baud_tick_tx edges
    expected_bits = 9 * 10  # 9 bytes, 10 bits each (start+8data+stop)
    received_bits = []
    received_timestamps = []
    old_flank=1;
    
    while len(received_bits) < expected_bits:
        await RisingEdge(dut.clk)
        old_flank=1;
        if ((dut.uo_out.value.integer >> 0) & 1 ) != old_flank:  # detect every initial flank
            bit = (dut.uo_out.value.integer >> 0) & 1
            old_flank=bit;
            await ClockCycles(dut.clk, 100)
            for counting in range(8+1):
                await ClockCycles(dut.clk, 5208)
                bit = (dut.uo_out.value.integer >> 0) & 1
                timestamp = get_sim_time(units="ns")
                received_bits.append(bit)
                received_timestamps.append(timestamp)
                dut._log.info(f"TX Bit {len(received_bits) - 1}: {bit} at {timestamp} ns")
            

    # Decode UART frames as before
    def decode_uart(bits):
        bytes_out = []
        for i in range(0, len(bits), 10):
            if i + 9 >= len(bits):
                break  # incomplete frame
            start_bit = bits[i]
            stop_bit = bits[i + 9]
            if start_bit != 0 or stop_bit != 1:
                dut._log.warning(f"Frame {i//10} framing error: start={start_bit}, stop={stop_bit}")
                continue
            byte_val = 0
            for b in range(8):
                byte_val |= bits[i + 1 + b] << b
            bytes_out.append(byte_val)
        return bytes_out


    received_bytes = decode_uart(received_bits)
    received_chars = [chr(b) for b in received_bytes]
    dut._log.info(f"Received bytes: {received_chars}")

    expected_bytes = [ord(c) for c in "\n\rPOLO!\n\r"]
    assert received_bytes == expected_bytes, f"Expected {expected_bytes}, got {received_bytes}"
