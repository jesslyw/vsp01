
class SolManager:
    def __init__(self, sol_service):

        self.sol_service = sol_service


    def manage(self):

        #setting up a thread to listen for Hello?-messages
        self.sol_service.listen_for_hello()
