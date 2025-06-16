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
    wire tx_valid = 0;  // placeholder
    wire [7:0] tx_data = 8'h00;  // placeholder
    // --- Instantiate the baud generator ---
    wire baud_tick;

    baud_generator #(
        .BAUD_DIV(651)
    ) baud_gen_inst (
        .clk(clk),
        .rst_n(rst_n),
        .baud_tick(baud_tick)
    );

    uart_tx uart_tx_inst (
        .clk(clk),
        .rst_n(rst_n),
        .tx_valid(tx_valid),
        .tx_data(tx_data),
        .tx_ready(tx_ready),
        .tx_serial(tx_serial),
        .baud_tick(baud_tick)
    );

    // --- Intermediate sum wire ---
    wire [7:0] sum = ui_in + uio_in;

    // --- Connect outputs ---
    assign uo_out     = { sum[6:0], baud_tick };  // still showing sum + tick
    assign uio_out[0] = tx_serial;                // expose UART TX on uio_out[0]
    assign uio_out[7:1] = 0;

    assign uio_oe[0]  = 1;                        // actively drive uio_out[0]
    assign uio_oe[7:1] = 0;

    // Prevent unused warnings (now clk and rst_n are used)
    wire _unused = &{ena, 1'b0};

endmodule
