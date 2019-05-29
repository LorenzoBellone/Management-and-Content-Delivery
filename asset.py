def nearest_servers(id):
    nations = ["china", "usa", "india", "japan", "brazil"]
    index = nations.index(id)
    distances = [[0, 4, 2, 1, 3],  [4, 0, 5, 3, 2], [1, 5, 0, 2, 6], [1, 3, 2, 0, 4], [3, 2, 4, 6, 0]]
    list_nations = []
    for i in range(len(nations)):
        closest = nations[distances[index].index(min(distances[index]))]
        list_nations.append(closest)
        distances[index][distances[index].index(min(distances[index]))] += 10
    return list_nations
