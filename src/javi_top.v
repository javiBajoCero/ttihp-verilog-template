`timescale 1ns/1ps
`default_nettype none

module tt_um_javibajocero_top (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

    // --- UART Baud Generators ---
    wire baud_tick_tx;
    wire baud_tick_rx;

    baud_generator #(.BAUD_DIV(5208)) baud_gen_tx ( // 50MHz / 9600
        .clk(clk),
        .rst_n(rst_n),
        .baud_tick(baud_tick_tx)
    );

    baud_generator #(.BAUD_DIV(651)) baud_gen_rx ( // 50MHz / (9600 * 8)
        .clk(clk),
        .rst_n(rst_n),
        .baud_tick(baud_tick_rx)
    );

    // --- UART RX ---
    wire [7:0] rx_data;
    wire       rx_valid;

    uart_rx uart_rx_inst (
        .clk(clk),
        .rst_n(rst_n),
        .baud_tick(baud_tick_rx),
        .rx(uio_in[0]),     // RX from pin
        .data(rx_data),
        .byte_received(rx_valid)
    );

    // --- Buffer Comparator (detect "MARCO") ---
    wire trigger_send;

    buffer_comparator comp (
        .clk(clk),
        .rst_n(rst_n),
        .new_byte(rx_valid),
        .the_byte(rx_data),
        .match(trigger_send)
    );

    // --- UART TX ---
    wire tx_busy;
    wire tx_serial;

    uart_tx uart_tx_inst (
        .clk(clk),
        .rst_n(rst_n),
        .baud_tick(baud_tick_tx),
        .send(trigger_send),
        .tx(tx_serial),
        .busy(tx_busy)
    );

    // --- Output Connections ---
    assign uo_out[0] = tx_serial;
    assign uo_out[1] = baud_tick_rx;
    assign uo_out[2] = baud_tick_tx;
    assign uo_out[3] = trigger_send;
    assign uo_out[4] = tx_busy;
    assign uo_out[5] = 1'b1;
    assign uo_out[6] = 1'b1;
    assign uo_out[7] = 1'b1;

    // --- UART TX routing to IO pin ---
    assign uio_out[0] = tx_serial;
    assign uio_oe[0]  = 1'b1;

    // --- All other IOs unused ---
    assign uio_out[7:1] = 7'b0;
    assign uio_oe[7:1]  = 7'b0;

    // Unused signal suppression
    wire _unused = ena | &ui_in;

endmodule
