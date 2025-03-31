import threading
from polling_server import start_polling_server
from main_server import start_main_server

def main():
    print()
    host = "172.20.10.9" #'192.168.1.110'
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