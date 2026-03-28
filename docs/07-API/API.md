---
title: Mobillity API
---

## Overview
This page exists to show the API messaging of the Wheel and mobillity subsystem
Following are messages sent and received to my board. Some messages get passed from me as my subsystem will check the message and sent it to the next person.
The subsystem's ID is "w".

Cristopher sends me a message via Bluetooth, and I verify it. I use it to send it back to him. He forwards it to Jacob. Jacob will tell my board the wheel commands for controlling it. Each message will have a destination type instead of being a loop source. It is also broadcasted used for everyone. Messages will be done one by one, as it is a daisy chain.



### All Subsystem IDs

| Subsystem | ID |
|-----------|-----|
| HMI | 'h' |
| Comm | 'c' |
| Wheel | 'w' |
| Pressure | 'P' |
| Arm | 'a' |
| Metal | 'm' |
| Temp | 't' |


## Received Messages
- Message framing: 
- AZ [Sender] [Receiver] {Data in the message} YB
- | WD:S:F |
- | WD:S:B |
- | WD:S:R |
- | WD:S:L |


## Meaning for the messaging:
- `AZ` = Packet start
- `h` = HMI subsystem
- `X` = Broadcast to everyone
- `ST` = Start
- `S` = String
- `Start` = Communication started / LED on
- `YB` = End of packet


## Behaviour check
- Check whether the format of the message packet is valud
- Check if it is for wheel subsystem
- Check destination if not

## Receiving messages

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
