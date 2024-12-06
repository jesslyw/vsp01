import os

"""
The input_reader receives prompts from the user via a shell and performs according to the input.
This method is supposed to be started in a thread.
"""


class Input_Reader:

    def __init__(self, peerService, model):
        self.peerService = peerService
        self.component = model
        self.solService = None

    def read_input(self):

        while True:
            try:
                user_input = input()
                match user_input:
                    case "EXIT":
                        # TODO disconnect from star
                        if self.component.is_sol:
                            pass
                        else:
                            self.peerService.send_exit_request()
                        os.abort()
                    case "CRASH":
                        os.abort()
                    case _:
                        print("Not a valid prompt.")
            except Exception as e:
                print(f"Error while reading input: {e}")
