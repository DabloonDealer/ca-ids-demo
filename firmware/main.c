#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include "mxc.h"
#include "mxc_delay.h"
#include "cnn.h"

typedef enum {
    WAIT_SOF1,
    WAIT_SOF2,
    READ_SEQ,
    READ_PAYLOAD,
    READ_CRC,
    VALIDATE
} parser_state_t;

#define PAYLOAD_LEN  60
#define N_TIMESTEPS  10
#define N_FEATURES    6
#define N_CLASSES     5

static uint8_t  rx_buf[64];
static int8_t   window[N_TIMESTEPS][N_FEATURES];
static uint8_t  rx_seq;
static uint8_t  rx_payload[PAYLOAD_LEN];
static uint8_t  rx_crc;
static uint8_t  rx_payload_idx;

volatile uint32_t cnn_time;

static const char *CLASS_NAMES[N_CLASSES] = {
    "Normal", "DoS", "Spoofing", "Replay", "Fuzzing"
};

/* ── UART helpers ─────────────────────────────────────────────────── */
static void uart_flush(void)
{
    MXC_Delay(MXC_DELAY_MSEC(10));
}

static void uart_print(const char *s)
{
    int len = (int)strlen(s);
    MXC_UART_Write(MXC_UART0, (const uint8_t *)s, &len);
    uart_flush();
}

static void uart_print_uint8(uint8_t val)
{
    char buf[4];
    int i = 3;
    buf[i] = '\0';
    if (val == 0) {
        buf[--i] = '0';
    } else {
        while (val > 0) { buf[--i] = '0' + (val % 10); val /= 10; }
    }
    uart_print(&buf[i]);
}

static void uart_print_uint32(uint32_t val)
{
    char buf[11];
    int i = 10;
    buf[i] = '\0';
    if (val == 0) {
        buf[--i] = '0';
    } else {
        while (val > 0) { buf[--i] = '0' + (val % 10); val /= 10; }
    }
    uart_print(&buf[i]);
}

/* ── Window loader ────────────────────────────────────────────────── */
static void load_window(void)
{
    for (int t = 0; t < N_TIMESTEPS; t++)
        for (int f = 0; f < N_FEATURES; f++)
            window[t][f] = (int8_t)rx_payload[t * N_FEATURES + f];
}

/* ── CNN input loader — confirmed layout from sampledata.h ───────── */
static void load_cnn_input(void)
{
    volatile uint32_t *bank0 = (volatile uint32_t *)0x50400000;
    volatile uint32_t *bank1 = (volatile uint32_t *)0x50800000;

    for (int t = 0; t < N_TIMESTEPS; t++) {
        uint8_t f0 = (uint8_t)(int8_t)window[t][0];
        uint8_t f1 = (uint8_t)(int8_t)window[t][1];
        uint8_t f2 = (uint8_t)(int8_t)window[t][2];
        uint8_t f3 = (uint8_t)(int8_t)window[t][3];
        uint8_t f4 = (uint8_t)(int8_t)window[t][4];
        uint8_t f5 = (uint8_t)(int8_t)window[t][5];

        bank0[t] = ((uint32_t)f3 << 24) |
                   ((uint32_t)f2 << 16) |
                   ((uint32_t)f1 << 8)  |
                   ((uint32_t)f0);

        bank1[t] = ((uint32_t)f5 << 8) |
                   ((uint32_t)f4);
    }
}

/* ── Inference ────────────────────────────────────────────────────── */
static int run_inference(uint32_t *out)
{
    cnn_start();
    while (cnn_time == 0) __WFI();
    cnn_time = 0;
    cnn_unload(out);

    int label = 0;
    for (int i = 1; i < N_CLASSES; i++)
        if (out[i] > out[label]) label = i;

    return label;
}

/* ── Result sender ────────────────────────────────────────────────── */
static void send_result(int label, uint32_t *out)
{
    uint32_t score = out[label];
    if (label == 0) {
        uart_print("OK,");
        uart_print_uint32(score);
        uart_print("\n");
    } else {
        uart_print("ALERT,");
        uart_print(CLASS_NAMES[label]);
        uart_print(",");
        uart_print_uint32(score);
        uart_print("\n");
    }
}

/* ── State machine ────────────────────────────────────────────────── */
static void run_parser(void)
{
    parser_state_t state = WAIT_SOF1;
    uint8_t b;
    int len;

    while (1) {
        len = 1;
        MXC_UART_Read(MXC_UART0, &b, &len);

        switch (state) {
        case WAIT_SOF1:
            if (b == 0xA5) state = WAIT_SOF2;
            break;
        case WAIT_SOF2:
            if (b == 0x5A) state = READ_SEQ;
            else            state = WAIT_SOF1;
            break;
        case READ_SEQ:
            rx_seq = b;
            rx_payload_idx = 0;
            state = READ_PAYLOAD;
            break;
        case READ_PAYLOAD:
            rx_payload[rx_payload_idx++] = b;
            if (rx_payload_idx == PAYLOAD_LEN)
                state = READ_CRC;
            break;
        case READ_CRC:
            rx_crc = b;
            state = VALIDATE;
        case VALIDATE: {
            uint8_t crc = rx_seq;
            for (int i = 0; i < PAYLOAD_LEN; i++)
                crc ^= rx_payload[i];

            if (crc == rx_crc) {
                rx_buf[0] = 0xA5; rx_buf[1] = 0x5A; rx_buf[2] = rx_seq;
                memcpy(&rx_buf[3], rx_payload, PAYLOAD_LEN);
                rx_buf[63] = rx_crc;

                load_window();
                load_cnn_input();

                uint32_t out[N_CLASSES];
                int label = run_inference(out);
                send_result(label, out);
            } else {
                uart_print("CRC_FAIL,");
                uart_print_uint8(rx_seq);
                uart_print("\n");
            }
            state = WAIT_SOF1;
            break;
        }
        default:
            state = WAIT_SOF1;
            break;
        }
    }
}

/* ── Main ─────────────────────────────────────────────────────────── */
int main(void)
{
    MXC_UART_Init(MXC_UART0, 115200, MXC_UART_APB_CLK);
    uart_print("CA-IDS firmware ready\r\n");

    cnn_enable(MXC_S_GCR_PCLKDIV_CNNCLKSEL_PCLK,
               MXC_S_GCR_PCLKDIV_CNNCLKDIV_DIV1);
    cnn_init();
    cnn_load_weights();
    cnn_load_bias();
    cnn_configure();

    uart_print("Task 5: Correct input layout. Waiting...\r\n");
    run_parser();
    return 0;
}