`default_nettype none

module uart_tx (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       tx_valid,
    input  wire [7:0] tx_data,
    output reg        tx_ready,
    output reg        tx_serial,
    input  wire       baud_tick  // <<< use your existing baud_generator output
);

    typedef enum logic [2:0] {
        IDLE    = 3'b000,
        START   = 3'b001,
        DATA    = 3'b010,
        STOP    = 3'b011,
        CLEANUP = 3'b100
    } state_t;

    state_t state;

    reg [3:0] bit_index;
    reg [7:0] shift_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state      <= IDLE;
            tx_serial  <= 1;  // idle = high
            tx_ready   <= 1;
            shift_reg  <= 0;
            bit_index  <= 0;
        end else if (baud_tick) begin  // <<< driven externally
            case (state)
                IDLE: begin
                    tx_serial <= 1;
                    if (tx_valid) begin
                        shift_reg <= tx_data;
                        bit_index <= 0;
                        tx_ready  <= 0;
                        state     <= START;
                    end
                end

                START: begin
                    tx_serial <= 0;  // Start bit
                    state     <= DATA;
                end

                DATA: begin
                    tx_serial <= shift_reg[0];
                    shift_reg <= shift_reg >> 1;
                    bit_index <= bit_index + 1;
                    if (bit_index == 7)
                        state <= STOP;
                end

                STOP: begin
                    tx_serial <= 1;  // Stop bit
                    state     <= CLEANUP;
                end

                CLEANUP: begin
                    tx_ready <= 1;
                    state    <= IDLE;
                end
            endcase
        end
    end

endmodule
