import copy
import random

def nearest_servers(id):
    nations = ["china", "usa", "india", "japan", "brazil"]
    index = nations.index(id)
    distances = [[0, 11004, 3783, 2100, 16950],
                 [1104, 0, 11770, 10864, 6835],
                 [3783, 11770, 0, 5848, 14258],
                 [2100, 10864, 5848, 0, 17692],
                 [16950, 6835, 14258, 17962, 0]]
    list_nations = []
    for i in range(len(nations)):
        closest = nations[distances[index].index(min(distances[index]))]
        list_nations.append(closest)
        distances[index][distances[index].index(min(distances[index]))] += max(distances[index])+1
    return list_nations


def RTT(server, client):
    nations = ["china", "usa", "india", "japan", "brazil"]
    distances = [[0, 11004, 3783, 2100, 16950],
                 [1104, 0, 11770, 10864, 6835],
                 [3783, 11770, 0, 5848, 14258],
                 [2100, 10864, 5848, 0, 17692],
                 [16950, 6835, 14258, 17962, 0]]
    ind_server = nations.index(server)
    ind_client = nations.index(client)
    return distances[ind_server][ind_client]


def global_service_times(server, dict, name_request, current_time, current_capacity):

    # The new packet dimension, equal to the previous dimension minus the amount of bits downloaded in the meantime
    dict[server]["current_requests"][name_request][2] = dict[server]["current_requests"][name_request][2] - dict[server]["current_requests"][name_request][1]*(current_time - dict[server]["current_requests"][name_request][3])
    # The new current time, referred to the last update of shared capacity
    dict[server]["current_requests"][name_request][3] = current_time
    # The new shared capacity for the packet
    dict[server]["current_requests"][name_request][1] = current_capacity
    # THe new service time, equal to the current dimension of the packet over the current shared capacity
    dict[server]["current_requests"][name_request][0] = dict[server]["current_requests"][name_request][2]/dict[server]["current_requests"][name_request][1]
    print("New service time for id", name_request, " : ", round(dict[server]["current_requests"][name_request][0], 10))
    return dict


def evaluate_cost(last_update, time, server):
    costs = {"china": 0.104/60, "usa": 0.0976/60, "india": 0.0896/60, "japan": 0.1088/60, "brazil": 0.1344/60}
    return (time - last_update)*costs[server]


def arrival_function(time, nation, arrival_rate):
    nation_timezone = {"china": 8, "usa": -5, "india": 5, "brazil": -3, "japan": 9}
    hour_to_sec = 60*60
    if (time % 24*hour_to_sec) < (8 + nation_timezone[nation])*hour_to_sec or (time % 24*hour_to_sec > (20 + nation_timezone[nation])*hour_to_sec):
        arrival_rate2 = copy.deepcopy(arrival_rate * random.uniform(0.05, 0.15))
    else:
        arrival_rate2 = copy.deepcopy(arrival_rate * random.uniform(0.8, 1.2))
    return arrival_rate2


def which_nation(name):
    k = len(name) - 1
    while name[k].isdigit() is True:
        k -= 1
    return name[:k+1]


def which_id(name):
    k = 0
    while name[k].isalpha() is True:
        k += 1
    return name[k:]
