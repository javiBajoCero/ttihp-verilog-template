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

    // --- Instantiate the baud generator ---
    wire baud_tick;

    baud_generator #(
        .BAUD_DIV(1250)
    ) baud_gen_inst (
        .clk(clk),
        .rst_n(rst_n),
        .baud_tick(baud_tick)
    );
    
    // --- Connect outputs ---
    // Show sum of ui_in and uio_in on bits [7:1]
    // Show baud_tick on bit [0]
    assign uo_out  = { (ui_in + uio_in)[6:0], baud_tick };
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    // Prevent unused warnings (now clk and rst_n are used)
    wire _unused = &{ena, 1'b0};

endmodule
