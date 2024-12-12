import os
import sys
import threading
from utils.logger import global_logger
"""
The input_reader receives prompts from the user via a shell and performs according to the input.
This method is supposed to be started in a thread.
"""


class Input_Reader:

    def __init__(self, peerService, solService, model):
        self.peerService = peerService
        self.component = model
        self.solService = solService
    

    def read_input(self):
            while True:
                try:
                    print("Waiting for user input...")
                    user_input = input()
                    print("After waiting for user input...")
                    if user_input == "EXIT":                        
                        if self.component.is_sol:
                            self.solService.unregister_all_peers_and_exit()
                        else:
                            self.peerService.send_exit_request()
                    elif user_input == "CRASH":
                        os.abort()
                    else:
                        print("Not a valid prompt.")
                except Exception as e:
                    print(f"Error while reading input: {e}")




