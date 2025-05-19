# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


@cocotb.test()
async def test_tt_um_javibajocero_top(dut):
    dut._log.info("Start test_baud_generator")

    # Start 50 MHz clock (20 ns period)
    clock = Clock(dut.clk, 20, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.ena.value = 1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1

    dut._log.info("Waiting for baud_tick on uo_out[0]...")

    counter = 0
    prev = dut.uo_out.value[0].integer  # Read the LSB

    while True:
        await RisingEdge(dut.clk)
        counter += 1
        curr = dut.uo_out.value[0].integer
        if prev == 0 and curr == 1:
            break
        prev = curr

    dut._log.info(f"baud_tick occurred after {counter} clock cycles")

    # For 9600 baud with 50 MHz clock, expect around 5208 cycles
    assert 5190 <= counter <= 5220, "baud_tick did not occur at expected interval"
