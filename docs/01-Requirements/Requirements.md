---
title: Mobility / Drive Actuation Module's Requirements
---

## Module Requirements
This section of the website outlines the requirements for the proper operation of my subsystem. The table includes threshold and target measures for each requirement. The rover's mobility is key, and ensuring that the motors and wheels support the upper body is crucial. Each requirement is important for the proper operation of my subsystem, ensuring it not only works properly but also meets EGR 314 criteria. Motor drivers require 9V, so my subsystem needs an additional power source. I have also included an additional column to show if the measure stretch requirement is met. The target measure is ideal for my motor, PCB, and power system.

| Requirement description | Measure of threshold | Target measure | Stretch requirement (Y-N) |
| :---- | :---- | :---- | :---- |
| Surface-mounted, 3.3 V switching regulator | 3.2 Volts | Stable 3.3 Volts | **No** |
| Surface-mounted microcontroller for mobility control | 1 PIC18F or ESP32 | ESP32 | **No** |
| Wireless communication through UART | Able to send or receive data with at least a wireless communication subsystem | Send and receive Wi-Fi Data to MQTT to all subsystems | **Yes** |
| Consumption of power | Motors, motor driver, and PCB do not heat up too much | Meets power budget guidelines | **No** |
| Low-voltage DC motors | 4 Brushless DC motors | 2 brushless DC motors can hold and move the upper body of the rover | **No** |
| Motor driver | L298N motor driver | No overheating in the test window | **No** |
| Shared power for motor | Module runs well with pin header| Consistent power without need to change source  | **No** |
| The motor moves forward and back | All wheels turn on flat surfaces | No slipping and works well on hard surfaces too | **No** |
| Motor turns right and left | 2 motors on the left and 2 on the right turn together and move, staying in the  same place | The steering system works, and the 2 motors work with better-controlled movement | **Yes** |
| 4 Wheels | Wheels are good enough to hold the rover | Wheels operate well and have stable alignment | **No** |
| Mechanical constraints | Fits within a decided shape  | Clean mounting of motors to the PCB | **No** | 

