import json
import socket
import threading
import select

import message


class Logic:
    # addresses are tuples like: [("127.0.0.2", 2000), ("127.0.0.3", 2000)]
    client_adresses = []

    server_ip = ""  # server ip
    server_port = 0  # server port
    server_socket = None
    server_message = None

    data = None
    running = False
    receive_thread = None

    @classmethod
    def __init__(cls):
        # server ip address & port
        cls.server_ip = "127.0.0.1"
        cls.server_port = 2001
        cls.data = None

        cls.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        cls.server_socket.bind((cls.server_ip, cls.server_port))
        cls.server_message = message.Message('Server')

        # clients addresses # 172.20.10.4 e.g.
        cls.client_adresses = []

        cls.running = False
        cls.receive_thread = threading.Thread(target=cls.receive_fct, args=(cls.server_socket,))

    @classmethod
    def server_start(cls):
        cls.running = True
        cls.send_to_clients()

    @classmethod
    def server_stop(cls):
        cls.running = False

    @classmethod
    def set_data(cls, data):
        cls.data = data

    @classmethod
    def send_to_clients(cls):
        try:
            cls.receive_thread = threading.Thread(target=cls.receive_fct)
            cls.receive_thread.start()
        except:
            print("TTT Error at starting Thread")
            return

        while True:
            if cls.data is not None:
                cls.message_clients(cls.data)

            if not cls.running:
                print("TTT Waiting for the thread to close...")
                cls.message_clients('Server has Quit!')
                cls.receive_thread.join()
                print("TTT Thread receive_thread closed")
                break

    @classmethod
    def message_clients(cls, message):
        # send clients the message
        for i in range(len(cls.client_adresses)):
            ip = cls.client_adresses[i][0]
            port = cls.client_adresses[i][1]
            cls.server_socket.sendto(bytes(message, encoding="ascii"), (ip, port))
        cls.data = None

    @classmethod
    def receive_fct(cls):
        counter = 0
        while cls.running:
            # Apelam la functia sistem IO -select- pentru a verifca daca socket-ul are date in bufferul de receptie
            # Stabilim un timeout de 1 secunda
            r, _, _ = select.select([cls.server_socket], [], [], 1)
            if not r:
                counter = counter + 1
            else:
                # server connects to clients as well when they send a message
                data, address = cls.server_socket.recvfrom(1024)
                print("Received", str(data), "from", address)

                # add client address when client sends to server
                if address not in cls.client_adresses:
                    cls.client_adresses.append(address)

                # process data
                cls.process_data(data, address)

                print("Counter = ", counter)

    @classmethod
    def process_data(cls, data, address):
        # data is of type packed_data
        """
        header_format - (81, 38, 255, 255, 0, 255)
        encoded_json - b'{"command": "hello"}'
        command - hello
        """
        header_format, encoded_json = cls.server_message.decode_message(data)
        command = json.loads(encoded_json)['command']
        print(command)

        # verify header format from data and do CoAP Codes
        cls.server_message.verify_format(header_format, command)

        # remove client address if message is 'Disconnected'
        if command == 'disconnect':
            cls.client_adresses.remove(address)
