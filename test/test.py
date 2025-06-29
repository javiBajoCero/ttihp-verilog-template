# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, FallingEdge

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
    bits = [0]  # Start bit
    bits += [(byte >> i) & 1 for i in range(8)]
    bits += [1]  # Stop bit
    return bits

@cocotb.test()
async def test_uart_tx(dut):
    """Send 'MARCO' to RX and check if 'POLO!\\n\\r' is transmitted"""

    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())  # 50 MHz

    # Reset
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    dut._log.info("Reset done")

    # The RX line is idle high
    dut.ui_in[0].value = 1
    await ClockCycles(dut.clk, 100)

    # Send "MARCO" to trigger response
    for ch in "MARCO":
        bits = uart_encode(ord(ch))
        for bit in bits:
            dut.ui_in[0].value = bit
            await ClockCycles(dut.clk, 651)  # wait 1 baud @ 9600*8 (from your top)
        dut._log.info(f"Sent char: {ch}")

    # Wait for TX to start (uo_out[0] = tx line)
    received_bits = []
    collecting = False

    while len(received_bits) < 90:  # Expecting 9 bytes * 10 bits = 90 bits
        await RisingEdge(dut.clk)
        if dut.uo_out.value[1]:  # baud_tick_tx
            tx_bit = int(dut.uo_out.value[0])  # tx_serial
            received_bits.append(tx_bit)
            dut._log.info(f"Bit {len(received_bits) - 1}: {tx_bit}")

    # Decode bytes
    def decode_uart(bits):
        return [
            sum(bits[i + 1 + b] << b for b in range(8))
            for i in range(0, len(bits), 10)
        ]

    received_bytes = decode_uart(received_bits)
    dut._log.info(f"Received bytes: {[chr(b) for b in received_bytes]}")

    # Match against full expected string
    expected_bytes = [ord(c) for c in "\n\rPOLO!\n\r"]
    assert received_bytes == expected_bytes, f"Expected {expected_bytes}, got {received_bytes}"