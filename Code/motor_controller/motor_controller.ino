#include "BluetoothSerial.h"
#include <ESP32Servo.h>

BluetoothSerial SerialBT;
Servo firingServo;
Servo horizontalServo;
Servo tiltingServo;

int firingServoPin = 18;
int horizontalServoPin = 19;
int tiltingServoPin = 5;

char moveState = 'x';
bool isFiring = false;
unsigned long lastFireTime = 0;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  SerialBT.begin("MotorESP");

  firingServo.attach(firingServoPin);
  horizontalServo.attach(horizontalServoPin);
  tiltingServo.attach(tiltingServoPin);

  firingServo.write(150);
  horizontalServo.write(90);
  tiltingServo.write(90);
  
  Serial.println("Initialized Bluetooth and Motors. Pair with PC");

}


void loop() {
  // put your main code here, to run repeatedly:
  if (SerialBT.available()){
    char incoming = SerialBT.read();

    if (incoming == '\n' || incoming == '\r'){
      return; //ignore repeated garbage ie ffffff
    }

    if (incoming == 'f'){
      if (!isFiring){
        isFiring = true;
        lastFireTime = millis();
        
        Serial.println("Firing!!!");
        firingServo.write(10);
    
      }
    }

    else if (incoming == 'w' || incoming == 'a' || incoming == 's' || incoming == 'd' || incoming == 'x'){
      moveState = incoming;
      Serial.print("New Move State: ");
      Serial.println(moveState);
    }

    else{
      Serial.print("Invalid Command Received: ");
      Serial.println(incoming);
    }
  }

  if (moveState == 'w'){
    tiltingServo.write(135);
    Serial.println("Moving Forwards");
  }
  
  else if (moveState == 's'){
    tiltingServo.write(45);
    Serial.println("Moving Backwards");
  }

  else if (moveState == 'a'){
    horizontalServo.write(135);
    Serial.println("Moving Left");
  }

  else if (moveState == 'd'){
    horizontalServo.write(45);
    Serial.println("Moving Right");
  }

  else if (moveState == 'x'){
    horizontalServo.write(90);
    tiltingServo.write(90);

    Serial.println("Stop");
  }
  

  if (isFiring && (millis() - lastFireTime >= 400)){
    firingServo.write(150);
    //delay(400);
    //firingServo.write(90);
    isFiring = false;
    Serial.println("Trigger Reset");
    
    while (SerialBT.available() && SerialBT.peek() == 'f'){ //clearing any fffff during 300ms interval
      SerialBT.read(); //discards the extra ffff by reading and not storing it
    }
  }


  delay(10);

}
