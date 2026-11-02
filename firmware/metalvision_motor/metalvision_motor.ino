#include <Stepper.h>

const int stepsPerRevolution = 2048;

// Motor pins (28BYJ-48 via ULN2003 driver)
Stepper motor(stepsPerRevolution, 8, 10, 9, 11);

// Potentiometer
const int potPin = A0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  // Read potentiometer
  int potValue = analogRead(potPin);

  // Map potentiometer to motor speed
  int motorSpeed = map(potValue, 0, 1023, 1, 15);

  // Set motor speed
  motor.setSpeed(motorSpeed);

  // Continuously rotate
  motor.step(50);

  // Display speed
  Serial.print("Pot Value: ");
  Serial.print(potValue);

  Serial.print(" | Motor Speed: ");
  Serial.print(motorSpeed);
  Serial.println(" RPM");
}
