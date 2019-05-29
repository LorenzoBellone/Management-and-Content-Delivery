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
SIM_TIME = 60  # 24 for each day
total_users = 765367947 + 451347554 + 244090854 + 141206801 + 115845120
arrival_rate_global = 10  # 100%, and after will be used to define the rate of arrival of each country
nation_stats = {"china": 0, "usa": 0, "india": 0, "brazil": 0, "japan": 0, "total":0}

def arrival(environment, nation, arrival_rate):
    global client_id
    # keep track of client number client id
    # arrival will continue forever
    nation_timezone={"china":8*60*60, "usa":-(5*60*60),"india":5*60*60,"brazil":-3*60*60,"japan":9*60*60}
    global china
    global china_time
    china = []
    china_time = []
    while True:

        nation_stats[nation] += 1
        nation_stats["total"] = client_id

        if (env.now % 24*60*60) < (8*60*60+nation_timezone[nation]) or (env.now % 24*60*60 > (20*60*60+nation_timezone[nation])):
            arrival_rate2 = arrival_rate * 0.1
        else:
            arrival_rate2 = arrival_rate_global*arrival_rate

        inter_arrival = random.expovariate(lambd=arrival_rate2)
        print("arrival_rate : ", arrival_rate2)
        if nation == "china":
            china.append(arrival_rate2)
            china_time.append(env.now + nation_timezone["china"])

        # yield an event to the simulator
        yield environment.timeout(inter_arrival)

        # a new client arrived
        Client(environment, nation, client_id)
        client_id += 1

class Client(object):

    def __init__(self, environment, i="nations", client_id=0):
        self.env = environment
        self.nation = i
        self.client_id = client_id
        self.response_time = 0
        self.k = random.randint(10, 100)
        # the client is a "process"
        env.process(self.run())

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
            while dictionary_of_server[string[i]].servers.count == MAX_CLIENT:
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
            yield env.process(dictionary_of_server[string[i]].serve(pack_dim, self.nation))

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

    def serve(self, pack_dim, name_client):
        # request a server

        with self.servers.request() as request:  # create obj then destroy
            yield request

            shared_capacity = self.capacity / self.servers.count
            service_time = pack_dim / shared_capacity
            print("shared capacity: ", shared_capacity)
            print("service time: ", service_time)

            # server is free, wait until service is finish
            # Latency between 10 and 100 ms from the seconds.
            yield self.env.timeout(random.randint(10, 100)*(10e-3))
            # LAtency due to RTT
            yield self.env.timeout(RTT(self.name_server, name_client)/(3*10e8))
            # yield an event to the simulator
            yield self.env.timeout(service_time)


if __name__ == '__main__':
    nations = ["china", "usa", "india", "japan", "brazil"]
    arrival_nations = {"china": round(765367947 / total_users, 2), "usa": round(451347554 / total_users, 2),
               "india": round(244090854 / total_users, 2),
               "brazil": round(141206801 / total_users, 2), "japan": round(115845120 / total_users, 2)}
    client_id = 1
    random.seed(RANDOM_SEED)  # same sequence each time

    max_capacity = 5e5  # diverso per ogni server
    response_time = []

    # create lambda clients
    #for i in range(1, lambd):
    env = simpy.Environment()
    stats = Statistics()
    # servers
    dictionary_of_server = {}
    for i in nations:
        env.server = Servers(environment=env, max_client=MAX_CLIENT, capacity=max_capacity, name=i)
        dictionary_of_server[i] = env.server

    # start the arrival process
    env.process(arrival(environment=env, nation ="china", arrival_rate=arrival_rate_global*arrival_nations["china"]))
    # technically, a process actually is an event. Example: process of parking a car.
    # https://simpy.readthedocs.io/en/latest/simpy_intro/process_interaction.html?highlight=process
    env.process(arrival(environment=env, nation="usa", arrival_rate=arrival_rate_global*arrival_nations["usa"]))
    env.process(arrival(environment=env, nation="india", arrival_rate=arrival_rate_global*arrival_nations["india"]))
    env.process(arrival(environment=env, nation="brazil", arrival_rate=arrival_rate_global*arrival_nations["brazil"]))
    env.process(arrival(environment=env, nation="japan", arrival_rate=arrival_rate_global*arrival_nations["japan"]))
    # simulate until SIM_TIME
    env.run(until=SIM_TIME)  # the run process starts waiting for it to finish
    response_time.append(stats.mean())
    print(nation_stats)

    plt.plot(china_time, china)
    plt.grid()
    plt.xlim([0,SIM_TIME])
    plt.show()
# totally occupied servers in this case
# we need parallel servers for example 5 servers for 5 continents