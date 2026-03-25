#include <stddef.h>
#include <stdint.h>
#include "mxc.h"
#include "cnn.h"

volatile uint32_t cnn_time;

// Define a buffer to hold the 6 incoming features
int32_t sensor_data[6];

void process_incoming_data(void) {
    // Read 24 bytes (6 ints * 4 bytes) from UART
    int rx_len = 24;
    MXC_UART_Read(MXC_UART0, (uint8_t*)sensor_data, &rx_len);
    
    // Trigger LED to confirm receipt
    LED_On(0); 
}

int main(void)
{
    /* Initialise UART0 at 115200 baud */
    mxc_uart_regs_t *uart = MXC_UART0;
    MXC_UART_Init(uart, 115200, MXC_UART_APB_CLK);

    /* Initialise CNN accelerator */
    cnn_enable(MXC_S_GCR_PCLKDIV_CNNCLKSEL_PCLK,
               MXC_S_GCR_PCLKDIV_CNNCLKDIV_DIV1);
    cnn_init();
    cnn_load_weights();
    cnn_load_bias();

    /* Main inference loop */
    while (1) {
        process_incoming_data();
    }
}
