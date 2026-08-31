# CropSCOUT — from a class project to robot working

This repository is where CropSCOUT started: my individual datasheet for **EGR 314** at ASU Polytechnic, Spring 2026, as part of Team 202 — the Crop S.C.O.U.T.S.

The assignment was an exploration rover. Seven of us built one in four months. My subsystem was mobility: a custom PCB around an **ESP32-S3-WROOM-1** driving four DC motors, two LEDs and two buttons, handling daisy-chain UART and MQTT with the rest of the team's boards. Input takes anything from 5 V to 40 V, regulated to 3.3 V by an LM2596S-3.3 and to 5.5 V by an LM2575-5.5.

Everything below the fold — requirements, block diagram, component selection, BOM, schematic, PCB layout, the full subsystem API — is that class work, unchanged.

## What happened next

We showed the rover to farmers in Uzbekistan expecting notes on the electronics. They asked when they could buy one.

So we stopped guessing and asked properly. **We interviewed 30 farmers** in Jizzakh, Surkhandarya and Shakhrisabz — what they grow, what eats their time, what eats their money, and what they would actually pay for. The answers were blunt:

- **14 of 30** named weeding as the job that takes the most time. Spraying was second.
- **8 of the 29** who answered named spraying as their single largest cash cost in a season.
- **12 of 30** said seasonal labour is hard to find at all.
- Shown three concepts, **18 of 30** picked the universal platform — the biggest, most capable one — and rated it **4.5 out of 5**.

That last one changed the plan. We had designed a small rover; farmers kept asking for a bigger one that could do more than one job on the same base. The V2 CAD is being drawn around that.

The full results, including the answers that contradict our pitch, are published live at **[crop-scout.com/survey](https://crop-scout.com/survey/)** — every figure computed from the database as responses arrive.

## Where it lives now

| | |
|---|---|
| **[crop-scout.com](https://crop-scout.com)** | The robot: what it does, the interactive demo, the field research |
| **[bestarorg.uz](https://bestarorg.uz)** | The venture behind it, and our other projects |
| **[Presentation](https://www.canva.com/design/DAHR2F0Cv24/_gwUxZhiubCPhxlqnAkmqw/view)** | CropSCOUT deck |

CropSCOUT is backed by **UzCombinator**, Batch 2, 2026.

## Founders

**Asadbek Ruziev** — electronics. Robotics Engineering at ASU, El-Yurt Umidi scholar. CAN-bus, motor control, the boards.

**Asror Uralov** — mechanical. Chassis, arms and attachment systems in SolidWorks.

**Samandar** — manufacturing engineer

## The code

The mobility subsystem runs MicroPython on the ESP32-S3: MQTT over TLS for commands and telemetry, a UART daisy chain to the other boards, and closed-loop control of the four motors.

**[`Motor subsystem/`](https://github.com/mraruziev/Asadbek-EGR314/tree/main/Motor%20subsystem)** — `main.py` (633 lines), `config.py`, and the `mqtt_as` async client.

## Demo

[![CropSCOUT demo](https://img.youtube.com/vi/CgNYh9vksoY/hqdefault.jpg)](https://youtu.be/CgNYh9vksoY?si=Wh2rkczbTwafdUjh)

▶ **[Watch the demo](https://youtu.be/CgNYh9vksoY?si=Wh2rkczbTwafdUjh)**

## The datasheet

Live site: **[mraruziev.github.io/Asadbek-EGR314](https://mraruziev.github.io/Asadbek-EGR314/)**
Team 202 report: **[egr314-s-2026-202.github.io](https://egr314-s-2026-202.github.io/)**

Built with the rest of Team 202: Caleb Yuen, Cristopher Gutierrez, Jacob Alger, Aaron Kiem and Isaiah Johnston.
>>>>>>> d1ab0351fcce91105b6e6388854c63e64ff8db13
