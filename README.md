# Distributed-Fliight-Reservation-System
A course project, which simulates a tiny airline system with 20 flights. 
Distributed algorithms are applied to ensure the reservations from different systems valid even in an unreliable network with communication failures.

## Main Task:
- Designed and implemented a flight reservation system on Docker containers with a crash tolerant design.
- Utilized both Wuu-Bernstein replicated log and dictionary Algorithm and Paxos Algorithm.
- Used multithreaded UDP sockets for network communication.

## Work distribution
- **Enzhe Lu** is responsible for core algorithm design( how to solve the conflicts and pending status), data structure design and implementation, Dictionay.py file, and all the specific function, such as reserve, delete, MsgNeedSend, UpdateAfterReceive implementation, debugging and recovery method.
- **Maida Wu** is responsible for core algorithm design( how to solve the conflicts and pending status), network build(UDP socket, receive, send), multi-threading creating and quit, Interface for object class and input command and report writing.

## File Designation:
- Agent.py:
Defines reservation class and log class, both of them don’t have any membership function and only act as an import module for Dictionary class.
- Dictionary.py:
Defines the core class, site_all_info for this project, all of our operation, such as insert, delete, view, log are treated as membership function of our object class, site_all_info. Besides, site_all_info includes all the data structure we need for this implementation, such as logs, timestamp, sited, etc.
- main.py:
This file provides all the interface we need between the object class site_all_info and the user command on the shell, besides it reads all the information we need from the known host.json file and build up the UDP socket for the present using container. A thread was created for each container as the listening port.

## Detailed Implementation
Our project use one UDP socket for each agent as a listen socket, a receive and send socket at the same time. Multi-threading programming was used as a way to handle the listening and executing the user input command at the same time. Another Thread was created as a way to check if there is any failure or quit at other agent. This was achieved by sending message to all agent in the siteid_list at a constant frequency consecutively. If there is a send failure at any agent, we would know that this agent encounter a failure or it is closed currently.
Our whole design of this project is object orientation style, so all the input command we get from the user at each agent would be treated as a related member function of our class site_all_info, all the information, add, delete, look up and change can be completed within this class.

### Data structure
1. **flightDict** *( {1: [(log, status),(log2, status)], 2: [(log, status)]} )* : a dictionary of tuples including both reservation and status information. SiteID is the key of dictionary. For every site, there are at most two seats, so we use list to save the snapshots at any moment and we keep checking the length of each list not larger than 2.
2. **logs** *( [log1,log2,log3] )*: a list of log variables
3. **Matrix** *( [[0,0,0],[1,2,2],[1,0,0] )*: a 2D matrix which composed of nested lists.

### Reserve
Once we call the reserve function which indicates that there is a client trying to make a reservation, we first update the timestamp and matrix clock. Then check our dictionary of the flight. If the seat has been reserved before, the reservation request is denied, else we treat this reservation as a pending status, because we haven’t got enough information we need to definitely decide the status of this reservation yet. (which would be explained in details in the following context)

### Delete
Once the user type in the cancel command we call this delete function. Delete function won’t encounter so much conflicts, because we only need to check if the reservation the user want to cancel exist. If it is, then delete it immediately in our dictionary. Else, the user id isn’t in our dictionary which indicates that he has never made a reservation before or he has made reservation before but it is at another agent and that information hasn’t been updated to this agent yet.

### MsgNeedSend/MsgNeedSendAll
This function decides which part of the information in our matrix clock, log and dictionary can be sent and it follows the principle of wuu-Berstein algorithm. For MsgNeedSend function, we use hasRec function to judge whether weneed to send certain message. For MsgNeedSendAll function, we calculate minimum value of a certain column. If we think any site doesn’t receive that, we will send it to all sites.

### SmallSend/SmallSendAll
Basically smallSend/smallSendAll use the same method as MsgNeedSend/MsgNeedSendAll.The only difference is we just send a certain line (line represent that site) to our target site. The problem of that is we will include more logs than logs we should according to our timetable. But we don’t think it will cause serious problem and after receiving messages from all sites, our logs will totally match with our timetable.

### UpdateAfterRecieve
Each time after relieve the message from another agent, there are several things to be done. First is to update our log, dictionary and matrix clock according to the wuu-Berstein algorithm. We will then calculate the rest seat of each site. For example, if a site has one user confirmed, then the rest seat is 1. We sort all pending users and select top1(if rest seats has 2, we will select top 2). If user is not in that list, we will delete the user immediately. If we find the timestamp of certain user reservation(site i) is less than the minimum time of row i (which means we get all info that we need), we will transform it from “pending” to “confirmed”. Also, we will delete all logs (from site i) with timestamp less than minimum time value of a column i.
All the other function, smallestCol, checkUserConfirmed, checkFlightsPos are served as helper function for this UpdateAfterRecieve function.

## Conflicts handling
The way we solved the several user reserving the same flight seat at the same time is stated as followed in detail. Once a user make a reservation on a flight seat, it comes into pending status.( if there is no one make a reservation according to our local record). The only way we can end this pending status into confirmation or cancellation is to get the information from all the other agent, which means that every other agent have at least send one message to our present agent after we made that reservation. Then we check the matrix clock, for example, we may assume that we are agent No.2 and we need to check the second row of the matrix clock, if matrix(1,1) is the smallest one in that row, which indicates that we have know all other agents’ information and the timestamp of all other agents is at least as large as our present agent.
Then we can decide which user can get this reservation according to the lexicographically order. All the other user who can’t get the confirmation get a cancel in the end. In this way, we handle the conflicts and finally end the pending status into a confirmation status.

## Failure handing
From the beginning, once we initialize the log, dictionary and matrix clock, we build several txt file as the back up of the information and save them at the present working directory. Once we update the log, dictionary and matrix clock, we make the corresponding changes to our txt back up file. If we encounter a failure and the agent is gone. All the data on the stack will be lost. But all the txt back up file is still there. We can ‘restart’ that agent and reload the txt file as our log, dictionary and matrix.

## Code testing
Code was tested in different containers and each of them has their own IP address. Local files were copied into the different container bin and we assign them the related IP address in the knownhost.json file, build the name and use the port number in the json file to test our code.
Failure and message lost are tested by shutdown the container shell and re-enter it again, simulating the agent failure.


