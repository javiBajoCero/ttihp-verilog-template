`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 06/30/2025 12:20:25 AM
// Design Name: 
// Module Name: uart_rx
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module uart_rx (
    input  wire clk,
    input  wire rst_n,
    input  wire baud_tick,   // oversampled (e.g. 8x)
    input  wire rx,          // serial input line
    output reg  [7:0] data,
    output reg  byte_received
);

    localparam [2:0]
        IDLE     = 3'd0,
        START    = 3'd1,
        DATA     = 3'd2,
        STOP     = 3'd3;

    reg [2:0] state;
    reg [2:0] bit_index;
    reg [3:0] baud_ctr;
    reg [7:0] rx_shift;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state      <= IDLE;
            bit_index  <= 0;
            baud_ctr   <= 0;
            rx_shift   <= 0;
            data       <= 0;
            byte_received <= 0;
        end else begin
            byte_received <= 0;

            if (baud_tick) begin
                case (state)
                    IDLE: begin
                        if (!rx) begin // start bit detected
                            state <= START;
                            baud_ctr <= 0;
                        end
                    end
                    START: begin
                        if (baud_ctr == 4) begin  // sample at center of bit
                            if (!rx) begin
                                state <= DATA;
                                bit_index <= 0;
                            end else begin
                                state <= IDLE;
                            end
                        end else
                            baud_ctr <= baud_ctr + 1;
                    end
                    DATA: begin
                        if (baud_ctr == 7) begin
                            rx_shift <= {rx, rx_shift[7:1]};
                            baud_ctr <= 0;
                            if (bit_index == 7)
                                state <= STOP;
                            else
                                bit_index <= bit_index + 1;
                        end else
                            baud_ctr <= baud_ctr + 1;
                    end
                    STOP: begin
                        if (baud_ctr == 7) begin
                            if (rx) begin // stop bit OK
                                data <= rx_shift;
                                byte_received <= 1;
                            end
                            state <= IDLE;
                            baud_ctr <= 0;
                        end else
                            baud_ctr <= baud_ctr + 1;
                    end
                endcase
            end
        end
    end

endmodule
