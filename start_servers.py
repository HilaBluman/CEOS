import threading
import socket
from polling_server import start_polling_server
from main_server import start_main_server

def main():
    print()
    host = "192.168.68.56" 
    #host = socket.gethostbyname(socket.gethostname())

    # Create threads for both servers
    polling_thread = threading.Thread(target=start_polling_server, args=(host, 8001))
    main_thread = threading.Thread(target=start_main_server, args=(host, 8000))

    # Start the threads
    polling_thread.start()
    main_thread.start()


    # Optionally, wait for both threads to complete
    polling_thread.join()
    main_thread.join()

if __name__ == "__main__":
    main()