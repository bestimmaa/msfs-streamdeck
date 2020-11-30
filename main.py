#!/usr/bin/env python3

#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

# Example script showing basic library usage - updating key images with new
# tiles generated at runtime, and responding to button state change events.

# TODO:


import os
import threading

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
from StreamDeck.Transport.Transport import TransportError
from SimConnect import *
import time
import sys

# Create SimConnect link
sm = SimConnect()
# Note the default _time is 2000 to be refreshed every 2 seconds
aq = AircraftRequests(sm, _time=2000)
ae = AircraftEvents(sm)

# Folder location of image assets used by this example.
ASSETS_PATH = os.path.join(os.getcwd(), "Assets")

# A mapping from identifiers to a button position - the id are equal to the SimConnect Variable name that is rendered per button.
# Keep in mind that the events have usually different identifiers.
# TODO: Add the following variables / events
# KEY_LANDING_LIGHTS_TOGGLE	LANDING_LIGHTS_TOGGLE	Toggle landing lights

key_index = {
    "AUTOPILOT_MASTER" : 0,
    "AUTOPILOT_VERTICAL_HOLD" : 4,
    "AUTOPILOT_HEADING_LOCK" : 2,
    "AUTOPILOT_ALTITUDE_LOCK" : 3,
    "AUTOPILOT_NAV1_LOCK" : 1,
    "AUTOPILOT_APPROACH_HOLD" : 5,
    "AUTOPILOT_YAW_DAMPER" : 6,
    "LIGHT_LANDING":7,
    "NAV_ACTIVE_FREQUENCY:1" : 11,
    "COM_ACTIVE_FREQUENCY:1" : 12,
    "GPS_ETE" : 13
}

# Variable to start / stop the UI update thread
update_ui_periodically = True

