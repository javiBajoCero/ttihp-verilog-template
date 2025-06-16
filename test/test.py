# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, FallingEdge


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Test project behavior")

    # Set the input values you want to test
    dut.ui_in.value = 20
    dut.uio_in.value = 30

    # Wait for one clock cycle to see the output values
    await ClockCycles(dut.clk, 1)

    # The following assersion is just an example of how to check the output values.
    # Change it to match the actual expected output of your module:
    # Extract sum from bits [7:1]
    actual_sum = dut.uo_out.value.integer >> 1
    assert actual_sum == 50, f"Expected sum 50, got {actual_sum}"

    # Keep testing the module by changing the input values, waiting for
    # one or more clock cycles, and asserting the expected output values.


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
async def test_uart_tx(dut):
    dut._log.info(f"Send a byte and verify tx_serial waveform using baud_tick (via uio_out[0])")
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())  # 50 MHz clock

    # Reset
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1

    # Prepare data
    byte_to_send = 0x41  # 'A' = 0b01000001
    expected_bits = [0]                          # Start bit
    expected_bits += [int(b) for b in f"{byte_to_send:08b}"[::-1]]  # Data bits LSB first
    expected_bits += [1]                         # Stop bit

    dut._log.info(f"Sending byte: 0x{byte_to_send:02X} ({chr(byte_to_send)})")

    # Wait until tx_ready is high (uo_out[1])
    while not dut.uo_out.value[1]:
        await RisingEdge(dut.clk)

    # Set tx_data and pulse tx_valid (using ui_in and/or uio_in if needed)
    # You must externally drive tx_data and tx_valid via UI pins — not shown in this example

    dut._log.warning("tx_valid and tx_data are not directly driven in this test; assuming external drive")

    # Wait a few cycles to let transmission begin
    await ClockCycles(dut.clk, 10)

    # Capture serial output over time by sampling uio_out[0] at baud rate intervals
    captured_bits = []

    for i in range(len(expected_bits)):
        await ClockCycles(dut.clk, 5208)  # wait ~1 baud period (50MHz / 9600)
        serial_bit = int(dut.uio_out.value[0])
        captured_bits.append(serial_bit)
        dut._log.info(f"Bit {i}: {serial_bit}")

    assert captured_bits == expected_bits, f"Expected {expected_bits}, got {captured_bits}"

