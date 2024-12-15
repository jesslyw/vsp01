import os

"""
The input_reader receives prompts from the user via a shell and performs according to the input.
This method is supposed to be started in a thread.
"""


class Input_Reader:
    def __init__(self, peerService, solService, model, message_service):
        self.peerService = peerService
        self.component = model
        self.message_service = message_service
        self.solService = solService
    

    def read_input(self):
            while True:
                try:
                    user_input = input("Command> ").strip()
                    if user_input.upper() == "EXIT":                        
                        if self.component.is_sol:
                            self.solService.unregister_all_peers_and_exit()
                        else:
                            self.peerService.send_exit_request()
                    elif user_input.upper() == "CRASH":
                        os.abort()

                    elif user_input.startswith("MESSAGE CREATE"):
                        # Nachrichten-Erstellungsprozess
                        self.create_message()
    
                    elif user_input.startswith("MESSAGE DELETE"):
                        # Nachrichten-Löschprozess
                        msg_id = user_input.split(" ", 2)[2]
                        self.delete_message(msg_id)
    
                    elif user_input.startswith("MESSAGE LIST"):
                        # Nachrichten anzeigen
                        self.list_messages()
    
                    elif user_input.startswith("MESSAGE GET"):
                        # Einzelne Nachricht anzeigen
                        msg_id = user_input.split(" ", 2)[2]
                        self.get_message(msg_id)
    
                    else:
                        print(
                            "Invalid command. Available commands: EXIT, CRASH, MESSAGE CREATE, MESSAGE DELETE <msg-id>, MESSAGE LIST, MESSAGE GET <msg-id>")

                except Exception as e:
                    print(f"Error while reading input: {e}")

    def create_message(self):
        """
        Handles the interactive creation of a message.
        """
        try:
            star_uuid = input("Enter STAR-UUID: ").strip()
            #origin = input("Enter Origin (COM-UUID or Email): ").strip()
            #sender = input("Enter Sender (COM-UUID or leave empty): ").strip()
            subject = input("Enter Subject: ").strip()
            message = input("Enter Message Body (can be empty): ").strip()

            # if not star_uuid or not origin or not subject:
            #     print("Missing required fields: STAR-UUID, Origin, or Subject.")
            #     return

            response = self.message_service.send_create_message_request(
                self.peerService.peer.sol_connection.ip,
                self.peerService.peer.sol_connection.port,
                self.peerService.peer.sol_connection.star_uuid,
                self.peerService.peer.com_uuid,
                self.peerService.peer.com_uuid, subject, message)
            if response:
                print(f"Message created successfully")
            else:
                print("Failed to create message.")
        except Exception as e:
            print(f"Error creating message: {e}")

    def delete_message(self, msg_id):
        """
        Handles the deletion of a message.
        """
        try:
            star_uuid = input("Enter STAR-UUID: ").strip()
            if not star_uuid:
                print("STAR-UUID is required.")
                return

            success = self.message_service.send_delete_message_request(
                self.peerService.peer.sol_connection.ip,
                self.peerService.peer.sol_connection.port,
                self.peerService.peer.sol_connection.star_uuid, msg_id)
            if success:
                print(f"Message {msg_id} deleted successfully.")
            else:
                print(f"Failed to delete message {msg_id}.")
        except Exception as e:
            print(f"Error deleting message: {e}")

    def list_messages(self):
        """
        Displays a list of messages based on scope and view.
        """
        try:
           # star_uuid = input("Enter STAR-UUID: ").strip()
            scope = input("Enter Scope (active, all): ").strip() or "active"
            view = input("Enter View (id, header): ").strip() or "id"

            messages = self.message_service.send_list_messages_request(
                            self.peerService.peer.sol_connection.ip,
                            self.peerService.peer.sol_connection.port,
                            self.peerService.peer.sol_connection.star_uuid,
                            scope,
                            view)
            print("Messages:")
            for message in messages:
                print(message)
        except Exception as e:
            print(f"Error listing messages: {e}")

    def get_message(self, msg_id):
        """
        Retrieves a single message based on the message ID.
        """
        try:
            star_uuid = input("Enter STAR-UUID: ").strip()
            if not star_uuid:
                print("STAR-UUID is required.")
                return

            message = self.message_service.send_get_message_request(
                    self.peerService.peer.sol_connection.ip,
                    self.peerService.peer.sol_connection.port,
                    msg_id,
                    star_uuid)
            if message:
                print("Message Details:")
                print(message)
            else:
                print(f"Message {msg_id} not found.")
        except Exception as e:
            print(f"Error retrieving message: {e}")
