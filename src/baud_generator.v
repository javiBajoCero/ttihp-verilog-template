/*
 * Copyright (c) 2025 javier munoz saez
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module baud_generator (
    input  wire clk,        // 50 MHz input clock
    input  wire rst_n,      // Active-low reset
    output reg  baud_tick   // Output pulse at desired baud rate
);

    parameter BAUD_DIV = 5208;  // 50_000_000 / 9600

    reg [12:0] counter;  // Enough bits to hold values up to 5208

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter   <= 0;
            baud_tick <= 0;
        end else begin
            if (counter == BAUD_DIV - 1) begin
                counter   <= 0;
                baud_tick <= 1;
            end else begin
                counter   <= counter + 1;
                baud_tick <= 0;
            end
        end
    end

endmodule
