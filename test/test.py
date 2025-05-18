# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_baud_generator(dut):
    dut._log.info("Start test_baud_generator")

    # Start 50 MHz clock (20 ns period)
    clock = Clock(dut.clk, 20, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.ena.value = 1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1

    dut._log.info("Waiting for baud_tick...")

    # Count how many clock cycles until we get a baud_tick
    counter = 0
    while True:
        await RisingEdge(dut.clk)
        counter += 1
        if dut.baud_gen.baud_tick.value == 1:
            break

    dut._log.info(f"baud_tick occurred after {counter} clock cycles")
    
    # Assert that it happens around the right number of cycles
    # For 9600 baud from 50MHz clock, should be about 5208 cycles
    assert 5190 <= counter <= 5220, "baud_tick did not occur at expected interval"
