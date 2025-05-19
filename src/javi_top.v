/*
 * Copyright (c) 2025 javier munoz saez
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
    input  wire       clk,      // clock (tinytapeouts clock is 50Mhz)
    input  wire       rst_n     // reset_n - low to reset
);

  // All output pins must be assigned. If not used, assign to 0.
  assign uo_out[7:1] = 0;
  assign uio_out = 0;
  assign uio_oe[7:1]  = 0;

  wire baud_tick;
  assign uio_oe[0] = 1;           //enable debug clock pin
  assign uo_out[0] = baud_tick;   //assign debug clock pin

  baud_generator baud_gen (
      .clk(clk),
      .rst_n(rst_n),
      .baud_tick(baud_tick)
  );
  
  // List all unused inputs to prevent warnings
  wire _unused = &{ena, 1'b0};

endmodule
