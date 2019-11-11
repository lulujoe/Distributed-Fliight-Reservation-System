import json
from socket import *
import ctypes
import os
import threading
from Dictionary import *
from Agent import *
import sys
import pickle
BUFFER_SIZE = 4096
quit_or_not = False

with open('knownhosts.json', 'r') as myfile:
    data = myfile.read()

siteInfo = json.loads(data)["hosts"]
nodes_ip_to_port = {}
siteid_to_ip = {}
ip_to_siteid = {}
siteid_to_index = {}
ip_list = []
siteid_list = []
port_list = []
for i, site in enumerate(siteInfo):
    ip_list.append(str(siteInfo[site]["ip_address"]))
    ip_to_siteid[str(siteInfo[site]["ip_address"])] = str(site)
    port_list.append(str(siteInfo[site]["udp_end_port"]))
    nodes_ip_to_port[str(siteInfo[site]["ip_address"])] = str(
        siteInfo[site]["udp_end_port"])
    siteid_to_ip[str(site)] = str(siteInfo[site]["ip_address"])
    siteid_to_index[str(site)] = i
    siteid_list.append(str(site))

#ip_to_siteid[current_ip]
current_siteid = sys.argv[1]
current_ip = siteInfo[current_siteid]["ip_address"]
HOST = current_ip
PORT = siteInfo[current_siteid]["udp_end_port"]
BUFFER_SIZE = 4096
UDP_socket = socket(AF_INET, SOCK_DGRAM)
UDP_server_address = (HOST, PORT)
UDP_socket.bind(UDP_server_address)


def recover(current_site_all_info):
    original_data = {}
    with open('logs.txt', 'rb') as file1:
        original_data["logs"] = pickle.load(file1)
    with open('FlightDictionary.txt', 'rb') as file2:
        original_data["FlightDictionary"] = pickle.load(file2)
    with open('timetable.txt', 'rb') as file3:
        original_data["timetable"] = pickle.load(file3)
    with open('userFlightInfo.txt', 'rb') as file4:
        original_data["userFlightInfo"] = pickle.load(file4)
    if len(original_data) > 0:
        current_site_all_info.import_data(original_data)


current_site_all_info = site_all_info(siteid_list, current_siteid)
if os.path.exists("logs.txt") and os.path.exists(
        'FlightDictionary.txt') and os.path.exists(
            'timetable.txt') and os.path.exists('userFlightInfo.txt'):
    recover(current_site_all_info)


def recv_msg_from_others():
    while quit_or_not == False:
        data, addr = UDP_socket.recvfrom(4096)

        if quit_or_not == True:
            break
        data = pickle.loads(data)[0]
        T, NP, index, userFlightInfo = data[0], data[1], data[2], data[3]
        current_site_all_info.UpdateAfterReceive(T, NP, index, userFlightInfo)

    #h here we handle the recv situation and update the log&&dictionay recod


UDP_listening_thread = threading.Thread(target=recv_msg_from_others)
UDP_listening_thread.start()
sys.stdout.flush()

while True:
    # print(str(current_siteid) + ' at your service!')
    command_input = input('')
    if 'reserve' in command_input:
        command_input_list = command_input.split()
        # corner case 1: customers need to input right number of inputs
        if len(command_input_list) != 3:
            print("Please input right number of inputs!")
            continue
        # corner case 2: one user can only appears once
        client_id = command_input_list[1]
        if client_id in current_site_all_info.userFlightInfo:
            print("One user can only make one reservation!")
            continue
        client_list_flight = command_input_list[2].split(',')
        for i in range(len(client_list_flight)):
            client_list_flight[i] = int(client_list_flight[i])

        current_site_all_info.reserve(client_id, client_list_flight)

    elif 'cancel' in command_input:
        # print("test case 1")
        command_input_list = command_input.split()
        client_id = command_input_list[1]
        current_site_all_info.delete(client_id)

    elif 'view' in command_input:
        current_site_all_info.view()

    elif 'log' in command_input:
        current_site_all_info.log()

    elif 'clock' in command_input:
        current_site_all_info.clock()

    elif 'smallsendall' in command_input:
        data = [current_site_all_info.smallSendAll()]
        data = pickle.dumps(data)
        for i in range(len(siteid_list)):
            reciever_id = siteid_list[i]
            reciever_ip = siteid_to_ip[reciever_id]
            reciever_port = int(siteInfo[reciever_id]["udp_end_port"])
            reciever_addr = (reciever_ip, reciever_port)
            UDP_socket.sendto(data, reciever_addr)

    elif 'smallsend' in command_input:
        command_input_list = command_input.split()
        reciever_id = command_input_list[1]
        if reciever_id in siteid_list:
            # print('get int to the seend function here.')
            reciever_ip = siteid_to_ip[reciever_id]
            reciever_port = int(siteInfo[reciever_id]["udp_end_port"])
            reciever_addr = (reciever_ip, reciever_port)

            data = [
                current_site_all_info.smallSend(siteid_to_index[reciever_id])
            ]
            data = pickle.dumps(data)
            value = UDP_socket.sendto(data, reciever_addr)
        else:
            print('We are sorry, this agent is currently closed.')

    elif 'sendall' in command_input:
        data = [current_site_all_info.MsgNeedSendAll()]
        data = pickle.dumps(data)
        for i in range(len(siteid_list)):
            reciever_id = siteid_list[i]
            reciever_ip = siteid_to_ip[reciever_id]
            reciever_port = int(siteInfo[reciever_id]["udp_end_port"])
            reciever_addr = (reciever_ip, reciever_port)
            UDP_socket.sendto(data, reciever_addr)

    elif 'send' in command_input:

        command_input_list = command_input.split()
        reciever_id = command_input_list[1]
        if reciever_id in siteid_list:
            # print('get int to the seend function here.')
            reciever_ip = siteid_to_ip[reciever_id]
            reciever_port = int(siteInfo[reciever_id]["udp_end_port"])
            reciever_addr = (reciever_ip, reciever_port)

            data = [
                current_site_all_info.MsgNeedSend(siteid_to_index[reciever_id])
            ]
            data = pickle.dumps(data)
            #print(reciever_addr)
            value = UDP_socket.sendto(data, reciever_addr)
            #print(value)
        else:
            print('We are sorry, this agent is currently closed.')

    elif 'quit' in command_input:

        quit_or_not = True
        data = 'quit'
        data = pickle.dumps(data)
        UDP_socket.sendto(data, UDP_server_address)
        break
    else:
        print('Please type valid command!')

UDP_socket.close()
