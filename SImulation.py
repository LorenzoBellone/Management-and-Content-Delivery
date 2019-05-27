import simpy
import numpy
import random
from runstats import Statistics
import matplotlib.pyplot as plt

RANDOM_SEED = 1
MAX_CLIENT = 5  # max client per server
SIM_TIME = 2
total_users = 765367947 + 451347554 + 244090854 + 141206801 + 115845120
nations = {"china": round(765367947/total_users, 2), "usa": round(451347554/total_users, 2), "india": round(244090854/total_users, 2),
           "brazil": round(141206801/total_users, 2), "japan": round(115845120/total_users, 2)}
arrival_rate_global = 100  # 100%, and after will be used to define the rate of arrival of each country
nation_stats = {"china": 0, "usa": 0, "india": 0, "brazil": 0, "japan": 0, "total":0}

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
        client_id += 1
        Client(environment, nation, client_id)


def nearest_server(id):
    return id

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
        if self.nation == "china":
            print("client", self.client_id, "from ", self.nation, "has arrived at", time_arrival)
            print("client tot request: ", self.k)

        for j in range(1, self.k+1):
            pack_dim = round(random.expovariate(lambd=0.001))
            if self.nation == "china":
                print("client", self.client_id, " from ", self.nation, " request number : ", j)
            # The client goes to the first server to be served ,now is changed
            # until env.process is complete
            string = nearest_server(self.nation)
            if string == "china":
                print("Total Clients in the queue:", string, " : ", len(dictionary_of_server[string].servers.queue))
                print("Total clients in server " + string + " : " + str(dictionary_of_server[string].servers.count))
            yield env.process(dictionary_of_server[string].serve(pack_dim))

        self.response_time = self.env.now - time_arrival
        if string == "china":
            print("client", self.client_id, "from ", self.nation, "response time ", self.response_time)
        stats.push(self.response_time)


class Servers(object):
    # constructor
    def __init__(self, environment, max_client, capacity, name):
        self.name = name
        self.env = environment
        self.capacity = capacity
        self.servers = simpy.Resource(env, capacity=max_client)  # https://simpy.readthedocs.io/en/latest/simpy_intro/shared_resources.html

    def serve(self, pack_dim):
        # request a server

        with self.servers.request() as request:  # create obj then destroy
            yield request
            shared_capacity = self.capacity / self.servers.count
            service_time = pack_dim / shared_capacity
            if self.name == "china":
                print("shared capacity: ", shared_capacity)
                print("service time: ", service_time)

            # server is free, wait until service is finish

            # yield an event to the simulator
            yield self.env.timeout(service_time)


if __name__ == '__main__':
    client_id = 1
    random.seed(RANDOM_SEED)  # same sequence each time

    max_capacity = 5e3  # diverso per ogni server
    response_time = []

    # create lambda clients
    #for i in range(1, lambd):
    env = simpy.Environment()
    stats = Statistics()

    # servers
    dictionary_of_server = {}
    env.server_china = Servers(environment=env, max_client=MAX_CLIENT, capacity=max_capacity, name="china")
    env.server_usa = Servers(environment=env, max_client=MAX_CLIENT, capacity=max_capacity, name="usa")
    env.server_brazil = Servers(environment=env, max_client=MAX_CLIENT, capacity=max_capacity, name = "brazil")
    env.server_japan = Servers(environment=env, max_client=MAX_CLIENT, capacity=max_capacity, name="japan")
    env.server_india = Servers(environment=env, max_client=MAX_CLIENT, capacity=max_capacity, name="india")
    dictionary_of_server["china"] = env.server_china
    dictionary_of_server["usa"] = env.server_usa
    dictionary_of_server["brazil"] = env.server_brazil
    dictionary_of_server["japan"] = env.server_japan
    dictionary_of_server["india"] = env.server_india


    # start the arrival process
    env.process(arrival(environment=env, nation ="china", arrival_rate=arrival_rate_global*nations["china"]))  # technically, a process actually is an event. Example: process of parking a car. https://simpy.readthedocs.io/en/latest/simpy_intro/process_interaction.html?highlight=process
    env.process(arrival(environment=env, nation ="usa", arrival_rate=arrival_rate_global*nations["usa"]))  # technically, a process actually is an event. Example: process of parking a car. https://simpy.readthedocs.io/en/latest/simpy_intro/process_interaction.html?highlight=process
    env.process(arrival(environment=env, nation ="india", arrival_rate=arrival_rate_global*nations["india"]))  # technically, a process actually is an event. Example: process of parking a car. https://simpy.readthedocs.io/en/latest/simpy_intro/process_interaction.html?highlight=process
    env.process(arrival(environment=env, nation ="brazil", arrival_rate=arrival_rate_global*nations["brazil"]))  # technically, a process actually is an event. Example: process of parking a car. https://simpy.readthedocs.io/en/latest/simpy_intro/process_interaction.html?highlight=process
    env.process(arrival(environment=env, nation ="japan", arrival_rate=arrival_rate_global*nations["japan"]))  # technically, a process actually is an event. Example: process of parking a car. https://simpy.readthedocs.io/en/latest/simpy_intro/process_interaction.html?highlight=process

    # simulate until SIM_TIME
    env.run(until=SIM_TIME)  # the run process starts waiting for it to finish
    response_time.append(stats.mean())
    print(nation_stats)
# totally occupied servers in this case
# we need parallel servers for example 5 servers for 5 continents