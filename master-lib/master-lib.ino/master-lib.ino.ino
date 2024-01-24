#include "FastLED.h"

#define NUM_LEDS 400
#define LED_PIN 2
#define PIN 12
#define BUFFER_SIZE 1200

byte buffer[BUFFER_SIZE];
CRGB leds[NUM_LEDS];

void setup() {
  Serial.begin(2000000); // opens serial port, sets data rate to 2MHz
  FastLED.addLeds<WS2812B, PIN, RGB>(leds, NUM_LEDS);
}

void loop() {
  // Read the specified number of bytes into the buffer
  int bytesRead = Serial.readBytes(buffer, BUFFER_SIZE);

  if (bytesRead > 0) {
    fill_leds();

    FastLED.show();
    
    memset(buffer, 0, sizeof(buffer));
  }

  delay(1);
}

void fill_leds() {
  for(int i = 0; i < BUFFER_SIZE/3; i++) {
    int buffer_index = i * 3;
    leds[i] = CRGB(buffer[buffer_index, buffer_index+1, buffer_index+2]);
  }
}