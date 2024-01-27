#include <stdint.h>
#include <FastLED.h>

#define LED_PIN     48  // Define the pin to which the LED is connected
#define NUM_LEDS    400  // Number of LEDs (1 for the built-in RGB LED on ESP32-S3)
#define RX_BUFFER_SIZE 1300 // 256 * 5 + 1 = 1281 rounded up.
// #define RX_BUFFER_SIZE NUM_LEDS * 3 + 1

#define STATUS_CODE_ERROR             0
#define STATUS_CODE_TOO_SLOW          1
#define STATUS_CODE_NON_MATCHING_CRC  2
#define STATUS_CODE_UNKNOWN_COMMAND   3
#define STATUS_CODE_OK                100
#define STATUS_CODE_NEXT              101
#define STATUS_CODE_RESET   	        255 // Emptying all serial buffers on both master and slave side, both not sending data for ~100 ms

CRGB leds[NUM_LEDS];
CRGB leds_old[NUM_LEDS];

uint8_t buffer[RX_BUFFER_SIZE];

void empty_rx_buffer() {
  while (Serial.available() > 0) {
    char __attribute__((unused)) c = Serial.read();  // Read and discard each character
  }
}

void finalize_command(int status_code) {
  // Not essential as, the buffer will always be completely overwritten when RX recevies new data.
  memset(buffer, 0, RX_BUFFER_SIZE);

  // Making sure that the Serial RX buffer is empty. 
  // THIS SHOULD BE EMPTY, AND THUS SHOULD NOT HAPPEN
  if(Serial.available()  != 0) {
    Serial.write(STATUS_CODE_RESET);
    delay(60);
    empty_rx_buffer();
    delay(20);
  } else {
    Serial.write(status_code);
  }
}

void command_0_show_pixels() {
  FastLED.show();
  finalize_command(STATUS_CODE_OK);
}

void command_1_clear_all() {
  FastLED.clear();
  finalize_command(STATUS_CODE_OK);
}

void command_2_update_all() {
  // Reading all color codes and indexes into buffer
  Serial.write(STATUS_CODE_NEXT);
  const int sizeof_incomming_data = NUM_LEDS*3+1;
  while(Serial.available() < 1); // Wait until first byte as been received, before we start reading bytes and start the read timer
  if(Serial.readBytes(buffer, sizeof_incomming_data) != sizeof_incomming_data) {
    // Checks if serial buffer is empty, if so, it send back ERROR
    finalize_command(STATUS_CODE_TOO_SLOW);
    return;
  }

  // Making copy of current state of leds if CRC is not matching
  memcpy(&leds_old, &leds, NUM_LEDS); 

  // Setting all the CRGB values into the "leds" variable on the correct index
  uint8_t crc = 0;
  for(uint16_t i = 0; i < NUM_LEDS*3; i += 3) {
    uint16_t led_idx = i*3;
    leds[led_idx] = CRGB(buffer[i + 0], buffer[i + 1], buffer[i + 2]);
    crc += buffer[i + 0] + buffer[i + 1] + buffer[i + 2];
  }

  // Checking if the crc is matching, if not the old leds RGB values will be copied back.
  if(buffer[NUM_LEDS*3] != crc) {
    memcpy(&leds, &leds_old, NUM_LEDS); // Copying back old leds, because crc is not matching

    // Checks if serial buffer is empty, if so, it send back NON_MATCHING_CRC
    finalize_command(STATUS_CODE_NON_MATCHING_CRC);

    return;
  }
  
  // Checks if serial buffer is empty, if so, it send back OK
  finalize_command(STATUS_CODE_OK);
}

void command_3_update_specific() {
  // Receiving the number of pixel RGB codes will be changed
  Serial.write(STATUS_CODE_NEXT);
  while(Serial.available() < 1); 
  uint8_t pixel_update_count = Serial.read();
  uint16_t buffer_size = pixel_update_count * 5 + 1;

  // Reading all color codes and indexes into buffer
  Serial.write(STATUS_CODE_NEXT);
  while(Serial.available() < 1); // Wait until first byte as been received, before we start reading bytes and start the read timer
  if(Serial.readBytes(buffer, buffer_size) != buffer_size) {
    // Checks if serial buffer is empty, if so, it send back ERROR
    finalize_command(STATUS_CODE_TOO_SLOW);
    return;
  }

  // Making copy of current state of leds if CRC is not matching
  memcpy(&leds_old, &leds, NUM_LEDS); 

  // Setting all the CRGB values into the "leds" variable on the correct index
  uint8_t crc = 0;
  for(uint16_t i = 0; i < buffer_size-1; i += 5) {
    /* Appends to bytes to create a 16-bit integer. Example:
    byte 0: 1101 0001
    byte 1: 0000 1100
    result: 1101 0001 0000 1100 */
    uint16_t led_idx = (buffer[i+0] << 8) + buffer[i+1];
  
    leds[led_idx] = CRGB(buffer[i + 2], buffer[i + 3], buffer[i + 4]);
    crc += buffer[i + 0] + buffer[i + 1] + buffer[i + 2] + buffer[i + 3] + buffer[i + 4];
  }

  // Checking if the crc is matching, if not the old leds RGB values will be copied back.
  if(buffer[buffer_size-1] != crc) {
    memcpy(&leds, &leds_old, NUM_LEDS); // Copying back old leds, because crc is not matching

    // Checks if serial buffer is empty, if so, it send back NON_MATCHING_CRC
    finalize_command(STATUS_CODE_NON_MATCHING_CRC);

    return;
  }

  // Checks if serial buffer is empty, if so, it send back OK
  finalize_command(STATUS_CODE_OK);
}

void setup() {
  Serial.begin(921600);
  Serial.setTimeout(10); // It takes 1.6ms to transfer 12000 bites over serial (921600), at 100% efficiency.

  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);  
}

void loop() {
  int data = Serial.read();

  switch(data) {
    case 0:
      command_0_show_pixels();
      break;
    case 1:
      command_1_clear_all();
      break;
    case 2:
      command_2_update_all();
      break;
    case 3:
      command_3_update_specific();
      break;
    case -1:
      // This means there is no incomming serial data, do nothing.
      break;
    default:
      Serial.write(STATUS_CODE_UNKNOWN_COMMAND);
      break;      
  }
}
