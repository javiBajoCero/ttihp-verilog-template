`timescale 1ns / 1ps
`default_nettype none
//////////////////////////////////////////////////////////////////////////////////
// Company: DAKKA POWER ELECTRONICS S.L
// Engineer: Javier MS
// 
// Create Date: 06/30/2025 12:20:25 AM
// Module Name: single_addresable_led
// Target Devices: spartan7 fpga and tiny tapeout ASIC
// Tool Versions: 
// Description: drives a single addressable 800Khz WS2812  led, the depending of color_select it will output color0 or color1 
// 
// Dependencies: none
// 
// Revision 0.01 - File Created
// Additional Comments: not really
// 
//////////////////////////////////////////////////////////////////////////////////

module single_addresable_led (
    input  wire clk,
    input  wire rst_n,
    input  wire color_select,   
    input wire  [23:0] color0,
    input wire  [23:0] color1,
    output reg led_data_out
);

    // Timing constants (50 MHz clock)
    localparam T1H         = 40;      // 800 ns
    localparam T0H         = 20;      // 400 ns
    localparam TOTAL       = 62;      // 1.24 us total bit time
    localparam RESET_TIME  = 2500;    // 50 us reset time
    localparam COLOR1_TIME = 5_000_000; // 100 ms (50 MHz clock)

    // State machine
    localparam IDLE  = 0,
               LOAD  = 1,
               SEND  = 2,
               RESET = 3;

    reg [2:0]  state;
    reg [5:0]  clk_cnt;
    reg [4:0]  bit_index;
    reg [11:0] reset_cnt;
    reg        bit_val;

    reg [23:0] color_reg;
    reg        active_color;         // 0: color0, 1: color1
    reg [22:0] shift_reg;

    // 100 ms timer for color1
    reg [22:0] color1_timer;
    wire       use_color1;

    assign use_color1 = (color1_timer != 0);

    // Color selection logic (on color_select)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            color1_timer <= 0;
        end else begin
            if (color_select)
                color1_timer <= COLOR1_TIME;
            else if (color1_timer != 0)
                color1_timer <= color1_timer - 1;
        end
    end

    // LED driving FSM
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            led_data_out   <= 0;
            clk_cnt    <= 0;
            bit_index  <= 0;
            reset_cnt  <= 0;
            shift_reg  <= 0;
            color_reg  <= 0;
            state      <= IDLE;
        end else begin
            case (state)
                IDLE: begin
                    color_reg <= use_color1 ? color1 : color0;
                    shift_reg <= use_color1 ? color1 : color0;
                    clk_cnt   <= 0;
                    bit_index <= 0;
                    state     <= LOAD;
                end

                LOAD: begin
                    bit_val   <= shift_reg[23];
                    shift_reg <= {shift_reg[22:0], 1'b0};
                    clk_cnt   <= 0;
                    led_data_out  <= 1;
                    state     <= SEND;
                end

                SEND: begin
                    clk_cnt <= clk_cnt + 1;

                    if (bit_val && clk_cnt == T1H)
                        led_data_out <= 0;
                    else if (!bit_val && clk_cnt == T0H)
                        led_data_out <= 0;

                    if (clk_cnt == TOTAL) begin
                        if (bit_index == 23) begin
                            state     <= RESET;
                            reset_cnt <= 0;
                            led_data_out  <= 0;
                        end else begin
                            bit_index <= bit_index + 1;
                            state     <= LOAD;
                        end
                    end
                end

                RESET: begin
                    led_data_out  <= 0;
                    reset_cnt <= reset_cnt + 1;
                    if (reset_cnt >= RESET_TIME)
                        state <= IDLE;
                end

                default: state <= IDLE;
            endcase
        end
    end

endmodule
