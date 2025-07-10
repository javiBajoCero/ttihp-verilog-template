`timescale 1ns / 1ps
`default_nettype none
//////////////////////////////////////////////////////////////////////////////////
// Company: DAKKA POWER ELECTRONICS S.L
// Engineer: Javier MS
// 
// Create Date: 06/30/2025 12:24:27 AM
// Module Name: buffer_comparator
// Target Devices: spartan7 fpga and tiny tapeout ASIC
// Tool Versions: 
// Description: when received a new_byte signal, the comparator stores the_byte in a fifo buffer
//              then checks if the buffer matches the harcoded message 'MARCO', if the buffer is equal to the message it triggers match.
// 
// Dependencies: none
// 
// Revision 0.01 - File Created
// Additional Comments: not really
// 
//////////////////////////////////////////////////////////////////////////////////

module buffer_comparator (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        new_byte,       // From uart_rx
    input  wire [7:0]  the_byte,       // New received UART byte
    output reg         match           // Goes high for 1 cycle when "MARCO" is matched
);

    // Shift register buffer (last 5 characters)
    reg [7:0] buffer [0:4];  // buffer[4] = newest

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            buffer[0] <= 8'd0;
            buffer[1] <= 8'd0;
            buffer[2] <= 8'd0;
            buffer[3] <= 8'd0;
            buffer[4] <= 8'd0;
            match     <= 1'b0;
        end else begin
            match <= 1'b0;

            if (new_byte) begin
                // Shift left, insert newest byte at end
                buffer[0] <= buffer[1];
                buffer[1] <= buffer[2];
                buffer[2] <= buffer[3];
                buffer[3] <= buffer[4];
                buffer[4] <= the_byte;

                // Check for "MARCO"
                if (buffer[1] == "M" &&
                    buffer[2] == "A" &&
                    buffer[3] == "R" &&
                    buffer[4] == "C" &&
                    the_byte  == "O") begin
                    match <= 1'b1;
                end
            end
        end
    end

endmodule

