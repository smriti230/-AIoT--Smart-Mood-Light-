#include <SPI.h>
#include <Ethernet.h>
#include <PubSubClient.h>
#include "HardwareSerial.h"

// Update these with values suitable for your network.
byte mac[]    = {  0xDE, 0xED, 0xBA, 35, 0xFE, 0xED };
IPAddress ip(172, 16, 0, 100);
IPAddress server(44, 195, 202, 69);
const char* rgb_values_topic = "rgb_values_topic"; // Replace with the actual topic

// Define the pins for each color channel
const int redPin = A0;
const int greenPin = D14;
const int bluePin = D15;

EthernetClient ethClient;
PubSubClient client(ethClient);

int redValue = 0;
int greenValue = 0;
int blueValue = 0;

void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";

  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  // Assuming the payload is in the format "R,G,B" (e.g., "255,0,0" for red)
  int commaIndex1 = message.indexOf(',');
  int commaIndex2 = message.indexOf(',', commaIndex1 + 1);

  if (commaIndex1 != -1 && commaIndex2 != -1) {
    redValue = message.substring(0, commaIndex1).toInt();
    greenValue = message.substring(commaIndex1 + 1, commaIndex2).toInt();
    blueValue = message.substring(commaIndex2 + 1).toInt();

    Serial.print("RGB: "); Serial.print(redValue);  Serial.print(greenValue); Serial.println(blueValue);
  }
}

void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect("arduinoClient35")) {
      Serial.println("connected");
      // Once connected, publish an announcement...
      client.publish("rgb_topic", "Values Sent!!");
      // ... and resubscribe
      client.subscribe(rgb_values_topic); // Subscribe to the rgb_values_topic
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void setup()
{
    //STM32F429ZI's Serial port changed from default Serial Port
  Serial3.setRx(PC11);
  Serial3.setTx(PC10); 
  Serial3.begin(9600);


  Serial.begin(9600);
  //Ethernet.init(17);

  client.setServer(server, 1883);
  client.setCallback(callback);

  Ethernet.begin(mac);
  // Allow the hardware to sort itself out
  delay(1500);

  // Set each pin as an OUTPUT
  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);
}

void loop()
{
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Set the color of the RGB LED based on the received RGB values
  analogWrite(redPin, 255 - redValue);
  analogWrite(greenPin,255 - greenValue);
  analogWrite(bluePin, 255 - blueValue);

  // Add any other code here that you want to run continuously
}



