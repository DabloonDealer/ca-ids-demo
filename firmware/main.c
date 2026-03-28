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

#define PAYLOAD_LEN   60
#define N_TIMESTEPS   10
#define N_FEATURES    6
#define N_CLASSES     5
#define CNN_IN0_BASE  0x50400000u
#define CNN_IN4_BASE  0x50408000u

static uint8_t rx_buf[64];
static int8_t window[N_TIMESTEPS][N_FEATURES];

static uint8_t rx_seq;
static uint8_t rx_payload[PAYLOAD_LEN];
static uint8_t rx_crc;
static uint8_t rx_payload_idx;

volatile uint32_t cnn_time;

static void uart_flush(void)
{
    while (MXC_UART_ReadyForSleep(MXC_UART0) != E_NO_ERROR) {}
}

static void uart_write_blocking(const uint8_t *buf, int len)
{
    for (int i = 0; i < len; i++) {
        while (MXC_UART_WriteCharacter(MXC_UART0, buf[i]) == E_OVERFLOW) {}
    }
    uart_flush();
}

static void uart_print(const char *s)
{
    uart_write_blocking((const uint8_t *)s, (int)strlen(s));
}

static void uart_print_uint8(uint8_t val)
{
    char buf[4];
    int i = 3;
    buf[i] = '\0';
    if (val == 0) {
        buf[--i] = '0';
    } else {
        while (val > 0) {
            buf[--i] = '0' + (val % 10);
            val /= 10;
        }
    }
    uart_print(&buf[i]);
}

static void uart_print_int32(int32_t val)
{
    char buf[12];
    int i = 11;
    uint8_t neg = 0;

    buf[i] = '\0';

    if (val < 0) {
        neg = 1;
        val = -val;
    }

    if (val == 0) {
        buf[--i] = '0';
    } else {
        while (val > 0) {
            buf[--i] = '0' + (val % 10);
            val /= 10;
        }
    }

    if (neg) {
        buf[--i] = '-';
    }

    uart_print(&buf[i]);
}

static void load_window(void)
{
    for (int t = 0; t < N_TIMESTEPS; t++) {
        for (int f = 0; f < N_FEATURES; f++) {
            window[t][f] = (int8_t)rx_payload[f * N_TIMESTEPS + t];
        }
    }
}

static void load_cnn_input(void)
{
    volatile uint32_t *cnn_input_0 = (volatile uint32_t *)CNN_IN0_BASE;
    volatile uint32_t *cnn_input_4 = (volatile uint32_t *)CNN_IN4_BASE;

    for (int t = 0; t < N_TIMESTEPS; t++) {
        uint32_t packed_0 = ((uint8_t)window[t][0]) |
                            (((uint8_t)window[t][1]) << 8) |
                            (((uint8_t)window[t][2]) << 16) |
                            (((uint8_t)window[t][3]) << 24);
        uint32_t packed_4 = ((uint8_t)window[t][4]) |
                            (((uint8_t)window[t][5]) << 8);

        cnn_input_0[t] = packed_0;
        cnn_input_4[t] = packed_4;
    }
}

static int run_inference(void)
{
    uint32_t out[N_CLASSES];
    int label = 0;

    cnn_start();

    while (cnn_time == 0) {
        __WFI();
    }
    cnn_time = 0;

    cnn_unload(out);

    for (int i = 1; i < N_CLASSES; i++) {
        if ((int32_t)out[i] > (int32_t)out[label]) {
            label = i;
        }
    }

    return label;
}

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
            else state = WAIT_SOF1;
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
                rx_buf[0] = 0xA5;
                rx_buf[1] = 0x5A;
                rx_buf[2] = rx_seq;
                memcpy(&rx_buf[3], rx_payload, PAYLOAD_LEN);
                rx_buf[63] = rx_crc;

                load_window();
                load_cnn_input();

                uart_print("PARSE_OK,");
                uart_print_uint8(rx_seq);
                uart_print(" CLASS=");
                uart_print_int32(run_inference());
                uart_print("\n");
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

int main(void)
{
    MXC_UART_Init(MXC_UART0, 115200, MXC_UART_APB_CLK);

    // Give the USB-UART bridge / terminal a moment to attach after reset.
    MXC_Delay(MXC_DELAY_MSEC(500));

    uart_print("CA-IDS firmware ready\r\n");
    cnn_enable(MXC_S_GCR_PCLKDIV_CNNCLKSEL_PCLK, MXC_S_GCR_PCLKDIV_CNNCLKDIV_DIV1);
    cnn_init();
    cnn_load_weights();
    cnn_load_bias();
    cnn_configure();

    uart_print("Task 3: CNN loaded. Waiting for packets...\r\n");
    run_parser();
    return 0;
}
