import sys
import pickle
from Agent import *


class site_all_info(object):
    def __init__(self, sites, siteID):
        self.siteID = siteID
        self.siteindex = {}
        self.flightDict = {}
        self.userFlightInfo = {}
        self.logs = []
        self.timestamp = 0
        siteNum = len(sites)
        # transfer siteID to be numeric values so that we can find their position in the matrix
        for i, id in enumerate(sites):
            self.siteindex[id] = i
        self.matrix = [[0 for x in range(siteNum)] for y in range(siteNum)]

    # listodflight should be a list: ex.[1,3]
    def reserve(self, clientName, listofFlightNum):
        # increase timestamp
        self.timestamp += 1
        index = self.siteindex[self.siteID]
        # update the matrix
        self.matrix[index][index] = self.timestamp
        # insert reservation for the dictionary
        for flight in listofFlightNum:
            if flight not in self.flightDict:
                self.flightDict[flight] = []

            if len(self.flightDict[flight]) > 1:
                print("Cannot schedule reservation for %s." % (clientName))
                return False

        # create log for insert action
        curReservation = reservation(clientName, listofFlightNum)
        curLog = log("insert", curReservation, self.timestamp, index)
        self.logs.append(curLog)
        self.userFlightInfo[clientName] = listofFlightNum
        for flight in listofFlightNum:
            self.flightDict[flight].append((curLog, "pending"))

        self.record()
        print("Reservation submitted for %s." % (clientName))
        return True

    def delete(self, clientName):
        # print("test case 2")
        # increase timestamp
        self.timestamp += 1
        index = self.siteindex[self.siteID]
        # update the matrix
        self.matrix[index][index] = self.timestamp
        # create log for delete action
        if clientName not in self.userFlightInfo:
            print("Output a wrong userName that is not in out database!")
            return False
        listofFlightNum = self.userFlightInfo[clientName]
        curReservation = reservation(clientName, listofFlightNum)
        curLog = log("delete", curReservation, self.timestamp, index)
        self.logs.append(curLog)
        # delete reservation for the dictionary
        for flight in listofFlightNum:
            if flight not in self.flightDict:
                continue

            # find our target seats need to be deleted and then delete
            for client, status in self.flightDict[flight]:
                if client.reservation.clientName != clientName:
                    continue
                self.flightDict[flight].remove((client, status))
        self.record()
        print("Reservation for " + str(clientName) + " cancelled.")
        return True

    def hasRec(self, eR, targetSite, matrix):
        return matrix[targetSite][eR.siteIndex] >= eR.timestamp

    def sendAllHelper(self, eR):
        for i in range(len(self.matrix[0])):
            if eR.siteIndex != i:
                continue
            if eR.timestamp > self.smallestCol(self.matrix, i):
                return True
            else:
                return False
        print("Warning: cannot find siteID!")
        return False

    # return two values (Ti, NP) which can be used for UDP communication
    def MsgNeedSend(self, targetSite):
        index = self.siteindex[self.siteID]
        msgThinkNeed = [
            i for i in self.logs
            if self.hasRec(i, targetSite, self.matrix) == False
        ]
        return self.matrix, msgThinkNeed, index, self.userFlightInfo

    def MsgNeedSendAll(self):
        index = self.siteindex[self.siteID]
        msgThinkNeed = [i for i in self.logs if self.sendAllHelper(i) == True]
        return self.matrix, msgThinkNeed, index, self.userFlightInfo

    def smallSend(self, targetSite):
        index = self.siteindex[self.siteID]
        recordSend = self.matrix[index]
        msgThinkNeed = [
            i for i in self.logs
            if self.hasRec(i, targetSite, self.matrix) == False
        ]

        return [recordSend], msgThinkNeed, index, self.userFlightInfo

    def smallSendAll(self):
        index = self.siteindex[self.siteID]
        recordSend = self.matrix[index]
        msgThinkNeed = [i for i in self.logs if self.sendAllHelper(i) == True]
        return [recordSend], msgThinkNeed, index, self.userFlightInfo

    def UpdateAfterReceive(self, T, NP, indexJ, userFlightInfo):
        siteNum = len(self.matrix)
        if len(T) == 1:
            tempMatrix = [[0 for x in range(siteNum)] for y in range(siteNum)]
            tempMatrix[indexJ] = T[0]
            T = tempMatrix

        index = self.siteindex[self.siteID]
        self.userFlightInfo.update(userFlightInfo)
        msgTrueNeed = [
            i for i in NP if self.hasRec(i, index, self.matrix) == False
        ]
        userPending = {}
        for msgLog in msgTrueNeed:
            name = msgLog.reservation.clientName
            if msgLog.operatingType == "insert":
                # if find insert same user many times, output warning message
                if name in userPending:
                    print(
                        "Warning: weird thing happened! you insert same user again!"
                    )
                userPending[name] = (msgLog.reservation.listofFlightNum,
                                     msgLog)
            elif msgLog.operatingType == "delete":
                userPending[name] = ([], msgLog)
            else:
                print(
                    "Error: operatingType should not have other type other than insert and delte!"
                )

        for flight in self.flightDict:
            for userLog, status in self.flightDict[flight]:
                if status == "confirmed":
                    continue
                userPending[userLog.reservation.clientName] = (
                    userLog.reservation.listofFlightNum, userLog)

        flightPending = self.checkFlightPos(userPending)

        # update time matrix
        for i in range(len(self.matrix[index])):
            self.matrix[index][i] = max(self.matrix[index][i], T[indexJ][i])

        for i in range(len(self.matrix)):
            for j in range(len(self.matrix[0])):
                self.matrix[i][j] = max(self.matrix[i][j], T[i][j])

        # update partial log
        self.logs = self.logs + msgTrueNeed
        self.logs = [
            log for log in self.logs
            if log.timestamp > self.smallestCol(self.matrix, log.siteIndex)
        ]

        # update the dictionary
        # add all pending log into out dictionary
        for flight in flightPending:
            if flight not in self.flightDict:
                self.flightDict[flight] = []
            for log in flightPending[flight]:
                count = 0
                for records, status in self.flightDict[flight]:
                    if records == log:
                        count += 1
                if count == 0:
                    self.flightDict[flight].append((log, "pending"))

        for users in userPending:
            # we should ignore users who have been inserted and then deleted
            if userPending[users][0] == []:
                continue
            # if we find user is not in the confirmed list, then delete it
            if not self.checkUserComfirmed(userPending, users, flightPending):
                self.delete(users)
                continue
            # if we can prove that this user has the highest priority, then we can change its status to be confirmed
            if userPending[users][1].timestamp <= min(self.matrix[index]):
                for flight in userPending[users][0]:
                    for log, status in self.flightDict[flight]:
                        if log.reservation.clientName == users:
                            self.flightDict[flight].remove((log, status))
                            self.flightDict[flight].append((log, "confirmed"))
        self.record()
        return True

    def smallestCol(self, matrix, col):
        minValue = sys.maxsize
        for i in range(len(matrix)):
            if matrix[i][col] < minValue:
                minValue = matrix[i][col]

        return minValue

    def checkUserComfirmed(self, userPending, users, flightPending):
        for flight in userPending[users][0]:
            if len(flightPending[flight]) == 0:
                return False
            count = 0
            for log in flightPending[flight]:
                if log.reservation.clientName == users:
                    count += 1
            # count variable is used to judge whether certain user is in the confiirmed list
            if count == 0:
                return False

        return True

    def checkFlightPos(self, userPending):
        # for all users' pending flight, we record these information in a new dictionary (flightPending)
        flightPending = {}
        for users in userPending:
            for flight in userPending[users][0]:
                logRecord = userPending[users][1]
                remainedSeat = 2
                if flight in self.flightDict:
                    for info in self.flightDict[flight]:
                        if info[1] == "confirmed":
                            remainedSeat -= 1

                if remainedSeat == 0:
                    flightPending[flight] = []
                elif remainedSeat == 1:
                    if flight not in flightPending:
                        flightPending[flight] = [logRecord]
                    else:
                        oldLog = flightPending[flight][0]
                        if self.compareLog(logRecord, oldLog):
                            flightPending[flight] = [logRecord]
                elif remainedSeat == 2:
                    if flight not in flightPending:
                        flightPending[flight] = [logRecord]
                    elif len(flightPending[flight]) == 1:
                        oldLog = flightPending[flight][0]
                        if self.compareLog(logRecord, oldLog):
                            flightPending[flight] = [logRecord, oldLog]
                        else:
                            flightPending[flight] = [oldLog, logRecord]
                    elif len(flightPending[flight]) == 2:
                        firstLog = flightPending[flight][0]
                        secondLog = flightPending[flight][1]
                        if self.compareLog(logRecord, firstLog):
                            flightPending[flight] = [logRecord, firstLog]
                        elif self.compareLog(logRecord, secondLog):
                            flightPending[flight] = [firstLog, logRecord]
                    else:
                        print("Warning: length of flightPending is incorrect!")
                else:
                    print("Warning: remainedSeat Number is incorrect!")
        return flightPending

    def compareLog(self, log1, log2):
        if log1.timestamp < log2.timestamp:
            return True
        elif log1.timestamp == log2.timestamp:
            return log1.reservation.clientName < log2.reservation.clientName
        else:
            return False

    def quickSort2(self, nums, left, right):
        def partition(nums, left, right):
            pivot = nums[left]
            while left < right:
                while left < right and nums[right] >= pivot:
                    right -= 1
                nums[left] = nums[right]
                while left < right and nums[left] <= pivot:
                    left += 1
                nums[right] = nums[left]
            nums[left] = pivot
            return left

        if left < right:
            pivotIndex = partition(nums, left, right)
            self.quickSort2(nums, left, pivotIndex - 1)
            self.quickSort2(nums, pivotIndex + 1, right)

        return nums

    def view(self):
        userSet = set()
        for flight in self.flightDict:
            for userLog, status in self.flightDict[flight]:
                userSet.add((userLog.reservation.clientName, status))

        userSet = list(userSet)
        userSet = self.quickSort2(userSet, 0, len(userSet) - 1)
        for user in userSet:
            output = user[0] + " "
            flights = self.userFlightInfo[user[0]]
            for i in range(len(flights)):
                if i == 0:
                    output += str(flights[i])
                    continue
                output += ","
                output += str(flights[i])
            output += " %s" % (user[1])
            print(output)

    def log(self):
        for log in self.logs:
            output = "%s %s " % (log.operatingType, log.reservation.clientName)
            if log.operatingType == "insert":
                for i in range(len(log.reservation.listofFlightNum)):
                    if i == 0:
                        output += str(log.reservation.listofFlightNum[i])
                        continue
                    output += ",%s" % (str(log.reservation.listofFlightNum[i]))
            print(output)

    def clock(self):
        for i in range(len(self.matrix)):
            output = ""
            for j in range(len(self.matrix[0])):
                if j == 0:
                    output += str(self.matrix[i][j])
                    continue
                output += " %s" % (str(self.matrix[i][j]))
            print(output)

    def import_data(self, original_data):
        index = self.siteindex[self.siteID]
        self.logs = original_data["logs"]
        self.matrix = original_data["timetable"]
        self.flightDict = original_data["FlightDictionary"]
        self.userFlightInfo = original_data["userFlightInfo"]
        self.timestamp = self.matrix[index][index]

    def record(self):
        with open('logs.txt', 'wb') as file1:
            pickle.dump(self.logs, file1)
        with open('FlightDictionary.txt', 'wb') as file2:
            pickle.dump(self.flightDict, file2)
        with open('timetable.txt', 'wb') as file3:
            pickle.dump(self.matrix, file3)
        with open('userFlightInfo.txt', 'wb') as file4:
            pickle.dump(self.userFlightInfo, file4)
