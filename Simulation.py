import simpy
import numpy
import random
from runstats import Statistics
from Lab3.asset import *

import matplotlib.pyplot as plt

# init
N_SERVERS = 5
RANDOM_SEED = 1
MAX_CLIENT = 5  # max client per server
SIM_TIME = 24  # 24 for each day
total_users = 765367947 + 451347554 + 244090854 + 141206801 + 115845120
arrival_rate_global = 10  # 100%, and after will be used to define the rate of arrival of each country
nation_stats = {"china": 0, "usa": 0, "india": 0, "brazil": 0, "japan": 0, "total":0}
never_offline = ["usa", "india"]

def arrival(environment, nation, arrival_rate):
    global client_id
    # keep track of client number client id
    # arrival will continue forever
    while True:

        nation_stats[nation] += 1
        nation_stats["total"] = client_id

        inter_arrival = random.expovariate(lambd=arrival_rate)

        # yield an event to the simulator
        yield environment.timeout(inter_arrival)

        # a new client arrived
        Client(environment, nation, client_id)
        client_id += 1

class Client(object):

    def __init__(self, environment, i ="nations", client_id = 0):
        self.env = environment
        self.nation = i
        self.client_id = client_id
        self.response_time = 0
        self.k = random.randint(1, 2)
        # the client is a "process"
        self.env.process(self.run())

    def run(self):
        # store the absolute arrival time
        time_arrival = self.env.now
        print("client", self.client_id, "from ", self.nation, "has arrived at", time_arrival)
        print("client tot request: ", self.k)

        for j in range(1, self.k+1):
            pack_dim = random.randint(8000, 16000)
            print("client", self.client_id, " request number : ", j)
            string = nearest_servers(self.nation)  # A string with sorted servers according to the distances
            print(string)
            i = 0
            # Try to find free servers if the closest one is already full
            while dictionary_of_server[string[i]].servers.count == MAX_CLIENT or supreme_dict[string[i]]["online"] is False:
                i += 1
                # If all the servers have been checked, then come back to the closest one and put the client in the queue
                if i == N_SERVERS:
                    i = 0
                    break
            print("Server Chosen: ", string[i])
            print("Total Clients in the queue:", string[i], " : ", len(dictionary_of_server[string[i]].servers.queue))
            print("Total clients in server " + string[i] + " : " + str(dictionary_of_server[string[i]].servers.count))
            # The client goes to the first server to be served ,now is changed
            # until env.process is complete
            yield env.process(dictionary_of_server[string[i]].serve(self.nation, j, self.client_id, pack_dim))

        self.response_time = self.env.now - time_arrival
        print("client", self.client_id, "from ", self.nation, "response time ", self.response_time)
        stats.push(self.response_time)


class Servers(object):
    # constructor
    def __init__(self, environment, max_client, capacity, name):
        self.name_server = name
        self.env = environment
        self.capacity = capacity
        self.servers = simpy.Resource(env, capacity=max_client)
        self.client_arrive = self.env.event()
        # https://simpy.readthedocs.io/en/latest/simpy_intro/shared_resources.html

    def serve(self, name_client, req, client, pack_dim):
        # request a server
        if self.servers.count == MAX_CLIENT - 1:
            for i in nearest_servers(self.name_server):
                if supreme_dict[i]["online"] is False:
                    supreme_dict[i]["online"] = True
                    print("Server", i, "went back online triggered by server", self.name_server)
                    supreme_dict[i]["last_update"] = self.env.now
                    break

        with self.servers.request() as request:  # create obj then destroy
            yield request

            name_request = "client_"+ str(client) +"_req_" + str(req)
            shared_capacity = self.capacity / self.servers.count
            roundtrip = RTT(self.name_server, name_client)/(3*10e5)     # Latency due to RTT
            latency = random.randint(10, 100)*10e-3       # Latency of the server
            yield self.env.timeout(roundtrip + latency)

            now = self.env.now
            service_time = pack_dim / shared_capacity
            print("shared capacity for", name_request, " : ", shared_capacity)
            print("service time for", name_request, " : ", service_time)
            supreme_dict[self.name_server]["current_requests"][name_request] = [service_time, shared_capacity, pack_dim, now]
            new_supreme_dict = global_service_times(self.name_server, supreme_dict, now, shared_capacity)
            for i in new_supreme_dict[self.name_server]["current_requests"].keys():
                supreme_dict[self.name_server]["current_requests"][i] = new_supreme_dict[self.name_server]["current_requests"][i]

            # yield an event to the simulator
            r = yield self.env.timeout(service_time)
            self.client_arrive.succeed()
        now = self.env.now
        supreme_dict[self.name_server]["tot_cost"] += evaluate_cost(supreme_dict[self.name_server]["last_update"], now, self.name_server)
        supreme_dict[self.name_server]["last_update"] = now
        del supreme_dict[self.name_server]["current_requests"][name_request]
        if self.servers.count == 0 and self.name_server not in never_offline:
            supreme_dict[self.name_server]["online"] = False
            print("Server", self.name_server, "went offline")


if __name__ == '__main__':
    supreme_dict = {"china":{"tot_cost": 0, "last_update":0, "online" : False , "current_requests":{}},
                    "usa":{"tot_cost": 0, "last_update":0,"online" : True , "current_requests":{}},
                    "india" : {"tot_cost": 0, "last_update":0,"online" : True , "current_requests":{}},
                    "japan": {"tot_cost": 0, "last_update":0,"online" : False , "current_requests":{}},
                    "brazil":{"tot_cost": 0, "last_update":0,"online" : False , "current_requests":{}}}
    arrival_nations = {"china": round(765367947 / total_users, 2), "usa": round(451347554 / total_users, 2),
               "india": round(244090854 / total_users, 2),
               "brazil": round(141206801 / total_users, 2), "japan": round(115845120 / total_users, 2)}
    client_id = 1
    random.seed(RANDOM_SEED)  # same sequence each time

    max_capacity = 10e4  # The same for each server
    response_time = []

    # create lambda clients
    #for i in range(1, lambd):
    env = simpy.Environment()
    stats = Statistics()
    # servers
    dictionary_of_server = {}
    for i in supreme_dict.keys():
        env.server = Servers(environment=env, max_client=MAX_CLIENT, capacity=max_capacity, name=i)
        dictionary_of_server[i] = env.server

    # start the arrival process

    # technically, a process actually is an event. Example: process of parking a car.
    # https://simpy.readthedocs.io/en/latest/simpy_intro/process_interaction.html?highlight=process
    for i in supreme_dict.keys():
        env.process(arrival(environment=env, nation =i, arrival_rate=arrival_rate_global*arrival_nations[i]))
    # simulate until SIM_TIME
    env.run(until=SIM_TIME)  # the run process starts waiting for it to finish
    response_time.append(stats.mean())
    print(nation_stats)
