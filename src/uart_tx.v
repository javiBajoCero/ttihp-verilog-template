`timescale 1ns/1ps
`default_nettype none

module uart_tx (
    input  wire clk,         // system clock
    input  wire rst_n,       // active-low reset
    input  wire baud_tick,   // 9600 baud tick (1 cycle per bit)
    input  wire send,        // trigger to start sending "POLO\n"
    output wire tx,          // UART transmit line
    output wire busy         // high when sending
);

    // State machine states
    typedef enum logic [2:0] {
        IDLE,
        START_BIT,
        DATA_BITS,
        STOP_BIT,
        NEXT_BYTE,
        DONE
    } state_t;

    state_t state;

    reg [7:0] message [0:4];      // "POLO\n"
    reg [2:0] bit_index;
    reg [2:0] byte_index;
    reg [7:0] shift_reg;
    reg tx_reg;
    reg sending;

    assign tx = tx_reg;
    assign busy = sending;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Async reset
            state       <= IDLE;
            bit_index   <= 0;
            byte_index  <= 0;
            shift_reg   <= 8'h00;
            tx_reg      <= 1'b1;
            sending     <= 1'b0;

            // Initialize message buffer
            message[0] <= 8'h50; // 'P'
            message[1] <= 8'h4F; // 'O'
            message[2] <= 8'h4C; // 'L'
            message[3] <= 8'h4F; // 'O'
            message[4] <= 8'h0A; // '\n'
        end else begin
            case (state)
                IDLE: begin
                    tx_reg <= 1'b1;
                    sending <= 1'b0;
                    if (send) begin
                        byte_index <= 0;
                        shift_reg <= message[0];
                        state <= START_BIT;
                        sending <= 1'b1;
                    end
                end

                START_BIT: begin
                    if (baud_tick) begin
                        tx_reg <= 1'b0; // Start bit
                        bit_index <= 0;
                        state <= DATA_BITS;
                    end
                end

                DATA_BITS: begin
                    if (baud_tick) begin
                        tx_reg <= shift_reg[0];
                        shift_reg <= {1'b0, shift_reg[7:1]};
                        if (bit_index == 7)
                            state <= STOP_BIT;
                        else
                            bit_index <= bit_index + 1;
                    end
                end

                STOP_BIT: begin
                    if (baud_tick) begin
                        tx_reg <= 1'b1; // Stop bit
                        state <= NEXT_BYTE;
                    end
                end

                NEXT_BYTE: begin
                    if (baud_tick) begin
                        if (byte_index == 4) begin
                            state <= DONE;
                        end else begin
                            byte_index <= byte_index + 1;
                            shift_reg <= message[byte_index + 1];
                            state <= START_BIT;
                        end
                    end
                end

                DONE: begin
                    sending <= 1'b0;
                    state <= IDLE;
                end
            endcase
        end
    end

endmodule
