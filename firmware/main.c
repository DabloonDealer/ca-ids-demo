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

#define PAYLOAD_LEN 60

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
                uart_print("PARSE_OK,");
                uart_print_uint8(rx_seq);
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
    uart_print("Task 1: UART parser active\r\n");
    run_parser();
    return 0;
}
