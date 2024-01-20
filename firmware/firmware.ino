#include <FastLED.h>

#define BUILTIN_LED 2
#define NUM_LEDS 400
#define WS2812B_PIN 12
#define BUFFER_SIZE NUM_LEDS * 3

CRGB leds[NUM_LEDS];
byte buffer[BUFFER_SIZE];

void emptySerialBuffer() {
  while (Serial.available() > 0) {
    char __attribute__((unused)) c = Serial.read();  // Read and discard each character
  }
}

void fillLEDS() {
  for (int i = 0; i < BUFFER_SIZE / 3; i++) {
    int bufferIndex = i * 3;
    leds[i] = CRGB(buffer[bufferIndex+1], buffer[bufferIndex + 2], buffer[bufferIndex + 0]);
  }
}

void setup() {
  // Highest baudrate which worked consistantly. 921600 is also the ESP32 upload speed.
  Serial.begin(921600);  

  pinMode(BUILTIN_LED, OUTPUT);

  FastLED.addLeds<WS2812B, WS2812B_PIN>(leds, NUM_LEDS);
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
}

void loop() {
  int bytesCount = Serial.readBytes(buffer, BUFFER_SIZE);

  // Probably be unnecessary, as Serial.readBytes removes the read bytes from the RX buffer
  emptySerialBuffer();

  if (bytesCount > 0) {
    digitalWrite(BUILTIN_LED, HIGH);

    fillLEDS();
    FastLED.show();

    // Not essential as, the buffer will always be completely overwritten when RX recevies new data.
    memset(buffer, 0, BUFFER_SIZE);

    digitalWrite(BUILTIN_LED, LOW);
  }

  delay(1);
}