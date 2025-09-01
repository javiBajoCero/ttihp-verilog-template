`timescale 1ns / 1ps
`default_nettype none
//////////////////////////////////////////////////////////////////////////////////
// Company: DAKKA POWER ELECTRONICS S.L
// Engineer: Javier MS
// 
// Create Date: 06/31/2025 12:20:25 AM
// Module Name: uart_tx
// Target Devices: spartan7 fpga and tiny tapeout ASIC
// Tool Versions: 
// Description: simple state machine, this is barely a uart, the transmission buffer is hardcoded and the baudrate is controled with baud_tick
//              when the signal send is received, this module spits out the hardcoded message serialiced to tx.
//              busy signal is kept high during the whole transmission , in case we need some flow control or debuging purposes
// Dependencies: none
// 
// Revision 0.01 - File Created
// Additional Comments: not really
// 
//////////////////////////////////////////////////////////////////////////////////

module uart_tx (
    input  wire clk,         // system clock
    input  wire rst_n,       // active-low reset
    input  wire baud_tick,   // 9600 baud tick (1 cycle per bit)
    input  wire send,        // trigger to start sending "POLO\n"
    output wire tx,          // UART transmit line
    output wire busy         // high when sending
);

    localparam [2:0]
        IDLE       = 3'd0,
        START_BIT  = 3'd1,
        DATA_BITS  = 3'd2,
        STOP_BIT   = 3'd3,
        NEXT_BYTE  = 3'd4,
        DONE       = 3'd5;

    reg [2:0] state;
    reg [2:0] bit_index;
    reg [3:0] byte_index;  // extended to fit up to 9 bytes
    reg [7:0] shift_reg;
    reg tx_reg;
    reg sending;

    assign tx = tx_reg;
    assign busy = sending;

    // ROM-like function to return byte from "POLO!\n\r"
    function automatic [7:0] get_message_byte(input [3:0] index);
        case (index)
            4'd0: get_message_byte = 8'h0A; // '\n'
            4'd1: get_message_byte = 8'h0D; // '\r'
            4'd2: get_message_byte = 8'h50; // 'P'
            4'd3: get_message_byte = 8'h4F; // 'O'
            4'd4: get_message_byte = 8'h4C; // 'L'
            4'd5: get_message_byte = 8'h4F; // 'O'
            4'd6: get_message_byte = 8'h21; // '!'
            4'd7: get_message_byte = 8'h0A; // '\n'
            4'd8: get_message_byte = 8'h0D; // '\r'
            default: get_message_byte = 8'h00;
        endcase
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state       <= IDLE;
            bit_index   <= 0;
            byte_index  <= 0;
            shift_reg   <= 8'h00;
            tx_reg      <= 1'b1;
            sending     <= 1'b0;
        end else begin
            case (state)
                IDLE: begin
                    tx_reg <= 1'b1;
                    sending <= 1'b0;
                    if (send) begin
                        byte_index <= 0;
                        shift_reg <= get_message_byte(0);  // preload first byte
                        state <= START_BIT;
                        sending <= 1'b1;
                    end
                end

                START_BIT: begin
                    if (baud_tick) begin
                        tx_reg <= 1'b0;  // start bit
                        bit_index <= 0;
                        state <= DATA_BITS;
                    end
                end

                DATA_BITS: begin
                    if (baud_tick) begin
                        tx_reg <= shift_reg[0];
                        shift_reg <= {1'b0, shift_reg[7:1]};
                        if (bit_index == 3'd7)
                            state <= STOP_BIT;
                        else
                            bit_index <= bit_index + 1;
                    end
                end

                STOP_BIT: begin
                    if (baud_tick) begin
                        tx_reg <= 1'b1; // stop bit
                        state <= NEXT_BYTE;
                    end
                end

                NEXT_BYTE: begin
                    if (baud_tick) begin
                        if (byte_index == 4'd8) begin
                            state <= DONE;
                        end else begin
                            byte_index <= byte_index + 1;
                            shift_reg <= get_message_byte(byte_index + 1);
                            state <= START_BIT;
                        end
                    end
                end

                DONE: begin
                    sending <= 1'b0;
                    state <= IDLE;
                end

                default: begin
                    // recover to safe state
                    state <= IDLE;
                    sending <= 1'b0;
                    tx_reg <= 1'b1;
                end
            endcase
        end
    end

endmodule

