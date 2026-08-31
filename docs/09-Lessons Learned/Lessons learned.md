---
title: Module Lessons
---

### Overview


## Module success 
Our project was successful, with most of our planned project requirements being met. We were able to move the wheels, the 3DoF front arm, get temperature and humidity readings, as well as the metal detector. While there were some issues during the daisy chain, our project worked most of the time. The rover was working well for 5 hours during the Innovation Showcase, and there was nothing that blew up.


## Lessons learned

1. I learned that UART TX0 and RX0 are not the best pins for the UART connection, and this caused many issues with my motor's movement, as my motors move freely without the daisy chain, but when I receive commands from HMI through MQTT, my motor faces issues by being locked up.

2. I learned a lot about the importance of showing up to classes and team meetings and being able to take notes.

3. I learned importance of starting to work on PCB early, as well as double and triple checking PCB design, was very important for me, but I started working on my PCB 2 days before the deadline, so it is a big lesson for me for future projects.

4. I learned to order components early and coordinate with your teammates and professor to choose good motors if you are running 4 wheels. We ordered wheels from Amazon, and they were not delivered on time, even though the planned delivery date was before the Innovation Showcase.

5. I learned that I need to spend enough time outside of this class. Make sure to attend meetings and come to every class on time. Participation and communication in team meetings are highly important and valuable, helping you stay on track to complete tasks and finish the subsystem.

6. 3D printing or machining your design/frame to include your PCBs and electronics would be very professional and helpful to showcase your concept design more clearly.

7. I learned importance of starting to work on PCB early, as well as double and triple checking PCB design, was very important for me, but I started working on my PCB 2 days before the deadline, so it is a big lesson for me for future projects.

8. Learning coding on Python and VS Code and reviewing slides from EGR 219 is crucial. This class is very coding-heavy and those skills are crucial for the career too.

9. I learned that putting components in proper way on the PCB is crucial. I put my barrel jack right next to my voltage regulator and it was hard to connect wires.

10. It is important to update the datasheet website as you go. Try to write changes to the website as you go. This helps to keep up with assignments and to keep up with the design review.


## Recommendations for future students

1. Read the lab manual and resources for the lab thoroughly. The links provided to you are very helpful to get started on working with your subsystem. Try to read at least part of a website every day, since they have helpful information you need, like voltage regulators, ESP32 setup, MQTT, timers, sensors, etc.

2. Start labs early. This would be very helpful as you would have an idea of what you are doing instead of rushing through getting checked off. 

3. Asks questions from TAs and attends office hours. TAs have taken this class, and they have troubleshooted issues with their PCB and coding, so get feedback from them.

4. Make sure to include twice more components from Digikey than you actually need for your PCB. You might need to resolder few components for your PCB and having extra parts like LEDs, buttons, motor drivers is crucial.

5. Learn surface mount soldering by practising on cheap boards from Amazon. That way you will be well prepapred before your PCB arrives.

## Microcontroller/Module Startup Tip
I would suggest uploading MicroPython to your ESP32 before connecting and programming. This would troubleshoot any potential issues you might face when connecting to your ESP32.

