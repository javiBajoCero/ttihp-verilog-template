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
        tick = dut.uo_out.value.integer & 0x01
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
        tick = (dut.uo_out.value.integer >> 1) & 0x01  # uo_out[1]
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
    bits += [(byte >> i) & 1 for i in range(8)]  # Data bits (LSB first)
    bits += [1]  # Stop bit
    return bits


@cocotb.test()
async def test_uart_tx(dut):
    """Test UART TX: check if 'POLO\\n' is transmitted correctly"""

    # Start 50MHz clock
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())  # 50MHz

    # Reset
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    dut._log.info("Reset done")

    # Trigger transmission by setting ui_in[0] = 1
    dut.ui_in.value = 0b00000001
    while dut.uo_out.value[4] == 0:  # wait for tx_busy
        await RisingEdge(dut.clk)
    dut.ui_in.value = 0

    # Expected bytes: 'P', 'O', 'L', 'O', '\n'
    expected_bytes = [ord(c) for c in "POLO\n"]
    expected_bits = []
    for byte in expected_bytes:
        expected_bits += uart_encode(byte)

    received_bits = []

    for i, expected in enumerate(expected_bits):
        # Wait for a rising edge of baud_tick_tx (uo_out[1])
        while dut.uo_out.value[1] == 0:
            await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)  # Align with baud tick

        tx_bit = int(dut.uo_out.value[3])  # tx_serial
        received_bits.append(tx_bit)
        dut._log.info(f"Bit {i}: {tx_bit}")

    # Reconstruct bytes and compare
    def decode_uart(bits):
        return [
            sum(bits[i + 1 + b] << b for b in range(8))
            for i in range(0, len(bits), 10)
        ]

    received_bytes = decode_uart(received_bits)
    dut._log.info(f"Received bytes: {[chr(b) for b in received_bytes]}")

    assert received_bytes == expected_bytes, \
        f"Expected {expected_bytes}, got {received_bytes}"