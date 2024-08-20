import matplotlib.pyplot as plt
import math
import random
import numpy as np

floor = 5

if True:
    if floor == 0:
        continue
    print('shoot')

def generate(size):
    vertBuffer = 720 // (16 * 4)
    mapHeight = int(size + 2 * vertBuffer) 
    horBuffer = 1080 // (16 * 4)
    mapWidth = int(size + 2 * horBuffer) 

    vertexNum = int(size / 2)
    roomCount = int((size / 5) ** 1.3)
    roomSize = size
    corridorLengthMin = 5
    corridorLengthMax = int(size / 2)


    map = np.zeros((mapHeight, mapWidth))
    for i in range(mapHeight):
        for j in range(mapWidth):
            map[i,j] = 1

    roomLocations = []
    for _ in range(vertexNum):
        
        corridorSuccess = False
        corridorLength = random.randint(corridorLengthMin, corridorLengthMax)
        while not corridorSuccess:
            
            if len(roomLocations) == 0:
                digPos = [random.randint(horBuffer, mapWidth - horBuffer), random.randint(vertBuffer, mapHeight - vertBuffer)]
            else:
                digPos = random.choice(roomLocations)

        
            currentDirection = [0, 0]
            currentDirection[random.randint(0,1)] = random.choice([-1,1])
            newPos = [digPos[0] + currentDirection[0] * corridorLength, digPos[1] + currentDirection[1] * corridorLength]
            
            if newPos[0] in range(horBuffer, mapWidth - horBuffer) and newPos[1] in range(vertBuffer, mapHeight - vertBuffer):
                roomLocations.append(newPos)
                while digPos != newPos:
                    map[digPos[1],digPos[0]] = 0
                    digPos[0] += currentDirection[0]
                    digPos[1] += currentDirection[1]
                corridorSuccess = True



    for _ in range(roomCount):
        digPos = random.choice(roomLocations)
        currentRoomCount = 0

        while currentRoomCount < roomSize: 
            currentDirection = [0, 0]           
            currentDirection[random.randint(0,1)] = random.choice([-1,1])
            newPos = [digPos[0] + currentDirection[0], digPos[1] + currentDirection[1]]
            

            if newPos[0] in range(horBuffer, mapWidth - horBuffer) and newPos[1] in range(vertBuffer, mapHeight - vertBuffer):
                map[newPos[1],newPos[0]] = 0
                digPos = newPos
                currentRoomCount += 1
            
                    
                





    # for i in range(horBuffer, mapWidth - horBuffer):
    #     for j in range(vertBuffer, mapHeight - vertBuffer):
    #         if random.random() > 0.5:
    #             map[j,i] = 0
    


    return map

# for i in range(100,120):
#     plt.imshow(generate(i))
#     plt.show()