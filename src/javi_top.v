`timescale 1ns/1ps
/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_javibajocero_top (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

    // --- Internal signals ---
    wire tx_serial;
    wire tx_ready;
    wire baud_tick_tx;
    wire baud_tick_rx;

    // Static transmit for testing (tx_valid high one cycle, tx_data = 'A')
    wire       tx_valid = 1'b0;       // Placeholder: replace with actual logic or testbench
    wire [7:0] tx_data  = 8'h00;      // Placeholder: 'A' = 8'h41 for real TX test

    // TX baud generator (9600 baud)
    baud_generator #(
        .BAUD_DIV(5208)//50000000/9600
    ) baud_gen_tx (
        .clk(clk),
        .rst_n(rst_n),
        .baud_tick(baud_tick_tx)
    );

    // RX baud generator (oversampled 8x)
    baud_generator #(
        .BAUD_DIV(651)//50000000/9600*8
    ) baud_gen_rx (
        .clk(clk),
        .rst_n(rst_n),
        .baud_tick(baud_tick_rx)
    );

    uart_tx uart_tx_inst (
        .clk(clk),
        .rst_n(rst_n),
        .tx_valid(tx_valid),
        .tx_data(tx_data),
        .tx_ready(tx_ready),
        .tx_serial(tx_serial),
        .baud_tick(baud_tick_tx)
    );

    // --- Connect inputs ---
    wire [7:0] tx_data = ui_in;

    // --- Connect outputs ---
    assign uo_out[0] = baud_tick_rx;
    assign uo_out[1] = baud_tick_tx;
    assign uo_out[2] = tx_ready;
    assign uo_out[3] = tx_serial; //UART serial output

    // --- Connect bidi ---
    assign uio_oe[7:0]   = 8'b0; //all inputs

    // Prevent unused warnings
    wire _unused = &{ena, 1'b0};

endmodule
