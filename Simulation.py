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
nation_stats = {"china": 0, "usa": 0, "india": 0, "brazil": 0, "japan": 0, "total": 0}
never_offline = ["usa", "india"]


def arrival(environment, nation, arrival_rate):
    global client_id
    # keep track of client number client id
    # arrival will continue forever
    while True:
        nation_stats[nation] += 1
        nation_stats["total"] = client_id

        arrival_rate2 = arrival_function(env.now, nation, arrival_rate)
        inter_arrival = random.expovariate(lambd=arrival_rate2)

        # yield an event to the simulator
        yield environment.timeout(inter_arrival)

        # a new client arrived
        Client(environment, nation, client_id)
        client_id += 1


class Client(object):

    def __init__(self, environment, name_client="nations", client_id=0):
        self.env = environment
        self.nation = name_client
        self.client_id = client_id
        self.response_time = 0
        self.k = random.randint(1, 2)
        # the client is a "process"
        self.env.process(self.run())

    def run(self):
        # store the absolute arrival time
        time_arrival = self.env.now
        print("client", self.client_id, "from ", self.nation, "wants to make requests at", round(time_arrival, 5))
        print("client tot request: ", self.k)

        for j in range(1, self.k + 1):
            pack_dim = random.randint(8000, 16000)
            print("client", self.client_id, " request number : ", j)
            string = nearest_servers(self.nation)  # A string with sorted servers according to the distances
            print(string)
            i = 0
            # Try to find free servers if the closest one is already full
            while supreme_dict[string[i]]["count"] == MAX_CLIENT or supreme_dict[string[i]]["online"] is False:
                i += 1
                # If all the servers have been checked, then come back to the closest one and put the client in the queue
                if i == N_SERVERS:
                    i = 0
                    break
            supreme_dict[string[i]]["count"] += 1
            print("Server Chosen: ", string[i])
            print("Total Clients in the queue:", string[i], " : ", len(dictionary_of_server[string[i]].servers.queue))
            print("Total clients in server " + string[i] + " : " + str(supreme_dict[string[i]]["count"]-1))
            if supreme_dict[string[i]]["count"] == MAX_CLIENT - 1:
                for j in nearest_servers(string[i]):
                    if supreme_dict[j]["online"] is False:
                        supreme_dict[j]["online"] = True
                        print("Server", j, "went back online triggered by server", string[i])
                        supreme_dict[j]["last_update"] = self.env.now
                        break
            roundtrip = RTT(string[i], self.nation) / (3 * 10e5)  # Latency due to RTT
            latency = random.randint(10, 100) * 10e-3  # Latency of the server
            print("Latency to reach the server: ", round(latency+roundtrip, 5))
            yield self.env.timeout(roundtrip + latency)
            # The client goes to the first server to be served ,now is changed
            # until env.process is complete
            serve_customer = env.process(
                dictionary_of_server[string[i]].serve(self.nation, j, self.client_id, pack_dim))
            yield serve_customer
            supreme_dict[string[i]]["count"] -= 1

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
        # https://simpy.readthedocs.io/en/latest/simpy_intro/shared_resources.html

    def serve(self, name_client, req, client, pack_dim):

        # request a server
        with self.servers.request() as request:  # create obj then destroy
            yield request

            name_request = "client_" + str(client) + "_req_" + str(req)
            servers_arrival[self.name_server].succeed()
            servers_arrival[self.name_server] = self.env.event()
            now = self.env.now
            shared_capacity = self.capacity / self.servers.count
            service_time = pack_dim / shared_capacity
            print("shared capacity for", name_request, " : ", shared_capacity)
            print("service time for", name_request, " : ", service_time, "Request arrived at the server at: ", round(self.env.now, 5))
            supreme_dict[self.name_server]["current_requests"][name_request] = [service_time, shared_capacity, pack_dim,
                                                                                now]
            go = False
            while go is False:
                now = self.env.now
                new_supreme_dict = global_service_times(self.name_server, supreme_dict, name_request, now,
                                                        self.capacity / self.servers.count)
                supreme_dict[self.name_server]["current_requests"][name_request] = \
                new_supreme_dict[self.name_server]["current_requests"][name_request]
                service_time = supreme_dict[self.name_server]["current_requests"][name_request][0]

                yield self.env.timeout(service_time) | servers_arrival[self.name_server] | servers_departure[self.name_server]
                if round((self.env.now - now), 5) < round(service_time, 5):
                    print("A new client arrived or just went away, update needed for: ", name_request)
                else:
                    go = True
            print("The service time for client", name_request, "was ", round(service_time, 5))
            print("The client left the server in ", round(self.env.now - now, 5))

        servers_departure[self.name_server].succeed()
        servers_departure[self.name_server] = self.env.event()

        now = self.env.now
        supreme_dict[self.name_server]["tot_cost"] += evaluate_cost(supreme_dict[self.name_server]["last_update"], now,
                                                                    self.name_server)
        supreme_dict[self.name_server]["last_update"] = now
        del supreme_dict[self.name_server]["current_requests"][name_request]
        if self.servers.count == 0 and self.name_server not in never_offline:
            supreme_dict[self.name_server]["online"] = False
            print("Server", self.name_server, "went offline")


if __name__ == '__main__':
    supreme_dict = {"china": {"tot_cost": 0, "last_update": 0, "online": False, "count":0, "current_requests": {}},
                    "usa": {"tot_cost": 0, "last_update": 0, "online": True,"count":0, "current_requests": {}},
                    "india": {"tot_cost": 0, "last_update": 0, "online": True,"count":0, "current_requests": {}},
                    "japan": {"tot_cost": 0, "last_update": 0, "online": False,"count":0, "current_requests": {}},
                    "brazil": {"tot_cost": 0, "last_update": 0, "online": False,"count":0, "current_requests": {}}}
    arrival_nations = {"china": round(765367947 / total_users, 2), "usa": round(451347554 / total_users, 2),
                       "india": round(244090854 / total_users, 2),
                       "brazil": round(141206801 / total_users, 2), "japan": round(115845120 / total_users, 2)}
    client_id = 1
    random.seed(RANDOM_SEED)  # same sequence each time

    max_capacity = 10e4  # The same for each server
    response_time = []

    # create lambda clients
    # for i in range(1, lambd):
    env = simpy.Environment()
    stats = Statistics()
    # servers
    dictionary_of_server = {}
    for i in supreme_dict.keys():
        env.server = Servers(environment=env, max_client=MAX_CLIENT, capacity=max_capacity, name=i)
        dictionary_of_server[i] = env.server


    servers_arrival = {}
    servers_departure = {}
    for i in supreme_dict.keys():
        servers_arrival[i] = env.event()
        servers_departure[i] = env.event()

    # start the arrival process
    # technically, a process actually is an event. Example: process of parking a car.
    # https://simpy.readthedocs.io/en/latest/simpy_intro/process_interaction.html?highlight=process
    for i in supreme_dict.keys():
        env.process(arrival(environment=env, nation=i, arrival_rate=arrival_rate_global * arrival_nations[i]))
    # simulate until SIM_TIME
    env.run(until=SIM_TIME)  # the run process starts waiting for it to finish
    response_time.append(stats.mean())
    print(nation_stats)

# totally occupied servers in this case
# we need parallel servers for example 5 servers for 5 continents


