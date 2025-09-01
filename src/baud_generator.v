`timescale 1ns / 1ps
`default_nettype none
//////////////////////////////////////////////////////////////////////////////////
// Company: DAKKA POWER ELECTRONICS S.L
// Engineer: Javier MS
// 
// Create Date: 06/16/2025 02:40:30 PM
// Module Name: baud_generator
// Target Devices: spartan7 fpga and tiny tapeout ASIC
// Tool Versions: 
// Description: BAUD_DIV is jsut a simple prescaler for clk signal
//              as long as it fits in the counter register it will scale down clk and output to baud_tick
// 
// Dependencies: none
// 
// Revision 0.01 - File Created
// Additional Comments: not really
// 
//////////////////////////////////////////////////////////////////////////////////


module baud_generator(
    input wire clk,
    input wire rst_n,
    output reg baud_tick
    );
    parameter BAUD_DIV = 1250;  // (12_000_000) / 9600

    reg [12:0] counter;  // Enough bits to hold values up to 65535
    
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
