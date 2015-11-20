# Water Monitor

Reads a HMC5883L sensor to detect a magnet spinning inside a water meter.
Reverses to field strength on the y axis are counted to detect water is flowing.
Liters in a period are uploaded to grovestreams for graphing.

Wiring:

| HMC5883L Pin | Raspberry Pi Pin |
| ------------ | ---------------- |
| Vin          | 1                |
| Gnd          | 6                |
| SDA          | 3                |
| SCL          | 5                |


