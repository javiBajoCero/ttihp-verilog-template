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
    

@cocotb.test()
async def test_uart_tx(dut):
    """Send a UART byte (via ui_in) and verify tx_serial on uo_out[3]"""

    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())  # 50 MHz

    # Reset
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    dut._log.info("Reset released")

    # UART data to transmit
    byte_to_send = 0x41  # 'A'
    bits_to_send = [int(b) for b in f"{byte_to_send:08b}"[::-1]]  # LSB first
    dut.ui_in.value = byte_to_send

    dut._log.info(f"Sending UART frame: {bits_to_send}")

    # Wait for tx_ready = 1 (uo_out[2])
    while not int(dut.uo_out.value[2]):
        await RisingEdge(dut.clk)

    # Capture bits from tx_serial (uo_out[3]) on each baud tick
    received = []
    full_framestartstop=[0]+ bits_to_send + [1]
    for i in range(len(full_framestartstop)):#start + frame + stop
        # Wait for baud_tick_tx
        while not int(dut.uo_out.value[1]):
            await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        bit = int(dut.uo_out.value[3])
        received.append(bit)
        dut._log.info(f"Captured bit {i}: {bit}")

    assert received == full_framestartstop, f"Expected {full_framestartstop}, got {received}"
