class reservation(object):
    def __init__(self, clientName, listofFlightNum):
        self.clientName = clientName
        self.listofFlightNum = listofFlightNum


class log(object):
    def __init__(self, operatingType, reservation, timestamp, siteIndex):
        self.operatingType = operatingType
        self.reservation = reservation
        self.timestamp = timestamp
        self.siteIndex = siteIndex
