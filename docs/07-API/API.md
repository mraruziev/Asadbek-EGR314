---
title: Mobillity API
---

## Overview
This page exists to show the API messaging of the Wheel and mobillity subsystem. API stands for Application Programming Interface.
The following are messages sent and received to my board. Some messages get passed from me, as my subsystem will check the message and send it to the next person.
The subsystem's ID is "w".

Cristopher sends me a message via MQTT/WiFi, and I verify it. I use it to send it back to him. He forwards it to Jacob. Jacob will share the wheel commands with my board. Each message will have a destination type instead of being a loop source. It is also broadcasted used for everyone. Messages will be done one by one, as it is a daisy chain.



### All Subsystem IDs

| Subsystem               | Identifier | Person                  |
| ----------------------- | ---------- | ----------------------- |
| HMI                     | h          | Jacob                   |
| Communication           | c          | Cris                    |
| Wheels                  | w          | Asadbek                 |
| Pressure/Accelerometer  | p          | Tyler                   |
| Front Arm               | a          | Caleb                   |
| Metal Detector          | m          | Aaron                   |
| Temperature/Humidity    | t          | Isaiah                  |
| Broadcast               | X          | System-Wide Messaging   |


## Message data types

| Description              | Prefix |
| ------------------------ | ------ |
| String (ASCII char array)| S:     |
| Integer (8 Bit)          | I:     |
| Integer (16 Bit)         | IL:    |
| Float (32 Bit)           | F:     |

## Received Messages
- Message framing for single-character subsystem IDs 
- AZ [Sender] [Receiver] [Data in the message (1-58 bytes) ] BY
- | WD:S:F |
- | WD:S:B |
- | WD:S:R |
- | WD:S:L |
The wheel subsystem will receive drive commands from the HMI and start broadcasting. Those commands are processed and sent back to the HMI with the values I receive over UART.

If Jacob/HMI is commanding wheels:
* Forward: AZhwWD:S:F;YB
* Backward: AZhwWD:S:B;YB
* Right: AZhwWD:S:R;YB
* Left: AZhwWD:S:L;YB
Start broadcast to everyone:
* AZhXST:S:Start;YB
If Chris/Communication is checking wheel Bluetooth:
* AZcwBT:S:check;YB
If you want to force-stop for testing, your current wheel code also supports:
* AZhwWD:S:S;YB

### Message Type -- Start Broadcast

As shown above, this is broadcast message for my board: `AZhXST:S:Start;YB`

| Bytes 1–3       | Bytes 4–5 | Bytes 6–11 |
| --------------- | --------- | ---------- |
| **Name**        | **Type**  | **Data**   |
| ST:             | S:        | Start;     |
| **Min**         |           | Start;     |
| **Max**         |           | Start;     |
| **Example** ST: | S:        | Start;     |

### Message Type -- Wheel Drive Mode

Receives the direction command from the HMI D-Pad and drives the wheels accordingly.

`AZhwWD:S:F;YB`

| Bytes 1–3       | Bytes 4–5 | Bytes 6–7         |
| --------------- | --------- | ----------------- |
| **Name**        | **Type**  | **Data**          |
| WD:             | S:        | F; / B; / R; / L; |
| **Min**         |           | F; / B; / R; / L; |
| **Max**         |           | F; / B; / R; / L; |
| **Example** WD: | S:        | F;                |



## Meaning for the messaging:
- `AZ` = Packet start
- `h` = HMI subsystem
- `X` = Broadcast to everyone
- `ST` = Start
- `S` = String
- `Start` = Communication started / LED on
- `YB` = End of packet


## Behaviour check
- Check whether the format of the message packet is valid
- Check if it is for the wheel subsystem
- Check the destination if not

## Receiving messages

When a byte comes through the UART/MQTT to my board
1. Look for the AZ packet prefix, and anything non-related is discarded
2. I read bytes into a buffer till suffix BY is found or the buffer limit of 62 bytes is exceeded.
3. If receiver == w (my board), the message is parsed
4. If receiver == X (broadcast), the message is parsed and processed
5. If the message receiver is not me, the packet is going to be forwarded out the downstream UART byte-for-byte


| Section | Bytes amount | Name of the variable | Tpe ID | Example for the code |
| :---- | :---- | :---- | :---- | :---- |
| Type ID | 5 | S | char | S |
| Variable | 2 | WD | char | WD |
| Seperator | 1 |  | char | : |
| Terminator value | 1 | DRCTN | char | : |
| Value | 1 |  | char |  |

Overall message bytes: 12


## Sending messages
| Section | Bytes amount | Name of the variable | Tpe ID | Example for the code |
| :---- | :---- | :---- | :---- | :---- |
| Type ID | 5 | S | char | S |
| Variable | 1 | : | char | ST |
| Seperator | 1 | : | char | : |
| Terminator value | 1 | DRCTN | char | : |
| Value | 1 | Start | char | Start |

Overall message bytes: 12




Example: AZhXST:S:Start;YB
