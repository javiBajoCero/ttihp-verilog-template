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
    return [0] + [(byte >> i) & 1 for i in range(8)] + [1]


@cocotb.test()
async def test_uart_tx(dut):
    """Send 'MARCO' to RX and check if '\\n\\rPOLO!\\n\\r' is transmitted"""

    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())  # 50 MHz

    # Reset
    dut.rst_n.value = 0
    dut.ui_in.value = 0xFF  # All lines high
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    dut._log.info("Reset released")

    # Keep RX line idle high before transmission
    dut.ui_in[0].value = 1
    await ClockCycles(dut.clk, 100)

    # Send "MARCO" to trigger UART TX response
    for ch in "MARCO":
        bits = uart_encode(ord(ch))

        bit_period = 651 * 8  # Full UART bit period in clock cycles

        for bit in bits:
            dut.ui_in[0].value = bit
            # Wait a bit before the middle of the bit period
            await ClockCycles(dut.clk, bit_period // 2)
            # Wait for the rising edge of baud_tick_rx (oversample tick)
            await RisingEdge(dut.clk)
            while not dut.uo_out.value[1]:  # wait for baud_tick_rx
                await RisingEdge(dut.clk)

        # After sending each character, hold idle for full frame + margin to allow receiver processing
        dut.ui_in[0].value = 1
        await ClockCycles(dut.clk, 651 * 12)

        dut._log.info(f"Sent char: {ch}")
        # Log reception status
        dut._log.info(f"byte_received: {int(dut.rx_valid.value)}")
        dut._log.info(f"data: {int(dut.rx_data.value)}")

    # Return line to idle and wait longer for stop bit + idle
    dut.ui_in[0].value = 1
    await ClockCycles(dut.clk, 651 * 12)

    # Wait until TX trigger is detected (uo_out[3])
    dut._log.info("Sent all bytes, checking for trigger and RX activity")
    for _ in range(10000):
        await RisingEdge(dut.clk)
        if dut.uo_out.value[3]:  # trigger_send
            dut._log.info("TRIGGER MATCHED! TX should start soon.")
            break
    else:
        assert False, "Trigger match never happened"

    # Wait for TX to start (uo_out[4] = tx_busy)
    for _ in range(10000):
        await RisingEdge(dut.clk)
        if dut.uo_out.value[4]:  # tx_busy
            dut._log.info("TX started (tx_busy is high)")
            break
    else:
        assert False, "TX never started (tx_busy never went high)"

    # Capture TX while tx_busy is high
    received_bits = []
    while dut.uo_out.value[4]:  # while tx_busy
        await RisingEdge(dut.clk)
        if dut.uo_out.value[1]:  # baud_tick_tx
            tx_bit = int(dut.uo_out.value[0])
            received_bits.append(tx_bit)
            dut._log.info(f"TX Bit {len(received_bits)-1}: {tx_bit}")

    # Decode UART frames
    def decode_uart(bits):
        return [
            sum(bits[i + 1 + b] << b for b in range(8))
            for i in range(0, len(bits), 10)
        ]

    received_bytes = decode_uart(received_bits)
    received_chars = [chr(b) for b in received_bytes]
    dut._log.info(f"Received bytes: {received_chars}")

    # Expected response from TX
    expected_bytes = [ord(c) for c in "\n\rPOLO!\n\r"]
    assert received_bytes == expected_bytes, f"Expected {expected_bytes}, got {received_bytes}"

