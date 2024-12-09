import os
import sys
import threading
from utils.logger import global_logger
"""
The input_reader receives prompts from the user via a shell and performs according to the input.
This method is supposed to be started in a thread.
"""


class Input_Reader:

    def __init__(self, peerService, model, shutdown_event):
        self.peerService = peerService
        self.component = model
        self.solService = None
        self.shutdown_event = shutdown_event
    

    def read_input(self):

            while not self.shutdown_event.is_set(): 
                try:
                    print("Waiting for user input...")
                    user_input = input()
                    print("After waiting for user input...")
                    if user_input == "EXIT":
                        self.peerService.send_exit_request()
                        if self.component.is_sol:
                            pass
                        else:
                            self.peerService.send_exit_request()
                        os.abort()
                    elif user_input == "CRASH":
                        os.abort()
                    else:
                        print("Not a valid prompt.")
                except Exception as e:
                    print(f"Error while reading input: {e}")

            global_logger.info("event set - exiting input reader")
            sys.exit(0)    


