# msfs-streamdeck
A python application to turn the Elgato Stream Deck into a Flight Simulator interface.


![alt text](https://github.com/bestimmaa/msfs-streamdeck/blob/bestimmaa-patch-1/IMG_2775.png?raw=true "Stream Deck with AP controls")

This python app is basically an extended version of python-elgato-streamdeck sample. It includes a variety of buttons that interact with and display information from the auto pilot using SimConnect. It also includes icons for different AP functions and other information. The icons are created from the excellent template provided by https://fsresources.weebly.com/stream-deck-templates.html


## Dependencies

Make sure to use Python3 on Windows and install the following modules before running the application

[python-elgato-streamdeck](https://github.com/abcminiuser/python-elgato-streamdeck) 

    pip install streamdeck
    
[Python-SimConnect](https://github.com/odwdinc/Python-SimConnect)

    pip install SimConnect

## Run

Run the application after launching MSFS

    python main.py