# Generates a custom tile with run-time generated text and custom image via the
# PIL module.
def render_key_image(deck, icon_filename, font_filename, label_text):
    # Resize the source image asset to best-fit the dimensions of a single key,
    # leaving a margin at the bottom so that we can draw the key title
    # afterwards.
    icon = Image.open(icon_filename)
    image = PILHelper.create_scaled_image(deck, icon, margins=[0, 0, 20 if len(label_text) > 0 else 0, 0])

    # Load a custom TrueType font and use it to overlay the key index, draw key
    # label onto the image.
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_filename, 14)
    label_w, label_h = draw.textsize(label_text, font=font)
    label_pos = ((image.width - label_w) // 2, image.height - 20)
    draw.text(label_pos, text=label_text, font=font, fill="white")

    return PILHelper.to_native_format(deck, image)

# Returns a button object with 2 states from a boolean SimConnect variable (e.g. AP Master)
# 
# variable: String, name of a SimConnect variable of type Bool to render, all spaces need to be replaced with underscores
# name: String, used for image lookup. NAME_on.png, NAME_off.png are used to display the state of the variable
def get_key_style_toggle(variable, name):
        v = 0.0 if aq.get(variable) == None else aq.get(variable)
        v =  v > 0.5 
        icon = "{}_on.png".format(name) if v else "{}_off.png".format(name)
        font = "Roboto-Regular.ttf"
        label = ""
        return {
            "name": name,
            "icon": os.path.join(os.path.join(ASSETS_PATH, "Icons"), icon),
            "font": os.path.join(os.path.join(ASSETS_PATH, "Fonts\\Roboto"), font),
            "label": label
        }

# Returns styling information for a key based on its position and state.
def get_key_style(deck, key, state):
    # Last button in the example application is the exit button.
    exit_key_index = deck.key_count() - 1
    # Default font to be overriden if needed
    font = "Roboto-Regular.ttf"

    if key == exit_key_index:
        name = "exit"
        icon = "{}.png".format("Exit")
        label = "Bye" if state else "Exit"
    elif key ==  key_index["AUTOPILOT_MASTER"]:
        return get_key_style_toggle("AUTOPILOT_MASTER","AP")
        
    elif key ==  key_index["AUTOPILOT_YAW_DAMPER"]:
        return get_key_style_toggle("AUTOPILOT_YAW_DAMPER","YD")

    elif key ==  key_index["AUTOPILOT_VERTICAL_HOLD"]:
        activated = 0.0 if aq.get("AUTOPILOT_VERTICAL_HOLD") == None else aq.get("AUTOPILOT_VERTICAL_HOLD")
        activated = activated < 1.0
        vs = 0.0 if aq.get("AUTOPILOT_VERTICAL_HOLD_VAR") == None else aq.get("AUTOPILOT_VERTICAL_HOLD_VAR")
        label = " " if vs > -5.0 and vs < 5.0 else "{:.0f} ft/min".format(vs)
        name = "VS"
        icon = "VS_off.png" if activated else "VS_on.png" 
    
    elif key ==  key_index["AUTOPILOT_HEADING_LOCK"]:
        activated = 0.0 if aq.get("AUTOPILOT_HEADING_LOCK") == None else aq.get("AUTOPILOT_HEADING_LOCK")
        activated = activated < 1.0
        hdg = 0.0 if aq.get("AUTOPILOT_HEADING_LOCK_DIR") == None else aq.get("AUTOPILOT_HEADING_LOCK_DIR")
        label = "{:.0f}°".format(hdg)
        name = "HDG"
        icon = "HDG_off.png" if activated else "HDG_on.png" 

    elif key ==  key_index["AUTOPILOT_ALTITUDE_LOCK"]:
        activated = 0.0 if aq.get("AUTOPILOT_ALTITUDE_LOCK") == None else aq.get("AUTOPILOT_ALTITUDE_LOCK")
        activated = activated < 1.0
        alt = 0.0 if aq.get("AUTOPILOT_ALTITUDE_LOCK_VAR") == None else aq.get("AUTOPILOT_ALTITUDE_LOCK_VAR")
        label = "{:.0f}ft".format(alt)
        name = "ALT"
        icon = "ALT_off.png" if activated else "ALT_on.png" 

    elif key ==  key_index["AUTOPILOT_NAV1_LOCK"]:
        return get_key_style_toggle("AUTOPILOT_NAV1_LOCK","NAV")

    elif key == key_index["GPS_ETE"]:
        ete = aq.get("GPS_ETE")
        display = "{:.0f}:{:02.0f}".format(ete/60,ete%60) if ete != None else "OFF"
        name = "ETE"
        icon = "ETE.png"
        label = display if state else display

    elif key == key_index["NAV_ACTIVE_FREQUENCY:1"]:
        freq = aq.get("NAV_ACTIVE_FREQUENCY:1")
        display = "{:02.2f}".format(freq) if freq != None else "OFF"
        name = "NAV1"
        icon = "NAV1.png"
        label = display if state else display

    elif key == key_index["COM_ACTIVE_FREQUENCY:1"]:
        freq = aq.get("COM_ACTIVE_FREQUENCY:1")
        display = "{:02.2f}".format(freq) if freq != None else "OFF"
        name = "COM1"
        icon = "COM.png"
        label = display if state else display    

    elif key ==  key_index["AUTOPILOT_APPROACH_HOLD"]:
        return get_key_style_toggle("AUTOPILOT_APPROACH_HOLD","APPR")

    elif key ==  key_index["LIGHT_LANDING"]:
        return get_key_style_toggle("LIGHT_LANDING","Land")
        
    else:
        name = "EMPTY"
        icon = "{}.png".format("Pressed" if state else "Released")
        label = ""
    return {
        "name": name,
        "icon": os.path.join(os.path.join(ASSETS_PATH, "Icons"), icon),
        "font": os.path.join(os.path.join(ASSETS_PATH, "Fonts\\Roboto"), font),
        "label": label
    }


# Creates a new key image based on the key index, style and current key state
# and updates the image on the StreamDeck.
def update_key_image(deck, key, state):
    # Determine what icon and label to use on the generated key.
    key_style = get_key_style(deck, key, state)

    # Generate the custom key with the requested image and label.
    image = render_key_image(deck, key_style["icon"], key_style["font"], key_style["label"])

    # Use a scoped-with on the deck to ensure we're the only thread using it
    # right now.
    with deck:
        try:
            # Update requested key with the generated image.
            deck.set_key_image(key, image)
        except TransportError:
            print("Unable to communicate with StreamDeck. This is expected when the application was shut down using the exit button.")
            sys.exit()


# Prints key state change information, updates rhe key image and performs any
# associated actions when a key is pressed.
def key_change_callback(deck, key, state):
    # Print new key state
    print("Deck {} Key {} = {}".format(deck.id(), key, state), flush=True)

    # Update the key image based on the new key state.
    update_key_image(deck, key, state)

    # Check if the key is changing to the pressed state.
    if state:
        key_style = get_key_style(deck, key, state)
        if key ==  key_index["AUTOPILOT_MASTER"]:
            event_to_trigger = ae.find("AP_MASTER")  # Toggles autopilot on or off
            event_to_trigger()    
        if key == key_index["AUTOPILOT_VERTICAL_HOLD"]:
            event_to_trigger = ae.find("AP_VS_HOLD")  # Toggles VS mode
            event_to_trigger()
        if key == key_index["AUTOPILOT_HEADING_LOCK"]:
            event_to_trigger = ae.find("AP_HDG_HOLD_ON")  # Toggles HDG mode
            event_to_trigger()   
        if key == key_index["AUTOPILOT_ALTITUDE_LOCK"]:
            event_to_trigger = ae.find("AP_PANEL_ALTITUDE_HOLD")  # Toggles ALT mode
            event_to_trigger() 
        if key == key_index["AUTOPILOT_NAV1_LOCK"]:
            event_to_trigger = ae.find("AP_NAV1_HOLD_ON")  # Toggles NAV mode
            event_to_trigger()   
        if key == key_index["AUTOPILOT_APPROACH_HOLD"]:
            event_to_trigger = ae.find("AP_APR_HOLD")  # Toggles APPR mode
            event_to_trigger()   
        if key == key_index["NAV_ACTIVE_FREQUENCY:1"]:
            event_to_trigger = ae.find("NAV1_RADIO_SWAP")  # Swap NAV1 standby / active frequency
            event_to_trigger()  
        if key == key_index["COM_ACTIVE_FREQUENCY:1"]:
            event_to_trigger = ae.find("COM_STBY_RADIO_SWAP")  # Swap COM1 standby / active frequency
            event_to_trigger()
        if key == key_index["AUTOPILOT_YAW_DAMPER"]:
            event_to_trigger = ae.find("YAW_DAMPER_TOGGLE")  # Toggle YD 
            event_to_trigger()
        if key == key_index["LIGHT_LANDING"]:
            event_to_trigger = ae.find("LANDING_LIGHTS_TOGGLE")  # Toggle landing lights
            event_to_trigger()
                    
        
        # When an exit button is pressed, close the application.
        if key_style["name"] == "exit":
            # Use a scoped-with on the deck to ensure we're the only thread
            # using it right now.
            with deck:
                # Reset deck, clearing all button images.
                deck.reset()
                # Close deck handle, terminating internal worker threads.
                deck.close()

def update_all_keys(deck):
    for key in range(deck.key_count()):
        update_key_image(deck, key, False)

def tick(deck):
    while update_ui_periodically:
        update_all_keys(deck)   
        time.sleep(1)    


if __name__ == "__main__":
    streamdecks = DeviceManager().enumerate()

    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))

    for index, deck in enumerate(streamdecks):
        deck.open()
        deck.reset()

        print("Opened '{}' device (serial number: '{}')".format(deck.deck_type(), deck.get_serial_number()))

        # Set initial screen brightness to 30%.
        deck.set_brightness(40)

        # Set initial key images.
        update_all_keys(deck)

        # Register callback function for when a key state changes.
        deck.set_key_callback(key_change_callback)

        thread = threading.Thread(target=tick, args=[deck] )
        thread.start()


        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed).
        for t in threading.enumerate():
            if t is threading.currentThread():
                continue

            if t.is_alive():
                t.join()