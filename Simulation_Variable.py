import simpy
import numpy
import random
from runstats import Statistics
from Lab3.asset_variable import *

import matplotlib.pyplot as plt

# init
RANDOM_SEED = 1
MAX_CLIENT = 20  # max client per server
max_capacity = 10e12  # The same for each server in 10 Gbps
SIM_TIME = 70 # 24 for each day
total_users = 765367947 + 451347554 + 244090854 + 141206801 + 115845120
arrival_rate_global = 1  # 100%, and after will be used to define the rate of arrival of each country
nation_stats = {"china": 0, "usa": 0, "india": 0, "brazil": 0, "japan": 0, "total": 0}
never_offline = ["china1", "usa1", "india1", "brazil1", "japan1"]
total_costs = {"china": 0, "usa": 0, "india": 0, "brazil": 0, "japan": 0}


def arrival(environment, nation, arrival_rate):
    global client_id
    # keep track of client number client id
    # arrival will continue forever
    while True:

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
        self.k = random.randint(1, 10)
        # the client is a "process"
        self.env.process(self.run())

    def run(self):
        # store the absolute arrival time
        time_arrival = self.env.now
        # print("client", self.client_id, "from ", self.nation, "wants to make requests at", round(time_arrival, 5))
        print("client tot request: ", self.k)

        for j in range(1, self.k + 1):
            pack_dim = random.randint(8000, 16000)
            #print("client", self.client_id, " request number : ", j)
            close_nations = nearest_servers(self.nation)  # A list with sorted countries according to the distances
            string = [] # A list with sorted servers according to the country in which they are.
            for i in close_nations:
                for q in supreme_dict.keys():
                    if which_nation(q) == i:
                        string.append(q)
            #print(string)
            i = 0
            # Try to find free servers if the closest one is already full
            while supreme_dict[string[i]]["count"] >= MAX_CLIENT:
                i += 1
                # If all the servers have been checked, then come back to the closest one and put the client in the queue
                if i == len(supreme_dict.keys())-1:
                    i = 0
                    break
            supreme_dict[string[i]]["count"] += 1
            # print("Server Chosen: ", string[i])
            # print("Total Clients in the queue:", string[i], " : ", len(dictionary_of_server[string[i]].servers.queue))
            # print("Total clients in server " + string[i] + " : " + str(dictionary_of_server[string[i]].servers.count))
            # If a server is going to become full, then create a new server in the same country.
            if supreme_dict[string[i]]["count"] == MAX_CLIENT - 1:
                new_server = which_nation(string[i]) + str(int(which_id(string[i]))+1)
                if new_server not in supreme_dict.keys():
                    supreme_dict[new_server] = {"last_update": 0, "count": 0, "current_requests": {}}
                    env.server = Servers(environment=env, max_client=MAX_CLIENT, capacity=max_capacity, name=new_server)
                    servers_arrival[new_server] = env.event()
                    servers_departure[new_server] = env.event()
                    dictionary_of_server[new_server] = env.server
                    #print("A new server has been created!", new_server)
            # The request has a RTT to wait before arriving at the server
            roundtrip = RTT(which_nation(string[i]), self.nation) / (3 * 10e5)  # Latency due to RTT
            # print("RTT to reach the server: ", round(roundtrip, 5))
            yield self.env.timeout(roundtrip)
            # Wait until the request is served by the process serve_customer
            serve_customer = env.process(
                dictionary_of_server[string[i]].serve(j, self.client_id, pack_dim))
            yield serve_customer

        self.response_time = self.env.now - time_arrival
        nation_stats[self.nation] += 1
        nation_stats["total"] += 1
        #print("client", self.client_id, "from ", self.nation, "response time ", self.response_time)
        stats.push(self.response_time)
        stats_dict[self.nation].push(self.response_time)


class Servers(object):
    # constructor
    def __init__(self, environment, max_client, capacity, name):
        self.name_server = name
        self.env = environment
        self.capacity = capacity
        self.servers = simpy.Resource(env, capacity=max_client)
        # https://simpy.readthedocs.io/en/latest/simpy_intro/shared_resources.html

    def serve(self, req, client, pack_dim):

        # request a server
        with self.servers.request() as request:
            yield request # create obj then destroy
            latency = random.randint(1, 10) * 10e-3  # Latency of the server
            servers_arrival[self.name_server].succeed()
            servers_arrival[self.name_server] = self.env.event()

            name_request = "client_" + str(client) + "_req_" + str(req)
            now = self.env.now
            shared_capacity = self.capacity / self.servers.count
            service_time = pack_dim / shared_capacity
            # print("shared capacity for", name_request, " : ", shared_capacity)
            # print("service time for", name_request, " : ", service_time, "Request arrived at the server at: ", round(self.env.now, 10))
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

                b = servers_arrival[self.name_server]
                c = servers_departure[self.name_server]
                r = yield self.env.timeout(service_time) | b | c
                if b not in r and c not in r:
                    go = True
                # else:
                    # print("A new client arrived or just went away from server ", self.name_server, "update needed for: ", name_request)
            yield self.env.timeout(latency)
            # print("The client left the server in ", round(self.env.now - now, 10))

        supreme_dict[self.name_server]["count"] -= 1
        servers_departure[self.name_server].succeed()
        servers_departure[self.name_server] = self.env.event()

        del supreme_dict[self.name_server]["current_requests"][name_request]
        if supreme_dict[self.name_server]["count"] == 0 and self.name_server not in never_offline:
            now = self.env.now
            total_costs[which_nation(self.name_server)] += evaluate_cost(supreme_dict[self.name_server]["last_update"],
                                                                         now,
                                                                         which_nation(self.name_server))
            del supreme_dict[self.name_server]
            del dictionary_of_server[self.name_server]
            del servers_arrival[self.name_server]
            del servers_departure[self.name_server]
            # print("Server", self.name_server, "went offline")


if __name__ == '__main__':
    supreme_dict = {"china1": {"last_update": 0, "count":0, "current_requests": {}},
                    "usa1": {"last_update": 0, "count":0, "current_requests": {}},
                    "india1": {"last_update": 0, "count":0, "current_requests": {}},
                    "japan1": {"last_update": 0, "count":0, "current_requests": {}},
                    "brazil1": {"last_update": 0, "count":0, "current_requests": {}}}
    arrival_nations = {"china": round(765367947 / total_users, 2), "usa": round(451347554 / total_users, 2),
                       "india": round(244090854 / total_users, 2),
                       "brazil": round(141206801 / total_users, 2), "japan": round(115845120 / total_users, 2)}
    client_id = 1
    random.seed(RANDOM_SEED)  # same sequence each time

    env = simpy.Environment()
    stats = Statistics()
    stats_dict = {}
    for i in arrival_nations.keys():
        stats_dict[i] = Statistics()

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
    for i in arrival_nations.keys():
        env.process(arrival(environment=env, nation=i, arrival_rate=arrival_rate_global * arrival_nations[i]))
    # simulate until SIM_TIME

    env.run(until=SIM_TIME)  # the run process starts waiting for it to finish

    for i in supreme_dict.keys():
        total_costs[which_nation(i)] += evaluate_cost(supreme_dict[i]["last_update"], SIM_TIME, which_nation(i))

    avg_response = stats.mean()
    dictionary_stats_nation = {}
    for i in arrival_nations.keys():
        dictionary_stats_nation[i] = stats_dict[i].mean()
    print(nation_stats)

