#         ARCHERS ADVENTURE
# Game by Asel Gamage

# This is a top down, fantasy, action-RPG type game filled with mythological creatures, medieval armor and bows

# One of my top considerations when I decided to make this game was to make the character customizable
# Because of this, I put a lot of time into getting sprite sheets and making GUI for the armory page
# which allows the character to change their appearance and become more powerful the more they play
# the game

# I also really enjoy listening to video game sound tracks so I added my choice of tracks that I feel 
# really add to the mood of the game. I also know that music and sound effects arent for everybody so 
# I not only made the sound effects and music togglable, but also adjustable in terms of the volume

# The levelling and coin system creates a drive for the player to keep playing the game so they can equip 
# new armorand upgrade their bows

# During the making of this game, I decided to make some of my own graphics and I ended up really liking
# pixel art. Because of this, I personally drew map tiles, editted/adjusted/added to the scrolling 
# background you see in the menu screens, and drew many of the GUI features in a free pixel art software
# called Piskel

# I've also added many features to the game-play of this game, making it interesting and fun, such as
#  the easily adaptable BFS implementation in the golem AI, the laser beams shown by the skeleton snipers,
# and the random nature of the imps

# Overall, I believe my game is relaxing and fun to play with a satifying and easy to use UI.
# Hope you enjoy!


# P.S. - if you would like to cheat coins and/or player levels into the game to upgrade without actually having to play
#        go to line 1105 or 1107 respectively and look at commented instructions
#      - if you would like to skip to a certain level go to line 1353 and look at commented instructions
#      - feel free to add enemies to enemy of the all___ lists for whatever reason, (just copy and paste a previous enemy and
#        change the first two number to change the location)


from pygame import*
from random import*
from math import*
from collections import deque
import copy

init()

#----------------------------------------GAME FUNCTIONS------------------------------------------------

#-----------General Purpose------------

def distance(object1,object2): #finds the distance between two given objects where the objects are lists with an X and Y pos at the beginning
    dist=sqrt((object2[X]-object1[X])**2 + (object2[Y]-object1[Y])**2)
    return dist

def checkState(obj): #checks if an entity within the game is alive according to their amount of HP
    # also runs through the die animation
    # returns True if the death animation is finished so the entity can be removed from the level
    if obj[STATE]==-1:
        if obj[HEALTH]<=0:
            obj[MOVE]=DIE
            obj[STATE]=75
            obj[FRAME]=0
    if obj[STATE]>0:
        obj[STATE]-=1
        if obj[FRAME]<5:
            obj[FRAME]+=0.125
        else:
            obj[FRAME]=5
            return True

def getDir(x,y,mx,my): #returns a direction of up,down,right or left according to where the mouse is in relation to the object
    # for example if mouse is approx. between the angles of 45 and 135, the function will return up or SHOOTU 
    # uses image list indexes as direction (up=SHOOTU, right=SHOOTR, etc.)
    if mx>x and abs(mx-x)>=abs(my-y):
        direction=SHOOTR
    elif mx<x and abs(mx-x)>=abs(my-y):
        direction=SHOOTL
    elif my>y and abs(mx-x)<abs(my-y):
        direction=SHOOTD
    elif my<y and abs(mx-x)<abs(my-y):
        direction=SHOOTU
    else:
        direction=SHOOTU
    return direction

def clear(x,y):#returns True if there is no obstacles at a given x,y location
    #obstacles are stored as coloured areas of masks
    #masks are stored as levels/level x/mask_x.png (x being any level)
    if x<0 or x >= mask.get_width() or y<0 or y >= mask.get_height():
        return False
    elif mask.get_at((x,y))==GROUND:
        return True
    else:
        return False

def clearWalls(x,y):#returns False if theres a wall at a given x,y location
    #I made this as well as the other clear function because when I use clear for arrows, they shouldnt seem to collide with the water
    #so I needed a way to only check for walls
    #walls are black-(0,0,0,255) and water is blue-(0,0,255,255)
    if x<0 or x >= mask.get_width() or y<0 or y >= mask.get_height():
        return False
    elif mask.get_at((x,y))==(0,0,0,255):
        return False
    else:
        return True

def getAngleDir(x1,y1,x2,y2):#returns the width and height of a rectangle with hypotneuse
    # one that is similar to a triangle with vertices (x1,y1)(x2,y2),(x1,y2)
    a=x2-x1
    b=y2-y1
    c=(a**2+b**2)**0.5
    return a/c,b/c

def getAngle(x1,y1,x2,y2):#returns the angle between a line connecting two given x,y locations and
    #a horizontal line
    a=x2-x1
    b=y2-y1
    ang=atan2(-b,a)
    return degrees(ang)

def collide(x,y,w,h,x2,y2,w2,h2):#returns True if a rectangle given x,y,w,h is colliding with another rectangle
    #given x2,y2,w2,h2 and other False otherwise
    playerRect=Rect(x-w//2,y-h//2,w,h)
    objRect=Rect(x2-w2//2,y2-h2//2,w2,h2)
    if playerRect.colliderect(objRect):
        return True
    return False

def collidePoint(x,y,x2,y2,w2,h2):#returns True if a point x,y is within a rect x2,y2,w2,h2
    if Rect(x2-w2//2,y2-h2//2,w2,h2).collidepoint(x,y):
        return True
    return False

def collideEntities(obj,others,dirTuple):#returns True if a point that is going in a direction stated by a tuple that is added
    #onto the coordinates is colliding with any of the enemies in that room
    #in other words it returns True if the player will collide with any entities if it continues in a given direction stated by a x,y tuple
    x=obj[X]+dirTuple[0]
    y=obj[Y]+dirTuple[1]
    for golem in others[GOLEMS]:
        if collide(x,y,obj[WIDTH],obj[HEIGHT],golem[X],golem[Y],golem[WIDTH],golem[HEIGHT]):
            return True
    for imp in others[IMPS]:
        if collide(x,y,obj[WIDTH],obj[HEIGHT],imp[X],imp[Y],imp[WIDTH],imp[HEIGHT]):
            return True
    for skel in others[SKELS]:
        if collide(x,y,obj[WIDTH],obj[HEIGHT],skel[X],skel[Y],skel[WIDTH],skel[HEIGHT]):
            return True
    return False

def collideArrow(arrow,others):#returns True if an arrow's x and y position will collide with any enemy entities
    #also takes HP off of the enemies if a collision occurs
    x=arrow[X]+(arrow[VX]*10)
    y=arrow[Y]+(arrow[VY]*10)
    #print(x,y)
    for golem in others[GOLEMS]:
        if collidePoint(x,y,golem[X],golem[Y]-golem[HEIGHT],golem[WIDTH],golem[HEIGHT]*2):
            golem[HEALTH]-=player[ATK]
            return True
    for imp in others[IMPS]:
        if collidePoint(x,y,imp[X],imp[Y]-imp[HEIGHT],imp[WIDTH],imp[HEIGHT]*2):
            imp[HEALTH]-=player[ATK]
    for skel in others[SKELS]:
        if collidePoint(x,y,skel[X],skel[Y]-skel[HEIGHT],skel[WIDTH],skel[HEIGHT]*2):
            skel[HEALTH]-=player[ATK]
            return True
    return False

def collideArrow1(arrow,others):#returns True if an arrow's x and y position will collide with the player
    #and takes off the players HP if a collision occurs
    x=arrow[X]+(arrow[VX]*10)
    y=arrow[Y]+(arrow[VY]*10)
    if collidePoint(x,y,player[X],player[Y]-player[HEIGHT],player[WIDTH],player[HEIGHT]*2):
        player[HEALTH]-=1
        return True
    return False

def checkEmpty(bigList):#returns True if a list of lists or 2d list is empty
    for i in bigList:
        if len(i)>0:
            return False
    return True

def drawHitboxes(obj): #takes an object and draws a box using its x,y,w and h
    draw.rect(screen,(0,0,0),(obj[X]-obj[WIDTH]//2,obj[Y]-obj[HEIGHT]//2,obj[WIDTH],obj[HEIGHT]),1)

def drawRoomPath(): #draws an image that shows how to get to the next room
    img=transform.scale(image.load("button/gui25.png"),(80,40))
    screen.blit(img,(360,40))


#---------------Player-----------------

#collide(player[X],player[Y]-4,25,25,golem[X],golem[Y],30,30)==False
#collide(player[X],player[Y]+4,25,25,golem[X],golem[Y],30,30)==False
#collide(player[X]+4,player[Y],25,25,golem[X],golem[Y],30,30)==False
#collide(player[X]-4,player[Y],25,25,golem[X],golem[Y],30,30)==False

def movePlayer(player):#this function moves and updates the player
    x=player[X]
    y=player[Y]
    w=player[WIDTH]
    h=player[HEIGHT]
    #the player will go through all the animations if W A S D keys are pressed but will only move if the path is clear
    #which is determined using the clear and collideEntities functions
    if keys[K_w]:
        player[MOVE]=UP
        if clear(x-w//2,y-h//2-3) and clear(x+w//2,y-h//2-3) and collideEntities(player,enemies,(0,-3))==False:
            player[Y]-=3
    elif keys[K_s]:
        player[MOVE]=DOWN
        if clear(x-w//2,y+h//2+3) and clear(x+w//2,y+h//2+3) and collideEntities(player,enemies,(0,3))==False:
            player[Y]+=3
    elif keys[K_d]:
        player[MOVE]=RIGHT
        if clear(x+w//2+3,y-h//2) and clear(x+w//2+3,y+h//2) and collideEntities(player,enemies,(3,0))==False:
            player[X]+=3
    elif keys[K_a]:
        player[MOVE]=LEFT
        if clear(x-w//2-3,y-h//2) and clear(x-w//2-3,y+h//2) and collideEntities(player,enemies,(-3,0))==False:
            player[X]-=3
    #if no movement key is being pressed then the player will auto shoot in the direction of the mouse
    else:
        player[MOVE]=getDir(player[X],player[Y],mx,my)
        if round(player[FRAME],5)==8:
            player[FRAME]=0
            vx,vy=getAngleDir(player[X]-5,player[Y]-20,mx,my)
            sounds[ARROW].play()
            addProjectile2(player[X]-5,player[Y]-20,vx,vy,-1)

    player[FRAME]+=0.25

    if player[FRAME]>=len(playerPics[player[MOVE]]):
        player[FRAME]=0


#---------------------Golems----------------------------

#------pathfinding stuff-------

def makeGrid(wid,hei,mask):#given a mask, this function will check every 'tile'
    #and if theres a obstacle shown on the mask at that tile then a tuple indicating the obstacles position
    #will be added to a list of obstacles (called walls even though it includes water tiles not just wall tiles)
    #the map is simplified into a 20 by 20 grid where each coordinate is its own tile
    #within the actual game, wall tiles and water blocks take up a 40 by 40 space so it is much less demanding of the computer to 
    #find a path with a 20 by 20 grid instead of a 800 by 800 grid
    walls=[]
    for i in range(0,wid):
        for j in range(0,hei):
            x=i*int(800/wid)+1 
            y=j*int(800/hei)+1
            if mask.get_at((x,y))==(0,0,0,255) or mask.get_at((x,y))==(0,0,255,255):
                walls.append((i,j))
    return walls

def inBounds(node,graph):#returns True if a given node tuple is within the bounds of the grid
    x,y=node
    if x>=0 and x<graph[WID] and y>=0 and y<graph[HEI]:
        return True
    return False


def getNeighbours(graph,node):#returns all relevant neighbours to a node
    #neighbours that are outside the grid or are in the walls list are irrelevant
    x,y=node
    #begins by forming a list of candidates which are the nodes 1 away in each direction relative to the first given node
    neighbours=[(x+1,y),(x,y-1),(x-1,y),(x,y+1)]
    for neighbour in reversed(neighbours):
        toRemove=False
        if (neighbour not in graph[2])==False:
            toRemove=True
        if inBounds(neighbour,graph)==False:
            toRemove=True
        if toRemove:#neighbour is only removed from the candidates at the end of the loop to make sure the order isnt mixed up and also to prevent
            #the program from crashing due to trying to delete the same thing twice
            neighbours.remove(neighbour)
    return neighbours

def makePath(cameFrom,node,dest):#goes back through the cameFrom dictionary to make a path that leads to the original node from the destination which has
    #been found and then reverses that list of locations
    current=dest
    path=[]
    while current!=node:
        path.append(current)
        current=cameFrom[current]
    path.append(node)
    path.reverse()
    #returns a list of tuple locations on a 20 by 20 grid that lead to the destination
    return path
            

def bfs(graph,node,dest):#pathfinding algorithm that checks evenly in all directions
    #uses a deque to make storing and taking values from the queue easier
    search=deque()
    search.append(node)
    cameFrom={}#cameFrom is a dictionary that stores the node used to get to the current one
    cameFrom[node]=None

    while len(search)>0:#loop keeps going until the destination is found or all possible locations are checked
        current=search.popleft() #pops the value on the left side of the queue
        if current==dest:
            break
        for next in getNeighbours(graph,current): #gets all valid neighbours and adds them to the queue and says that
            #the current node was the node used to get to the neighbour
            if next not in cameFrom:
                search.append(next)
                cameFrom[next]=current

    return cameFrom


def moveGolems(golem):#moves and updates a single golem
    if golem[STATE]==-1:
        if golem[MOVE]>UP:#makes sure that the golem is in a walk state
            golem[MOVE]-=4
        if distance(golem,player)>50:#if the golem is far enough away from the player to be in a different tile then
            #the pathfinding algorithm is used to find the next location to go to
            if (golem[X]-20)%40==0 and (golem[Y]-20)%40==0:
                x=(golem[X]-20)//40
                y=(golem[Y]-20)//40
                ex=player[X]//40
                ey=player[Y]//40
                #pathfinding algorithm used here
                global grid
                global path
                grid=[20,20,makeGrid(20,20,mask)]
                cameFrom=bfs(grid,(x,y),(ex,ey))
                path=makePath(cameFrom,(x,y),(ex,ey))
                changeX=(path[1][0]-path[0][0])
                changeY=(path[1][1]-path[0][1])
                #gets the new location for the golem to move to and puts the correct golem move in accordingly
                if changeX==1:
                    golem[MOVE]=RIGHT
                elif changeX==-1:
                    golem[MOVE]=LEFT
                elif changeY==1:
                    golem[MOVE]=DOWN
                elif changeY==-1:
                    golem[MOVE]=UP
            #moves the golem according to its move state
            if golem[MOVE]==RIGHT:
                golem[X]+=1
            elif golem[MOVE]==LEFT:
                golem[X]-=1
            elif golem[MOVE]==DOWN:
                golem[Y]+=1
            elif golem[MOVE]==UP:
                golem[Y]-=1
            golem[FRAME]+=0.125
        #if the golem is any closer than 50 away from the player he goes into an attack state
        else:
            #calls the function used to do all the golem attacking stuff
            golemAtk(golem,player)
            golem[FRAME]=golem[FRAME]+0.0625

        if golem[FRAME]>=len(golemPics[golem[MOVE]]):
            golem[FRAME]=1

        if golem[STATE]==0:
            golems.remove(golem)
            
        

def golemAtk(golem,player):#makes a golem attack the player
    #golem[MOVE]=getDir(golem[X],golem[Y],player[X],player[Y])
    if golem[MOVE]<SHOOTR:
        #increases the golems move state by four to put it in an attack state of whichever way he was facing prior to him starting to attack
        golem[MOVE]+=4
    if golem[FRAME]==4:
        #plays the slam sound effect and if the golem attack hitbox collides with the player hitbox then the player loses health
        sounds[SLAM].play()
        if golem[MOVE]==SHOOTD and golem[FRAME]==4:
            if collide(golem[X],golem[Y]+10,20,20,player[X],player[Y],25,25)==False:
                player[HEALTH]-=2
        if golem[MOVE]==SHOOTU and golem[FRAME]==4:
            if collide(golem[X],golem[Y]-10,20,20,player[X],player[Y],25,25)==False:
                player[HEALTH]-=2
        if golem[MOVE]==SHOOTL and golem[FRAME]==4:
            if collide(golem[X]-10,golem[Y],20,20,player[X],player[Y],25,25)==False:
                player[HEALTH]-=2
        if golem[MOVE]==SHOOTR and golem[FRAME]==4:
            if collide(golem[X]+10,golem[Y],20,20,player[X],player[Y],25,25)==False:
                player[HEALTH]-=2


#--------------------Imps-------------------------

def moveImps(imp,lastMove):#randomly moves the imp in a direction and randomly causes the imp to shoot fireballs at the player
    if imp[ACTION]==WALK:#the imp has two main states; attack or walk. If the imp is in walk mode then it walks in a direction and occassionally switches directions
        moves=[0,1,2,3]
        if imp[CMOVE]==0:#only changes the move if the move countdown is at 0
            move=choice(moves)
            lastMove=move
        elif imp[CMOVE]>0:#if the move countdown hasnt reached zero then the imp continues on whatever way he was going before
            move=lastMove
        if move==0:#if countdown is at 0 then a number is randomly picked to adjust the imps direction
            imp[MOVE]=RIGHT
            if clear(imp[X]+17,imp[Y]):
                imp[X]+=1
        elif move==1:
            imp[MOVE]=LEFT
            if clear(imp[X]-17,imp[Y]):
                imp[X]-=1
        elif move==2:
            imp[MOVE]=UP
            if clear(imp[X],imp[Y]-17):
                imp[Y]-=1
        elif move==3:
            imp[MOVE]=DOWN
            if clear(imp[X],imp[Y]+17):
                imp[Y]+=1
        imp[FRAME]+=0.0625

    elif imp[ACTION]==ATTACK:#if the imp is in attack mode then it idles at a image that best points in the direction of the player
        imp[MOVE]=getDir(imp[X],imp[Y],player[X],player[Y])
        if imp[CMOVE]==5 or imp[CMOVE]==15 or imp[CMOVE]==25:
            #shoots three fireballs over the course of its attack state that shoot not 100% precisely in the direction of the player
            #there is some randomness in the direction of the fireballs which can make them harder to dodge while close
            vx,vy=getAngleDir(imp[X],imp[Y],player[X]+randint(-30,30),player[Y]+randint(-30,30))
            sounds[FIREBALL].play()
            addFireball(imp[X],imp[Y],vx,vy)

    if imp[CMOVE]==0:
        #when switching to walk mode from attack, a counter of 50 is set
        if imp[ACTION]==ATTACK:
            imp[ACTION]=WALK
            imp[CMOVE]=50
        else:#if the counter is at zero and the last counter wasnt for an attack then theres a 1 in 3 chance that the imp will go into attack mode
            chance=randint(0,3)
            if chance==0:#if attack mode is triggered than a counter begins for 30 where 3 fireballs will be shot
                imp[ACTION]=ATTACK
                imp[CMOVE]=30
            else:#if not then the imp will have a chance at switching directions and continue walking
                imp[ACTION]=WALK
                imp[CMOVE]=50
    imp[CMOVE]-=1
    
    if imp[FRAME]>=len(impPics[imp[MOVE]]):
        imp[FRAME]=0

    return lastMove #returns the last move of the imp to keep track of the move to prevent the imp sporadically witching directions



#--------------------Skeletons-----------------------

def moveSkels(skel):#skels stay in place as they slowly fire arrows at the player
    skel[MOVE]=getDir(skel[X],skel[Y],player[X],player[Y])
    if skel[FRAME]==6:
        #if the skel has reached a frame of 6 then it adds an arrow that is on a timer and adds a laser to the lasers list
        vx,vy=getAngleDir(skel[X],skel[Y],player[X],player[Y])
        addProjectile1(skel[X]-5,skel[Y]-20,vx,vy,-1,player[X],player[Y])
        addLaser(skel[X],skel[Y],player[X],player[Y])

    #the skel goes through the frames much slower during the firing part of the animation to give the player more time to react
    if int(skel[FRAME])==6:
        skel[FRAME]+=0.015625
    else:
        skel[FRAME]+=0.125
    
    if skel[FRAME]>=len(skelPics[skel[MOVE]]):
        skel[FRAME]=0

#----------------Lasers-------------------------

def addLaser(x1,y1,x2,y2):#adds a laser to the laser list (shows approx. where the skeleton arrow will go)
    lasers.append([(x1,y1),(x2,y2),64])

def updateLaser(laser):#removes old lasers
    laser[2]-=1
    if laser[2]==0:
        lasers.remove(laser)


#-------------------Arrows----------------------

def addProjectile1(x,y,vx,vy,h,tx,ty):#made for skeleton arrows; adds a arrow to skelArrows with a counter of 64 so the arrows is actually
    #launched the same time the animation plays
    skelArrows.append([x,y,vx,vy,h,getAngle(x,y,tx,ty),64])

def addProjectile2(x,y,vx,vy,h):#made for player arrows; no counter
    arrows.append([x,y,vx,vy,h,getAngle(player[X],player[Y],mx,my),0])

def moveProjectile(arrow):#moves arrow if the arrows counter is up, if not it reduces the counter
    if arrow[6]==0:
        arrow[X]+=(arrow[VX])*10
        arrow[Y]+=(arrow[VY])*10
    else:
        arrow[6]-=1

def moveProjectiles1(arrows):
    for arrow in arrows:
        arrow[X]+=(arrow[VX])*10
        arrow[Y]+=(arrow[VY])*10

def checkProjectiles(arrows):#removes arrows that hit enemeis or have hit walls
    for arrow in arrows:
        #print(arrow)
        if collideArrow(arrow,enemies) or clearWalls(int(arrow[X]),int(arrow[Y]))==False:
            arrows.remove(arrow)

def checkProjectiles1(arrows):#removes enemy arrows that the player or walls
    for arrow in arrows:
        #print(arrow)
        if collideArrow1(arrow,player) or clearWalls(int(arrow[X]),int(arrow[Y]))==False:
            arrows.remove(arrow)


#------------------Fireballs---------------------------

def addFireball(x,y,vx,vy):#adds a fireball
    fireballs.append([x,y,vx,vy,getAngle(x,y,player[X],player[Y]),0])
def moveFireball(fireball):#moves and updates fireball
    fireball[X]+=(fireball[VX])*2
    fireball[Y]+=(fireball[VY])*2
    fireball[FRAME1]+=0.25
    if fireball[FRAME1]==2:
        fireball[FRAME1]=0
    if distance(fireball,player)<40:#if the fireball is close to the player, then it will turn into an explosion and also damage the player
        addExplosion(fireball,True)
        fireballs.remove(fireball)
    if clear(int(fireball[X]+fireball[VX]*2),int(fireball[Y]+fireball[VY]*2))==False:#if the fireball contacts a wall it will explode
        #but will not damage the player
        addExplosion(fireball,False)
        fireballs.remove(fireball)

def addExplosion(fireball,inflictDmg):
    #adds an explosions and damages the player if the second arg is True
    explosions.append([fireball[X],fireball[Y],randint(0,2),0])
    if inflictDmg:
        player[HEALTH]-=1

def updateExplosion(explosion):#updates the frame of the explosion and removes finished explosions
    explosion[FRAME]+=0.5
    if explosion[FRAME]>=len(explosionPics[explosion[MOVE]]):
        explosions.remove(explosion)


#-------------------Coins--------------------------

def addCoin(x,y):#adds a coin to the coins list
    coins.append([x,y,0])

def updateCoin(coin,player,count):#updates the coins frame and removes it if the player collides with it
    rect=Rect(player[X]-player[WIDTH]//2,player[Y]-player[HEIGHT]//2,player[WIDTH],player[HEIGHT])
    coinRect=Rect(coin[X]-15,coin[Y]-15,30,30)
    if rect.colliderect(coinRect):
        sounds[COIN].play()#plays the pickup sound effect and increases the coin count
        count+=1
        coins.remove(coin)
    
    coin[2]+=0.25

    if coin[2]>=9:
        coin[2]=0
        
    return count#returns the coin count


#---------------------Drawing Stuff---------------------------

def makeOrder(level,numWalls):#makes an order for the objects to be drawn in according to their Y location (objects with lower Y drawn first)
    objects=[]
    if numWalls[level]>0:#walls are split into seperate images and Y values are recorded using seperate tool
        #wall Y values stored in a data file at levels/level_x/walls_x/levelx_data.txt
        ls=str(level+1)
        walls=open("levels/level_"+ls+"/walls_"+ls+"/level"+ls+"_data.txt")
        for i in range(1,numWalls[level]+1):
            objects.append((int(walls.readline().strip()),8))
    #all other objects and their Y values added to the list along with an integer to keep track of what type of object they are
    objects.append((player[Y]-25,0))
    for arrow in arrows:
        objects.append((arrow[Y]-25,1,arrow))
    for fireball in fireballs:
        objects.append((fireball[Y],2,fireball))
    for arrow in skelArrows:
        objects.append((arrow[Y],3,arrow))
    for coin in coins:
        objects.append((coin[Y],4,coin))
    for golem in enemies[GOLEMS]:
        objects.append((golem[Y]-25,5,golem))
    for imp in enemies[IMPS]:
        objects.append((imp[Y]-25,6,imp))
    for skel in enemies[SKELS]:
        objects.append((skel[Y]-25,7,skel))
    #objects are sorted so that objects with lowest Y values are at the beginning of the list
    objects=sorted(objects)
    return objects #list of objects is returned

def drawScene(player,objects,coinCount):
    #objects are then drawn in the order made by 'makeOrder()'
    screen.blit(background,(0,0))
    wallc=0
    if checkEmpty(enemies):
        drawRoomPath()#draws a small icon to show where to go if all the enemies are dead
    for obj in objects:#objects are drawn according to their integer which tells what function to call
        if obj[1]==0:
            if player[STATE]==-1 or player[STATE]>0:
                drawPlayer(player)
            #draw.rect(screen,(0,255,0),(player[X]-12,player[Y]-12,25,25),1)
        elif obj[1]==1:
            drawArrow(obj[2])
        elif obj[1]==2:
            drawFireball(obj[2])
        elif obj[1]==3:
            drawArrow(obj[2])
        elif obj[1]==4:
            drawCoin(obj[2])
        elif obj[1]==5:
            drawGolem(obj[2])
        elif obj[1]==6:
            drawImp(obj[2])
        elif obj[1]==7:
            drawSkel(obj[2])
        else:
            screen.blit(wallImgs[wallc],(0,obj[0]))
            #draw.circle(screen,(255,0,0),(400,obj[0]),3)
            wallc+=1

    for explosion in explosions:
        drawExplosion(explosion)
    for laser in lasers:
        drawLaser(laser)
    
    drawPlayerXP(player[XP],player[LEVEL])
    drawHUD(level,coinCount)
    drawCursor(mx,my)
    
    display.flip()

def drawPlayer(player):#draws player
    move=player[MOVE]
    frame = int(player[FRAME])
    pic = playerPics[move][frame]
    screen.blit(pic,(player[X]-pic.get_width()//2,player[Y]-pic.get_height()+15))
    if player[STATE]==-1:
        drawBar(player,player[HEALTH],player[MAXHP])
        #print(player[HEALTH]*int(40/player[MAXHP]))

def drawBar(obj,health,maxHP):#draws a health bar above an entity using its health and maximum health values
    #bar changes colour as health drops
    draw.rect(screen,(80,80,80),(obj[X]-20,obj[Y]-50,40,6))
    draw.rect(screen,((maxHP-health)*floor(255/maxHP),255-((maxHP-health)*floor(255/maxHP)),0),(obj[X]-20,obj[Y]-50,int(health*40/maxHP),6))
    draw.rect(screen,(0,0,0),(obj[X]-20,obj[Y]-50,40,6),1)

def drawPlayerXP(xp,pLevel):#draws XP bar for player given its level
    draw.rect(screen,(50,50,50),(25,775,750,7))
    draw.rect(screen,(0,0,0),(25,782,750,10))
    draw.rect(screen,(100,200,255),(25,775,xp/getMaxXP(pLevel)*750,7))
    draw.rect(screen,(80,170,225),(25,782,xp/getMaxXP(pLevel)*750,10))
    draw.rect(screen,(57, 121, 184),(25,775,750,17),2)
    txtPic0=font5.render("Lv. "+str(pLevel),True,(120,220,255))
    txtPic1=font5.render("Lv. "+str(pLevel),True,(0,0,0))
    screen.blit(txtPic1,(46,755))
    screen.blit(txtPic0,(45,754))
    txtPic2=font6.render((str(int(xp))+"/"+str(int(getMaxXP(pLevel)))),True,(255,255,255))
    txtPic3=font6.render((str(int(xp))+"/"+str(int(getMaxXP(pLevel)))),True,(0,0,0))
    screen.blit(txtPic3,(391,777))
    screen.blit(txtPic2,(390,776))

def drawExplosion(explosion):#draws an explosion given its frame and position
    frame=int(explosion[FRAME])
    expl=explosion[MOVE]
    pic=explosionPics[expl][frame]
    screen.blit(pic,(int(explosion[X]-pic.get_width()//2),int(explosion[Y])-pic.get_height()//2))


def drawArrow(arrow):#draws an arrow and rotates it according to its direction
    if arrow[6]==0:
        pic=skelArrowPic
        pic=transform.rotate(pic,arrow[ANGLE1])
        screen.blit(pic,(arrow[X]-pic.get_width()//2,arrow[Y]-pic.get_height()//2))

def drawFireball(fireball):# draws a fireball and rotates it according to what direction its going in
    frame=int(fireball[FRAME1])
    pic=fireballPics[frame]
    pic = transform.rotate(pic,fireball[ANGLE])
    screen.blit(pic,(fireball[X]-pic.get_width()//2,fireball[Y]-pic.get_height()//2))

def drawGolem(golem):#draws a golem
    if golem[MOVE]==DIE and int(golem[FRAME])==5:
        enemies[GOLEMS].remove(golem)
        incPlayerXP()#if golem dies then the player xp is increased
        #all enemies drop a coin when they die
        addCoin(golem[X],golem[Y])
        return
    move=golem[MOVE]
    if golem[ACTION]==ATTACK:
        move+=4
    frame=int(golem[FRAME])
    pic=golemPics[move][frame]
    screen.blit(pic,(golem[X]-pic.get_width()//2,golem[Y]-pic.get_height()+10))
    #draw.circle(screen,(0,255,0),(golem[X],golem[Y]),3)
    #draw.rect(screen,(0,255,0),(golem[X]-15,golem[Y]-15,30,30),1)
    if golem[MOVE]==SHOOTD and int(golem[FRAME])==4:
        draw.rect(screen,(255,0,0),(golem[X]-10,golem[Y]+15,20,20))
    if golem[STATE]==-1:
        drawBar(golem,golem[HEALTH],golem[MAXHP])
    draw.circle(screen,(255,0,0),(golem[X],golem[Y]),2)
    #draw.rect(screen,(80,80,80),(golem[X]-20,golem[Y]-50,40,6))
    #draw.rect(screen,((20-golem[HEALTH])*25,255-((20-golem[HEALTH])*25),0),(golem[X]-20,golem[Y]-50,golem[HEALTH]*2,6))
    #draw.rect(screen,(250,50,50),(golem[X]-20,golem[Y]-50,40,6),1)

def drawSkel(skel):#draws a skeleton
    if skel[MOVE]==DIE:
        enemies[SKELS].remove(skel)
        incPlayerXP()
        addCoin(skel[X],skel[Y])
        return
    move=skel[MOVE]
    frame=int(skel[FRAME])
    pic=skelPics[move][frame]
    screen.blit(pic,(skel[X]-pic.get_width()//2,skel[Y]-pic.get_height()+8))
    if skel[STATE]==-1:
        drawBar(skel,skel[HEALTH],skel[MAXHP])

def drawLaser(laser):# draws a laser
    draw.line(screen,(255,0,0),laser[0],laser[1],3)

def drawImp(imp):# draws a imp
    if imp[MOVE]==DIE:
        enemies[IMPS].remove(imp)
        incPlayerXP()
        addCoin(imp[X],imp[Y])
        return
    move=imp[MOVE]
    frame=int(imp[FRAME])
    pic=impPics[move][frame]
    screen.blit(pic,(imp[X]-pic.get_width()//2,imp[Y]-pic.get_height()+8))
    if imp[STATE]==-1:
        drawBar(imp,imp[HEALTH],imp[MAXHP])

def drawCoin(coin):# draws a rotating coin
    pic=coinPics[int(coin[2])]
    screen.blit(pic,(coin[X]-pic.get_width()//2,coin[Y]-pic.get_height()//2))

def drawCursor(x,y):# draws a cross at the mouse position to help with aiming
    draw.line(screen,(0,0,0),(x-10,y),(x+10,y),5)
    draw.line(screen,(0,0,0),(x,y-10),(x,y+10),5)

def incPlayerXP():# increases a copy of the players XP amount to allow for the other one to increase gradually for the visual affect
    player[NXP]+=20

def playerXP(player):#increases player xp gradually for visual effect
    #if the max xp for that level is reached then the player levels up
    maxHP=getMaxXP(player[LEVEL])
    if player[NXP]>player[XP]:
        player[XP]+=0.5
    if player[XP]>=maxHP:
        player[XP]=0
        player[NXP]=0
        player[LEVEL]+=1
        sounds[LEVELUP].play()

def getMaxXP(level):#returns xp needed to get to the next level given a current level
    maxXP=100*level/4*(level**0.4)
    return maxXP

def drawHUD(level,coinCount):#draws some graphical elements at the top left of the screen
    # shows the number of the room your in and amount of coins
    display1=transform.scale(image.load("button/gui15.png"),(480,80))
    screen.blit(display1,(-100,0))
    coin=image.load("coin/goldCoin5.png")
    txtPic0=font7.render("ROOM "+str(level+1),True,(120,220,255))
    txtPic1=font7.render("ROOM "+str(level+1),True,(0,0,0))
    if coinCount>9:
        txtPic2=font6.render(str(coinCount),True,(255,255,0))
    else:
        txtPic2=font6.render("0"+str(coinCount),True,(255,255,0))
    screen.blit(txtPic1,(20,5))
    screen.blit(txtPic0,(19,4))
    screen.blit(coin,(170,-3))
    screen.blit(txtPic2,(200,6))
        


#-------------------------------------------

def drawCharacter(x,y,w,h):
    #draws a scaled down avatar of the player
    pic=playerPics[DOWN][0]
    pic=transform.scale(pic,(w,h))
    screen.blit(pic,(x,y))


#------------------LOADING FUNCTIONS----------------------

def loadImages(pics,string,num):#loads images to a list given the list, the name basic name of the image excluding the integer and a number of images to add
    ind=string.find(".")
    move=[]
    for i in range(0,num):
        move.append(image.load(string[:ind]+str(i)+string[ind:]))
    pics.append(move)


def loadResources(level,numWalls):#loads the wall images for a room
    ls=str(level+1)
    background=image.load("levels/level_"+ls+"/base_"+ls+".png").convert()
    background=transform.scale(background,(800,800))
    mask=image.load("levels/level_"+ls+"/mask_"+ls+".png").convert()
    mask=transform.scale(mask,(800,800))
    wallImgs=[]
    for i in range(numWalls[level]):
        #wallImgs.append(transform.scale(image.load("levels/level_"+ls+"/walls_"+ls+"/wall_"+str(i+1)+".png"),(800,89)))
        wallImgs.append(image.load("levels/level_"+ls+"/walls_"+ls+"/wall_"+str(i+1)+".png"))
    return background,mask,wallImgs


def loadEnemies(level,golems,imps,skels):#loads the entity data for the enemies for a given room
    levelGolems=golems[level]
    levelImps=imps[level]
    levelSkels=skels[level]
    nList=[]
    nList.append(levelGolems)
    nList.append(levelImps)
    nList.append(levelSkels)
    return nList

def loadPlayerpics(playerSet,pics):# loads the pictures of the player given the helmet and chest piece that he is wearing
    helm=playerSet[HELMET]
    chest=playerSet[CHEST]
    loadImages(pics,"player/armor"+str(chest)+str(helm)+"/walkRight/walkRight.png",8)
    loadImages(pics,"player/armor"+str(chest)+str(helm)+"/walkLeft/walkLeft.png",8)
    loadImages(pics,"player/armor"+str(chest)+str(helm)+"/walkDown/walkDown.png",8)
    loadImages(pics,"player/armor"+str(chest)+str(helm)+"/walkUp/walkUp.png",8)

    loadImages(pics,"player/armor"+str(chest)+str(helm)+"/shootRight/shootRight.png",12)
    loadImages(pics,"player/armor"+str(chest)+str(helm)+"/shootLeft/shootLeft.png",12)
    loadImages(pics,"player/armor"+str(chest)+str(helm)+"/shootDown/shootDown.png",12)
    loadImages(pics,"player/armor"+str(chest)+str(helm)+"/shootUp/shootUp.png",12)
    loadImages(pics,"player/armor"+str(chest)+str(helm)+"/playerDie/playerDie.png",6)



"""                         \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ ARMORY FUNCTIONS //////////////////////////////////////////"""


def drawArmoryHUD(playerSet):#displays the number of coins at top right
    hudImage=transform.scale(image.load("button/gui17.png"),(100,50))
    coin=image.load("coin/goldCoin5.png")
    if playerSet[COINS]>9:
        txtPic=font6.render(str(playerSet[COINS]),True,(255,255,0))
    else:
        txtPic=font6.render("0"+str(playerSet[COINS]),True,(255,255,0))
    screen.blit(hudImage,(800-hudImage.get_width(),0))
    screen.blit(coin,(720,-1))
    screen.blit(txtPic,(750,7))

def drawSelectRects(button1,button2,x1,x2,y,offY,text):#draws the buttons behind the armors that you can select
    for i in range(2):
        screen.blit(button1,(x1,i*offY+y))
        screen.blit(button2,(x2,i*offY+y))
        txtPic1=font40.render(text[i],True,(255,255,255))
        txtPic2=font41.render(text[i],True,(47, 121, 158))
        screen.blit(txtPic1,(x1+30,i*offY+50))
        screen.blit(txtPic2,(x1+30,i*offY+50))

def drawBowRect(button1,buttons,x,y,text):#draws the rectangle for the bow along with a button to upgrade the bow
    if buttons[2].collidepoint(mx,my):
        screen.blit(buttons[1],(x-1,y))
    else:
        screen.blit(buttons[0],(x-1,y))
    screen.blit(button1,(x,y))
    txtPic1=font40.render(text,True,(255,255,255))
    txtPic2=font41.render(text,True,(47,121,158))
    coin=transform.scale(image.load("misc resources/coin.png"),(20,25))
    if playerSet[BOWLVLS][playerSet[0]]<4:
        txtPic3=font6.render("Upgrade",True,(255,255,255))
        txtPic4=font6.render(str(getCost(playerSet[BOW],playerSet[BOWLVLS][playerSet[BOW]],playerSet)),True,(255,255,0))
        screen.blit(coin,(x+45,y+260))
    else:
        txtPic3=font6.render("N/A",True,(255,255,255))
        txtPic4=font6.render("",True,(255,255,255))
    screen.blit(txtPic1,(x+20,y-30))
    screen.blit(txtPic2,(x+20,y-30))
    screen.blit(txtPic3,(x+70-txtPic3.get_width()//2,y+245))
    screen.blit(txtPic4,(x+80-txtPic4.get_width()//2,y+265))

def drawArmor(set1,set2,l1,l2,click):#draws the helmets and chest pieces
    for i in range(l1):
        screen.blit(set1[i][0],(set1[i][1][:2]))
        if set1[i][1].collidepoint(mx,my):
            draw.rect(screen,(255,255,255),(set1[i][1][0]-5,set1[i][1][1]-5,set1[i][1][2]+5,set1[i][1][3]+5),2)
            #players can only access pieces once they are at a certain level
            if player[LEVEL]<playerSet[CHESTUNLOCK][i]:
                pic=transform.scale(image.load("button/gui18.png"),(set1[i][1][2]+5,set1[i][1][3]+5))
                screen.blit(pic,(set1[i][1][0]-5,set1[i][1][1]-5))
                txtPic1=font6.render("Reach level "+str(playerSet[CHESTUNLOCK][i]),True,(255,255,255))
                txtPic2=font6.render("to unlock this",True,(255,255,255))
                txtPic3=font6.render("armor",True,(255,255,255))
                screen.blit(txtPic1,(set1[i][1][0]+set1[i][1][3]//2-txtPic1.get_width()//2+5,set1[i][1][1]+20))
                screen.blit(txtPic2,(set1[i][1][0]+set1[i][1][3]//2-txtPic2.get_width()//2+5,set1[i][1][1]+35))
                screen.blit(txtPic3,(set1[i][1][0]+set1[i][1][3]//2-txtPic3.get_width()//2+5,set1[i][1][1]+50))
    for i in range(l2):
        screen.blit(set2[i][0],(set2[i][1][:2]))
        if set2[i][1].collidepoint(mx,my):
            draw.rect(screen,(255,255,255),(set2[i][1][0]-5,set2[i][1][1]-5,set2[i][1][2]+5,set2[i][1][3]+5),2)
            if player[LEVEL]<playerSet[HELMUNLOCK][i]:
                pic=transform.scale(image.load("button/gui18.png"),(set2[i][1][2]+5,set2[i][1][3]+5))
                screen.blit(pic,(set2[i][1][0]-5,set2[i][1][1]-5))
                txtPic1=font6.render("Reach level",True,(255,255,255))
                txtPic2=font6.render(str(playerSet[HELMUNLOCK][i])+" to unlock",True,(255,255,255))
                txtPic3=font6.render("this armor",True,(255,255,255))
                screen.blit(txtPic1,(set2[i][1][0]+set2[i][1][3]//2-txtPic1.get_width()//2,set2[i][1][1]+20))
                screen.blit(txtPic2,(set2[i][1][0]+set2[i][1][3]//2-txtPic2.get_width()//2,set2[i][1][1]+35))
                screen.blit(txtPic3,(set2[i][1][0]+set2[i][1][3]//2-txtPic3.get_width()//2,set2[i][1][1]+50))

def drawBow(bows,playerSet):#draws the bow along with the name of the bow and its upgrade level
    bowNames=["Legionnares Bow","Enchanted Bow","Dark Bow"]
    screen.blit(bows[playerSet[0]][0],(bows[0][1][:2]))
    if playerSet[BOWLVLS][playerSet[0]]<4:
        txtPic1=font6.render("LEVEL "+str(playerSet[BOWLVLS][playerSet[0]]),True,(200,230,255))
    else:
        txtPic1=font6.render("LEVEL MAX",True,(200,230,255))
    txtPic20=transform.rotate(font6.render(bowNames[playerSet[0]],True,(170,190,210)),90)
    txtPic21=transform.rotate(font6.render(bowNames[playerSet[0]],True,(0,0,0)),90)
    screen.blit(txtPic1,(85-txtPic1.get_width()//2,310))
    screen.blit(txtPic21,(38,271-txtPic21.get_height()))
    screen.blit(txtPic20,(37,270-txtPic20.get_height()))

def drawBackground(background,x,speed): #draws the endlessly scrolling background
    screen.blit(background,(x,0))
    x-=speed
    if x==-1707:
            x=0
    return x

def checkEquip(set1,set2,l1,l2,click): #checks if any of the armor pieces are being equiped
    for i in range(l1):
        if set1[i][1].collidepoint(mx,my) and click and player[LEVEL]>=playerSet[CHESTUNLOCK][i]:
            sounds[BUTTON].play()
            playerSet[2]=i
    for i in range(l2):
        if set2[i][1].collidepoint(mx,my) and click and player[LEVEL]>=playerSet[HELMUNLOCK][i]:
            sounds[BUTTON].play()
            playerSet[1]=i
            playerSet[0]=i


def drawEquiped(playerSet,set1,set2):#draws the equiped armor pieces
    draw.rect(screen,(100,180,205),(set2[playerSet[1]][1][0]-5,set2[playerSet[1]][1][1]-5,set2[playerSet[1]][1][2]+5,set2[playerSet[1]][1][3]+5),2)
    draw.rect(screen,(100,180,205),(set1[playerSet[2]][1][0]-5,set1[playerSet[2]][1][1]-5,set1[playerSet[2]][1][2]+5,set1[playerSet[2]][1][3]+5),2)
    screen.blit(set1[playerSet[2]][0],(193,set1[playerSet[2]][1][1]))
    screen.blit(set2[playerSet[1]][0],(200,set2[playerSet[1]][1][1]))

def drawPreview(playerSet,preview,set1,set2):#draws a preview of the player at the bottom right of the screen
    screen.blit(preview,(45,650))
    screen.blit(transform.scale(set1[playerSet[2]][0],(60,40)),(45,685))
    screen.blit(transform.scale(set2[playerSet[1]][0],(55,53)),(48,640))

def showStats():#shows a stat screen at the bottom of the armory page which displays HP and ATK levels
    screen.blit(transform.scale(image.load("button/gui10.png"),(620,400)),(150,600))
    hp,dmg=getStats()
    bar1W=hp/20*440 #converting the HP level to a width to draw the bar
    bar2W=dmg/6*440
    txtPic1=font6.render("HP",True,(255,255,255))
    txtPic2=font6.render("Atk",True,(255,255,255))
    txtPic30=font40.render("Player Level "+str(player[LEVEL]),True,(100,150,200))
    txtPic31=font41.render("Player Level "+str(player[LEVEL]),True,(255,255,255))
    txtPic4=font6.render(str(hp),True,(255,255,255))
    txtPic5=font6.render(str(dmg),True,(255,255,255))
    screen.blit(txtPic1,(270-txtPic1.get_width(),650))
    screen.blit(txtPic2,(270-txtPic2.get_width(),695))
    screen.blit(txtPic31,(250,730))
    screen.blit(txtPic30,(250,730))
    draw.rect(screen,(0,255,0),(280,645,bar1W,30))
    draw.rect(screen,(100,180,205),(280,645,bar1W,30),3)
    draw.rect(screen,(0,255,0),(280,690,bar2W,30))
    draw.rect(screen,(100,180,205),(280,690,bar2W,30),3)
    draw.line(screen,(39, 156, 119),(279,630),(279,730),3)
    screen.blit(txtPic4,(bar1W+285,650))
    screen.blit(txtPic5,(bar2W+285,695))

def getStats():#gets the atk and hp stats according to what armor is equiped
    hp=playerSet[1]+3
    hp+=(playerSet[2]+1)*2+1
    hp+=8
    dmg=1
    dmg+=playerSet[BOW]-1
    dmg+=playerSet[BOWLVLS][playerSet[BOW]]
    return hp,dmg

def checkUpgrade(upgradeRect,playerSet,click):#checks if bow is being upgraded
    if click and upgradeRect[2].collidepoint(mx,my) and playerSet[BOWLVLS][playerSet[0]]<4 and playerSet[COINS]>=getCost(playerSet[BOW],playerSet[BOWLVLS][playerSet[BOW]],playerSet):
        sounds[BUTTON].play()
        playerSet[COINS]-=getCost(playerSet[BOW],playerSet[BOWLVLS][playerSet[BOW]],playerSet)
        playerSet[BOWLVLS][playerSet[0]]+=1

def getCost(bow,level,playerSet):#uses a formula to determine the cost of the next upgrade for any of the bows
    if bow==0:
        base=20
    elif bow==1:
        base=30
    else:
        base=50
    final=base/2*(level**2)-base/2*level+base
    return int(final)


"""                         \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ SETTINGS FUNCTIONS ////////////////////////////////////////"""


def updateButtons(soundButton,sound,musicButton,music):#updates on and off buttons 
    if soundButton[-1].collidepoint(mx,my) and click:#on/off for sound effects
        sounds[BUTTON].play()
        if sound: #instead of checking if the sound effects are on or off every single time
            # I just decided to replace all the sound effects with a blank wav file if sound effects are turned off
            sounds[:]=[mixer.Sound("sounds/blank.wav") for i in range(8)]
            sounds.append(1)
            sound=False
        elif sound==False:
            sounds[:]=[mixer.Sound('sounds/button.wav'),mixer.Sound("sounds/levelUp.wav"),mixer.Sound("sounds/newRoom.wav"),mixer.Sound("sounds/arrow.wav"),
            mixer.Sound("sounds/fireball.wav"),mixer.Sound("sounds/slam.wav"),mixer.Sound("sounds/coin.wav"),mixer.Sound("sounds/tally.wav"),0]
            soundX=sounds[0].get_volume()*183+345
            sound=True
    if musicButton[-1].collidepoint(mx,my) and click:#on/off for music
        sounds[BUTTON].play()
        if music:
            #music is simply paused or played using the updateMusic function
            mixer.music.pause()
            music=False
        elif music==False:
            updateMusic(True)
            mixer.music.play()
            musicX=mixer.music.get_volume()*183+345
            music=True
    return sound,music

def updateScrolls(soundScroll,soundX,musicScroll,musicX):#updates scrolling icons
    if soundScroll[1].collidepoint(mx,my) and mb[0]==1:#adjusts volume of sound affects
        soundX=mx-5
    soundScroll[3]=Rect(soundX,299,10,20)
    if musicScroll[1].collidepoint(mx,my) and mb[0]==1:#adjusts volume of music 
        musicX=mx-5
    if soundScroll[1].collidepoint(mx,my) and click:
        sounds[BUTTON].play()
    if musicScroll[1].collidepoint(mx,my) and click:
        sounds[BUTTON].play()
    musicScroll[3]=Rect(musicX,419,10,20)
    return soundX,musicX

def drawButtons(soundButton,sound,musicButton,music):#draws the on and off buttons 
    if sound:#draws image according to whether the icon is on or off and if the mouse is hovering over it
        screen.blit(soundButton[0],(soundButton[-1][:2]))
        if soundButton[-1].collidepoint(mx,my):
            screen.blit(soundButton[1],(soundButton[-1][:2]))
    elif sound==False:
        screen.blit(soundButton[2],(soundButton[-1][:2]))
        if soundButton[-1].collidepoint(mx,my):
            screen.blit(soundButton[3],(soundButton[-1][:2]))

    if music:
        screen.blit(musicButton[0],(musicButton[-1][:2]))
        if musicButton[-1].collidepoint(mx,my):
            screen.blit(musicButton[1],(musicButton[-1][:2]))
    elif music==False:
        screen.blit(musicButton[2],(musicButton[-1][:2]))
        if musicButton[-1].collidepoint(mx,my):
            screen.blit(musicButton[3],(musicButton[-1][:2]))

def drawScrolls(soundScroll,soundX,musicScroll,musicX):#draws scroll bars
    screen.blit(soundScroll[0],(soundScroll[2][:2]))
    draw.rect(screen,(150,180,200),soundScroll[3])
    draw.rect(screen,(0,0,0),soundScroll[3],2)
    screen.blit(musicScroll[0],(musicScroll[2][:2]))
    draw.rect(screen,(150,180,200),musicScroll[3])
    draw.rect(screen,(0,0,0),musicScroll[3],2)

def updateAudio(soundX,musicX):#updates the volumes for music and sound effects according to the X position of the scroll bars
    soundVol=int((soundX-345)/183*100)/100
    musicVol=int((musicX-345)/183*100)/100
    for sfx in sounds[:-1]:
        sfx.set_volume(soundVol)
    mixer.music.set_volume(musicVol)

def updateMusic(override):#if the song ends then the next song is played
    #can be overrun so that the music is set to the correct volume and starts anew when the music is turned on after being turned off
    if not mixer.music.get_busy() or override==True:
        tracks.append(tracks.popleft())
        mixer.music.load(tracks[0])
        mixer.music.set_volume(0.5)
        mixer.music.play()

    

"""                           \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ VARIABLES /////////////////////////////////////////////"""


screen=display.set_mode((800,800))

#loading sound effects
sounds=[mixer.Sound('sounds/button.wav'),mixer.Sound("sounds/levelUp.wav"),mixer.Sound("sounds/newRoom.wav"),mixer.Sound("sounds/arrow.wav"),
        mixer.Sound("sounds/fireball.wav"),mixer.Sound("sounds/slam.wav"),mixer.Sound("sounds/coin.wav"),mixer.Sound("sounds/tally.wav"),0]
for sfx in sounds[:-1]:#setting sfx default volume
    sfx.set_volume(0.5)
tracks=deque(["sounds/music/track"+str(i)+".ogg" for i in range(0,7)])#loading music tracks
shuffle(tracks)#tracks are mixed up so the order is different each time

#first track is instantly loaded and starts playing            
mixer.music.load(tracks[0])
mixer.music.set_volume(0.2)
mixer.music.play()

#state of the game starts at menu
state="MENU"

#playerSet keeps track of the equiped armor, bows, bow levels, and level needed to equip new armor
playerSet=[0,0,0,25,[1,1,1],[0,5,12],[0,3,8]] #adjust integer at position 3 to add coins
#player keeps track of player entity data such as x,y position, state (dead/alive), move, frame, etc.
player=[400,740,0,0,25,25,4,10,10,-1,1,1,1,2] #adjust integer at position 10 (after the -1) to adjust player level

#indicates how many walls should be loaded for that room
numWalls=[3,2,2,4,0,0,0,0]
#starting position of the character at any new room or at beginning
start=(400,740)

#------ENTITY LISTS------
#entity data is stored here for all enemies as list (each list being a room) of lists (each being a seperate entity of the given type) of lists (entity data)
#Once needed, the room number is used as an index to access the entities for that room
allGolems=[[[100,300,3,0,30,30,0,6,6,-1],[700,300,3,0,30,30,0,6,6,-1]],
           [[220,140,3,0,30,30,0,7,7,-1],[580,140,3,0,30,30,0,7,7,-1]],
           [[60,700,3,0,30,30,0,8,8,-1],[740,700,3,0,30,30,0,8,8,-1]],
           [[380,380,3,0,30,30,0,10,10,-1],[100,100,3,0,30,30,0,10,10,-1],[100,700,3,0,30,30,0,10,10,-1],
            [700,700,3,0,30,30,0,10,10,-1],[700,100,3,0,30,30,0,10,10,-1]],
           [],
           [[100,100,3,0,30,30,0,16,16,-1],[700,100,3,0,30,30,0,16,16,-1],[700,700,3,0,30,30,0,16,16,-1],[100,700,3,0,30,30,0,16,16,-1]],
           [],
           [[100,100,3,0,30,30,0,30,30,-1],[300,100,3,0,30,30,0,30,30,-1],[500,100,3,0,30,30,0,30,30,-1],[700,100,3,0,30,30,0,30,30,-1],[100,500,3,0,30,30,0,30,30,-1],
            [100,700,3,0,30,30,0,30,30,-1],[700,500,3,0,30,30,0,30,30,-1],[700,700,3,0,30,30,0,30,30,-1]]]

allSkels=[[[600,500,0,0,20,20,0,4,4,-1,False],[150,600,0,0,20,20,0,4,4,-1,False]],
          [[150,500,0,0,20,20,0,5,5,-1,False],[650,650,0,0,20,20,0,5,5,-1,False],[400,250,0,0,20,20,0,5,5,-1,False]],
          [[180,300,0,0,20,20,0,6,6,-1,False],[620,300,0,0,20,20,0,6,6,-1,False],[220,420,0,0,20,20,0,6,6,-1,False],
           [580,420,0,0,20,20,0,6,6,-1,False]],
          [[100,740,0,0,20,20,0,8,8,-1,False],[700,740,0,0,20,20,0,8,8,-1,False]],
          [[180,140,0,5,20,20,0,10,10,-1,False],[400,140,0,0,20,20,0,10,10,-1,False],[620,140,0,5,20,20,0,10,10,-1,False],
           [180,260,0,0,20,20,0,10,10,-1,False],[400,260,0,5,20,20,0,10,10,-1,False],[620,260,0,0,20,20,0,10,10,-1,False],
           [180,380,0,5,20,20,0,10,10,-1,False],[400,380,0,0,20,20,0,10,10,-1,False],[620,380,0,5,20,20,0,10,10,-1,False]],
          [],
          [],
          [[200,200,0,0,20,20,0,20,20,-1,False],[400,200,0,0,20,20,0,20,20,-1,False],[600,200,0,0,20,20,0,20,20,-1,False],[200,350,0,0,20,20,0,20,20,-1,False],
           [400,350,0,0,20,20,0,20,20,-1,False],[600,350,0,0,20,20,0,20,20,-1,False]]]

allImps=[[[200,500,3,0,20,20,0,2,2,-1,0,0,0]],
         [[200,450,3,0,20,20,0,2,2,-1,0,0,0],[600,600,3,0,20,20,0,2,2,-1,0,0,0]],
         [[300,140,3,0,20,20,0,2,2,-1,0,0,0],[500,140,3,0,20,20,0,2,2,-1,0,0,0]],
         [],
         [],
         [[310,340,3,0,20,20,0,5,5,-1,0,0,0],[400,340,3,0,20,20,0,5,5,-1,0,0,0],[490,340,3,0,20,20,0,5,5,-1,0,0,0]],
         [[randint(50,750),randint(50,750),3,0,20,20,0,6,6,-1,0,0,0],[randint(50,750),randint(50,750),3,0,20,20,0,6,6,-1,0,0,0],
          [randint(50,750),randint(50,750),3,0,20,20,0,6,6,-1,0,0,0],[randint(50,750),randint(50,750),3,0,20,20,0,6,6,-1,0,0,0],
          [randint(50,750),randint(50,750),3,0,20,20,0,6,6,-1,0,0,0],[randint(50,750),randint(50,750),3,0,20,20,0,6,6,-1,0,0,0],
          [randint(50,750),randint(50,750),3,0,20,20,0,6,6,-1,0,0,0],[randint(50,750),randint(50,750),3,0,20,20,0,6,6,-1,0,0,0]],
         [[randint(50,750),randint(50,750),3,0,20,20,0,6,6,-1,0,0,0],[randint(50,750),randint(50,750),3,0,20,20,0,6,6,-1,0,0,0]]]



"""\\\\\\\\\\\\\\\\\\\\\\\\ INDEXES //////////////////////////"""
#colour of the ground in masks
GROUND=(255,255,255,255)


#OBJECT LIST INDEXES
#index labels for objects such as player,golems,imps,skels
X=0
Y=1
MOVE=2
DIR=2
FRAME=3
DTUP=3
HOLD=4
WIDTH=4
HEIGHT=5
LAYER=6
ACTION=6
HEALTH=7
MAXHP=8
STATE=9
LEVEL=10
COUNTER=10
SHOWLINE=10
XP=11
CMOVE=11
NXP=12
LASTMOVE=12
ATK=13

#index labels for arrows
VX=2
VY=3
ANGLE=4
ANGLE1=5
FRAME1=5

#labels for object action states
WALK=0
ATTACK=1

#ENEMIES LIST INDEXES
GOLEMS=0
IMPS=1
SKELS=2

#IMAGE LIST INDEXES
#index labels for any list of images that uses four directional movement and attacks
RIGHT=0
LEFT=1
DOWN=2
UP=3
SHOOTR=4
SHOOTL=5
SHOOTD=6
SHOOTU=7
DIE=8

#PLAYERSET LIST INDEXES
#index labels for playerSet list
BOW=0
HELMET=1
CHEST=2
COINS=3
BOWLVLS=4
HELMUNLOCK=5
CHESTUNLOCK=6

#SOUND EFFECTS LIST INDEXES
BUTTON=0
LEVELUP=1
NEWROOM=2
ARROW=3
FIREBALL=4
SLAM=5
COIN=6
TALLY=7

#GRID LIST INDEXES
WID=0
HEI=1
WALLS=2

"""\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ LOAD IMAGES //////////////////////////////"""


#---LOAD WALLS---
'''
wallImgs=[]
wallImgs.append(transform.scale(image.load("fullMap_walls/wall_1.png"),(800,89)))
wallImgs.append(transform.scale(image.load("fullMap_walls/wall_2.png"),(800,89)))
wallImgs.append(transform.scale(image.load("fullMap_walls/wall_3.png"),(800,89)))
'''

#---LOAD ENEMIES---

#   ---LOAD GOLEMS---

golemPics=[]
loadImages(golemPics,"golem/golem_walk/golem-walkRight.png",7)
loadImages(golemPics,"golem/golem_walk/golem-walkLeft.png",7)
loadImages(golemPics,"golem/golem_walk/golem-walkForward.png",7)
loadImages(golemPics,"golem/golem_walk/golem-walkBack.png",7)

loadImages(golemPics,"golem/golem_atk/golem-atkRight.png",7)
loadImages(golemPics,"golem/golem_atk/golem-atkLeft.png",7)
loadImages(golemPics,"golem/golem_atk/golem-atkBack.png",7)
loadImages(golemPics,"golem/golem_atk/golem-atkForward.png",7)

loadImages(golemPics,"golem/golem_die/golem_die.png",6)


#   ---LOAD IMPS---

impPics=[]
loadImages(impPics,"imp/imp_walk/imp_walkRight.png",4)
loadImages(impPics,"imp/imp_walk/imp_walkLeft.png",4)
loadImages(impPics,"imp/imp_walk/imp_walkUp.png",4)
loadImages(impPics,"imp/imp_walk/imp_walkDown.png",4)
impAttackR=[image.load("imp/imp_walk/imp_walkRight1.png")]
impAttackL=[image.load("imp/imp_walk/imp_walkLeft1.png")]
impAttackD=[image.load("imp/imp_walk/imp_walkDown1.png")]
impAttackU=[image.load("imp/imp_walk/imp_walkUp1.png")]
impPics.append(impAttackR)
impPics.append(impAttackL)
impPics.append(impAttackD)
impPics.append(impAttackU)

#   ---LOAD SKELETONS---

skelPics=[]
loadImages(skelPics,"skel/skel_walk/skel-walkRight.png",8)
loadImages(skelPics,"skel/skel_walk/skel-walkLeft.png",8)
loadImages(skelPics,"skel/skel_walk/skel-walkDown.png",8)
loadImages(skelPics,"skel/skel_walk/skel-walkUp.png",8)
loadImages(skelPics,"skel/skel_shoot/skel-shootRight.png",8)
loadImages(skelPics,"skel/skel_shoot/skel-shootLeft.png",8)
loadImages(skelPics,"skel/skel_shoot/skel-shootDown.png",8)
loadImages(skelPics,"skel/skel_shoot/skel-shootUp.png",8)
loadImages(skelPics,"skel/skel_die/skel-die.png",6)

#---LOAD PROJECTILES---
#   ---LOAD ARROWS---

arrowPicR=image.load("arrow/arrowR.png")
arrowPicL=image.load("arrow/arrowL.png")
arrowPicD=image.load("arrow/arrowD.png")
arrowPicU=image.load("arrow/arrowU.png")

skelArrowPic=image.load("arrow/arrowR.png")

#   ---LOAD FIREBALL---
fireball1=image.load("imp/fireball/Fireball1.png")
fireball2=image.load("imp/fireball/Fireball2.png")
fireball1=transform.scale(fireball1,(25,25))
fireball2=transform.scale(fireball2,(25,25))

fireballPics=[]
fireballPics.append(fireball1)
fireballPics.append(fireball2)

#   ---LOAD EXPLOSIONS---
explosionPics=[]
loadImages(explosionPics,"explosions/frames_1/1_.png",49)
loadImages(explosionPics,"explosions/frames_2/1_.png",32)
loadImages(explosionPics,"explosions/frames_3/1_.png",32)

#   ---LOAD COINS---
coins=[]
coinPics=[]
for i in range(1,10):
    coinPics.append(image.load("coin/goldCoin"+str(i)+".png"))



"""                  \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ GAME STATES /////////////////////////////////////////////////////"""


""" \\\\\\\\\\\\\\\\\\\\\\\\\\\\\ PLAY ///////////////////////////// """


def game(): #loop that contains actual gameplay
    #variables
    myClock = time.Clock()
    global level
    global playerPics
    global imps
    global skels
    global golems
    global enemies
    global background,mask,wallImgs
    global skelArrows,arrows,fireballs,explosions,lasers
    skelArrows=[]
    arrows=[]
    fireballs=[]
    explosions=[]
    lasers=[]
    level=0 #change to adjust starting room number (goes up to 7)
    #player=[400,740,0,0,25,25,4,10,10,-1,8,1,1]
    player[X],player[Y]=400,740
    player[MAXHP],player[ATK]=getStats()
    player[HEALTH]=player[MAXHP]
    player[STATE]=-1
    playerPics=[]
    loadPlayerpics(playerSet,playerPics)
    global coinCount
    coinCount=0
    golemsCopy=copy.deepcopy(allGolems)
    impsCopy=copy.deepcopy(allImps)
    skelsCopy=copy.deepcopy(allSkels)
    #entity data being taken from the lists using loadEnemies()
    enemies=loadEnemies(level,golemsCopy,impsCopy,skelsCopy)
    global keys
    global mx,my
    global lastMove
    background,mask,wallImgs=loadResources(level,numWalls)
    exitDoor=Rect(380,40,40,40)
    running=True
    while running:
        for e in event.get():
            if e.type==QUIT:
                running=False
        #before=time.get_ticks()
        
        mx,my=mouse.get_pos()
        keys = key.get_pressed()
        updateMusic(False)
        if keys[27]:
            sounds[BUTTON].play()
            return "MENU"
            running = False
            
        #objects are only updated if they are alive (state of -1)
        #other wise they will be updated by checkState() later in the loop
        if player[STATE]==-1:
            movePlayer(player)
            playerXP(player)

        #enemies updated
        for golem in enemies[GOLEMS]:
            moveGolems(golem)
        for imp in enemies[IMPS]:
            imp[LASTMOVE]=moveImps(imp,imp[LASTMOVE])
        for skel in enemies[SKELS]:
            moveSkels(skel)
        #projectiles and all other entities updated
        for arrow in arrows:
            moveProjectile(arrow)
        for arrow in skelArrows:
            moveProjectile(arrow)
        for fireball in fireballs:
            moveFireball(fireball)
        for explosion in explosions:
            updateExplosion(explosion)
        #projectiles checked for collisions
        checkProjectiles(arrows)
        checkProjectiles1(skelArrows)
        for laser in lasers:
            updateLaser(laser)
        for coin in coins:
            coinCount=updateCoin(coin,player,coinCount)
        #alive/dead states checked for player and enemies
        checkState(player)
        for creature in enemies:
            for enemy in creature:
                checkState(enemy)
        #player can only go on to the next room if he is standing on the correct tile and all the enemies are defeated
        playerRect=Rect(player[X],player[Y],player[WIDTH],player[HEIGHT])
        if playerRect.colliderect(exitDoor) and checkEmpty(enemies):
            level+=1
            if level==8:
                #if the player completes the final level the GAMEWON state is called
                level=0
                playerSet[COINS]+=coinCount
                return "GAMEWON"
                running=False
            #other wise the player just goes to the next level and the new enemies are loaded in
            golemsCopy=copy.deepcopy(allGolems)
            impsCopy=copy.deepcopy(allImps)
            skelsCopy=copy.deepcopy(allSkels)
            enemies=loadEnemies(level,golemsCopy,impsCopy,skelsCopy)
            background,mask,wallImgs=loadResources(level,numWalls)
            #any entities left from the last room are cleared
            arrows.clear()
            skelArrows.clear()
            coins.clear()
            fireballs.clear()
            player[X],player[Y]=start
            #player regains 4 HP
            player[HEALTH]+=4
            sounds[NEWROOM].play()
            if player[HEALTH]>player[MAXHP]:
                player[HEALTH]=player[MAXHP]
        #if the player dies then the GAMEOVER state is called
        if player[STATE]==0:
            playerSet[COINS]+=coinCount
            return "GAMEOVER"
            running=False
        #order for objects is made and everything is drawn
        objects=makeOrder(level,numWalls)
        drawScene(player,objects,coinCount)
        #game runs at 60 fps
        myClock.tick(60)
    quit()


#IMPORTANT kind of
    
#most GUI is stored as a list where the beginning is all the images that will go in the set location, and the last position is a Rect object that
#can be used to check collision or draw the GUI at a consistent spot without having to check numbers
    
#all non-game play pages have a small button at the top right to go back to the menu
    
    
""" \\\\\\\\\\\\\\\\\\\\\\\\\\\\ GAME OVER //////////////////////////////////"""

def gameOver(): #screen shown if player dies, shows how much coins the player got during the game and has a button to return to menu screen
    myClock=time.Clock()
    global mx,my
    level=0
    ls=str(level+1)
    #images loaded in
    background=transform.scale(image.load("levels/level_1/base_1.png"),(800,800))
    backgroundLayer=transform.scale(image.load("misc resources/gameOverBackground.png"),(800,800))
    board=transform.scale(image.load("button/gui14.png"),(650,650))
    text=["GAME OVER","YOU MADE IT TO","LEVEL "+str(level+1)]
    buttons=[(transform.scale(image.load("button/gui13.png"),(280,100)),Rect(260,400,280,100)),
             (transform.scale(image.load("button/gui12.png"),(280,100)),Rect(260,505,280,100),transform.scale(image.load("button/guiH12.png"),(280,100)))]
    coin=transform.scale(image.load("coin/goldCoin5.png"),(50,50))
    if coinCount>9:
        txtPic2=font7.render(str(coinCount),True,(255,255,0))
    else:
        txtPic2=font7.render("0"+str(coinCount),True,(255,255,0))
    
    running=True
    while running:
        for e in event.get():
            if e.type==QUIT:
                running=False

        mx,my=mouse.get_pos()
        mb=mouse.get_pressed()
        updateMusic(False)
        screen.blit(background,(0,0))
        screen.blit(backgroundLayer,(0,0))
        screen.blit(board,(75,75))
        for button in buttons:
            rect=button[1]
            if len(button)==3:
                if rect.collidepoint(mx,my):
                    screen.blit(button[2],rect[:2])
                    if mb[0]==1:
                        sounds[BUTTON].play()
                        return "MENU"
                else:
                    screen.blit(button[0],rect[:2])
            else:
                screen.blit(button[0],rect[:2])

        txtPic10=font20.render(text[0],True,(255,255,255))
        txtPic11=font21.render(text[0],True,(255,0,0))
        txtPic20=font40.render(text[1],True,(255,255,255))
        txtPic21=font41.render(text[1],True,(67, 141, 168))
        txtPic30=font40.render(text[2],True,(255,255,255))
        txtPic31=font41.render(text[2],True,(67, 141, 168))

        screen.blit(txtPic10,(400-txtPic10.get_width()//2,130))
        screen.blit(txtPic11,(400-txtPic11.get_width()//2,130))
        screen.blit(txtPic20,(400-txtPic20.get_width()//2,260))
        screen.blit(txtPic21,(400-txtPic21.get_width()//2,260))
        screen.blit(txtPic30,(400-txtPic30.get_width()//2,290))
        screen.blit(txtPic31,(400-txtPic31.get_width()//2,290))
        screen.blit(coin,(400-txtPic2.get_width()//2-42,423))
        screen.blit(txtPic2,(400-txtPic2.get_width()//2,435))

        myClock.tick()
        display.flip()
        

    quit()


""" \\\\\\\\\\\\\\\\\\\\\\\\\\\\ GAME WON //////////////////////////////////"""

def gameWon():# screen shown if character completes all levels, also shows coins collected
    myClock=time.Clock()
    global mx,my
    level=0
    ls=str(level+1)
    #images loaded in
    background=transform.scale(image.load("levels/level_1/base_1.png"),(800,800))
    backgroundLayer=transform.scale(image.load("misc resources/gameOverBackground.png"),(800,800))
    board=transform.scale(image.load("button/gui14.png"),(650,650))
    text=["YOU WIN","YOU HAVE COMPLETED","ALL THE ROOMS"]
    buttons=[(transform.scale(image.load("button/gui13.png"),(280,100)),Rect(260,400,280,100)),
             (transform.scale(image.load("button/gui12.png"),(280,100)),Rect(260,505,280,100),transform.scale(image.load("button/guiH12.png"),(280,100)))]
    coin=transform.scale(image.load("coin/goldCoin5.png"),(50,50))
    if coinCount>9:
        txtPic2=font7.render(str(coinCount),True,(255,255,0))
    else:
        txtPic2=font7.render("0"+str(coinCount),True,(255,255,0))
    
    running=True
    while running:
        for e in event.get():
            if e.type==QUIT:
                running=False

        mx,my=mouse.get_pos()
        mb=mouse.get_pressed()
        updateMusic(False)
        screen.blit(background,(0,0))
        screen.blit(backgroundLayer,(0,0))
        screen.blit(board,(75,75))
        for button in buttons:
            rect=button[1]
            if len(button)==3:
                if rect.collidepoint(mx,my):
                    screen.blit(button[2],rect[:2])
                    if mb[0]==1:
                        sounds[BUTTON].play()
                        return "MENU"
                else:
                    screen.blit(button[0],rect[:2])
            else:
                screen.blit(button[0],rect[:2])

        txtPic10=font20.render(text[0],True,(255,255,255))
        txtPic11=font21.render(text[0],True,(100,180,200))
        txtPic20=font40.render(text[1],True,(255,255,255))
        txtPic21=font41.render(text[1],True,(67, 141, 168))
        txtPic30=font40.render(text[2],True,(255,255,255))
        txtPic31=font41.render(text[2],True,(67, 141, 168))

        screen.blit(txtPic10,(400-txtPic10.get_width()//2,130))
        screen.blit(txtPic11,(400-txtPic11.get_width()//2,130))
        screen.blit(txtPic20,(400-txtPic20.get_width()//2,260))
        screen.blit(txtPic21,(400-txtPic21.get_width()//2,260))
        screen.blit(txtPic30,(400-txtPic30.get_width()//2,290))
        screen.blit(txtPic31,(400-txtPic31.get_width()//2,290))
        screen.blit(coin,(400-txtPic2.get_width()//2-42,423))
        screen.blit(txtPic2,(400-txtPic2.get_width()//2,435))

        myClock.tick()
        display.flip()
        

    quit()

        

""" \\\\\\\\\\\\\\\\\\\\\\\\\\ ARMORY //////////////////////////// """
        

def armory(): #armory page allows character to select new armor, upgrade their weapon and displays stats
    myClock=time.Clock()
    titleText=["ARMORY"]
    text=["HELM","CHEST PLATE"]
    text1="BOW"
    background=image.load("misc resources/menuBackground.png").convert()
    selectButton=transform.scale(image.load("button/gui7.png"),(445,150))
    selectedButton=transform.scale(image.load("button/gui8.png"),(150,150))
    backButton=transform.scale(image.load("button/gui9.png"),(64,46))
    backButtonRect=Rect(10,10,64,44)
    preview=transform.scale(image.load("armory/preview.png"),(60,98))
    chestPlates=[(transform.scale(image.load("armory/armor"+str(i)+".png"),(110,90)),Rect(i*130+370,300,115,95)) for i in range(3)]
    helms=[(transform.scale(image.load("armory/armor"+str(i+3)+".png"),(90,90)),Rect(i*130+380,115,95,95)) for i in range(3)]
    bows=[(transform.scale(image.load("armory/bow"+str(i)+".png"),(80,190)),Rect(55,120,65,165)) for i in range(3)]
    bowRect=transform.scale(transform.rotate(image.load("button/gui16.png"),90),(140,240))
    bowUpgradeRect=[transform.scale(transform.rotate(image.load("button/gui0.png"),90),(142,300)),transform.scale(transform.rotate(image.load("button/guih0.png"),90),(142,300)),Rect(15,335,142,60)]
    x=0

    running=True
    while running:
        click=False
        for e in event.get():
            if e.type==QUIT:
                running=False
            if e.type==MOUSEBUTTONUP:
                if e.button==1:
                    click=True
        global mx,my
        global mb
        mx,my=mouse.get_pos()
        mb=mouse.get_pressed()
        keys=key.get_pressed()
        updateMusic(False)
        if backButtonRect.collidepoint(mx,my) and click or keys[27]:
            sounds[BUTTON].play()
            return "MENU"
        #buttons are all updated first
        checkEquip(chestPlates,helms,len(chestPlates),len(helms),click)
        checkUpgrade(bowUpgradeRect,playerSet,click)
        #then everything is drawn
        x=drawBackground(background,x,1.25)
        screen.blit(backButton,(backButtonRect[:2]))
        drawArmoryHUD(playerSet)
        drawBowRect(bowRect,bowUpgradeRect,15,95,text1)
        drawSelectRects(selectButton,selectedButton,330,170,85,185,text)
        drawEquiped(playerSet,chestPlates,helms)
        drawBow(bows,playerSet)
        drawArmor(chestPlates,helms,len(chestPlates),len(helms),click)
        drawPreview(playerSet,preview,chestPlates,helms)
        showStats()
        myClock.tick(30)
        display.flip()
    quit()


""" \\\\\\\\\\\\\\\\\\\\\\\\\\\\ INSTRUCTIONS ///////////////////////////////"""


def instructions():#displays an image of words that give the player a story and instructions of what to do and point behind the game
    myClock=time.Clock()
    background=image.load("misc resources/menuBackground.png").convert()
    backButton=transform.scale(image.load("button/gui9.png"),(64,46))
    backButtonRect=Rect(10,10,64,44)
    board=transform.scale(transform.rotate(image.load("button/gui10.png"),90),(700,700))
    #instead of rendering a picture for each line, I made a png image of the text using screenshotting and some background editting since the paragraph was pretty long
    txtImg=transform.scale(image.load("misc resources/txtImg.png"),(635,600))
    txtPic0=font10.render("Instructions",True,(255,255,255))
    txtPic1=font11.render("Instructions",True,(67,141,168))
    
    x=0

    running=True
    while running:
        click=False
        for e in event.get():
            if e.type==QUIT:
                running=False
            if e.type==MOUSEBUTTONUP:
                if e.button==1:
                    click=True
                    
        global mx,my,mb,keys
        mx,my=mouse.get_pos()
        mb=mouse.get_pressed()
        keys=key.get_pressed()
        
        if backButtonRect.collidepoint(mx,my) and click or keys[27]:
            sounds[BUTTON].play()
            return "MENU"
        
        x=drawBackground(background,x,0.5)
        screen.blit(backButton,(backButtonRect[:2]))
        screen.blit(board,(90,10))
        screen.blit(txtPic1,(150,-17))
        screen.blit(txtPic0,(150,-17))
        screen.blit(txtImg,(130,70))
        
        
        myClock.tick(60)
        display.flip()
    quit()


"""\\\\\\\\\\\\\\\\\\\\\\\\\ SETTINGS //////////////////////////"""


def settings():#settings allow the user to turn the music and sound effect on and off, as well as adjust the volume of both
    myClock=time.Clock()
    background=image.load("misc resources/menuBackground.png").convert()
    backButton=transform.scale(image.load("button/gui9.png"),(64,46))
    backButtonRect=Rect(10,10,64,44)
    x=0
    backBoard=transform.scale(image.load("button/gui3.png"),(400,650))
    title0=font10.render("SETTINGS",True,(255,255,255))
    title1=font11.render("SETTINGS",True,(67,141,168))
    global sound,music
    
    soundButton=[transform.scale(image.load("button/gui19.png"),(100,100)),transform.scale(image.load("button/guiH19.png"),(100,100)),transform.scale(image.load("button/gui20.png"),(100,100)),
                 transform.scale(image.load("button/guiH20.png"),(100,100)),Rect(280,120,100,100)]
    if sounds[-1]==0:
        sound=True
    else:
        sound=False
    
    musicButton=[transform.scale(image.load("button/gui22.png"),(100,100)),transform.scale(image.load("button/guiH22.png"),(100,100)),transform.scale(image.load("button/gui23.png"),(100,100)),
                 transform.scale(image.load("button/guiH23.png"),(100,100)),Rect(420,120,100,100)]
    music=True

    soundX=sounds[0].get_volume()*183+345
    soundScroll=[transform.scale(image.load("button/gui24.png"),(310,100)),Rect(345,299,178,20),Rect(245,260,310,100),Rect(soundX,299,10,20)]
    musicX=mixer.music.get_volume()*183+345
    musicScroll=[transform.scale(image.load("button/gui21.png"),(310,100)),Rect(345,419,178,20),Rect(245,380,310,100),Rect(musicX,419,10,20)]

    running=True
    global click
    while running:
        click=False
        for e in event.get():
            if e.type==QUIT:
                running=False
            if e.type==MOUSEBUTTONUP:
                if e.button==1:
                    click=True
                    
        global mx,my,mb,keys
        mx,my=mouse.get_pos()
        mb=mouse.get_pressed()
        keys=key.get_pressed()
        updateMusic(False)
        
        if backButtonRect.collidepoint(mx,my) and click or keys[27]:
            sounds[BUTTON].play()
            return "MENU"

        sound,music=updateButtons(soundButton,sound,musicButton,music)
        soundX,musicX=updateScrolls(soundScroll,soundX,musicScroll,musicX)
        updateAudio(soundX,musicX)
        
        x=drawBackground(background,x,0.5)
        screen.blit(backButton,(backButtonRect[:2]))
        screen.blit(backBoard,(200,75))
        screen.blit(title0,(230,40))
        screen.blit(title1,(230,40))
        drawButtons(soundButton,sound,musicButton,music)
        drawScrolls(soundScroll,soundX,musicScroll,musicX)
        
        myClock.tick(60)
        display.flip()
    quit()


""" \\\\\\\\\\\\\\\\\\\\\\\\\\\\\ ABOUT ////////////////////////////// """
    

def about():#about page just gives a little bit of info about the project itself
    myClock=time.Clock()
    background=image.load("misc resources/menuBackground.png").convert()
    backButton=transform.scale(image.load("button/gui9.png"),(64,46))
    backButtonRect=Rect(10,10,64,44)
    board=transform.scale(transform.rotate(image.load("button/gui10.png"),90),(700,780))
    
    title0=font10.render("ABOUT",True,(255,255,255))
    title1=font11.render("ABOUT",True,(67,141,168))
    txt0a=font8.render("GAME MADE BY ASEL GAMAGE INDUSTRIES",True,(100,200,200))
    txt0b=font8.render("GAME MADE BY ASEL GAMAGE INDUSTRIES",True,(255,255,255))
    txt1=font8.render("GAME ART BY",True,(20,50,100))
    #some game art sources
    #unfortunately I forgot to round up all the audio sources but that could be done in the future just as peace of mind although it has zero affect on the game
    txt2=font9.render("    -Asel Gamage",True,(255,255,255))
    txt3=font9.render("    -opengameart.org/users/williamthompsonj",True,(255,255,255))
    txt4=font9.render("    -opengameart.org/users/morgan3d",True,(255,255,255))
    txt5=font9.render("    -opengameart.org/users/scaghound",True,(255,255,255))
    txt6=font9.render("    -xyezawr.itch.io/",True,(255,255,255))
    txt7=font9.render("    -runica.itch.io/game-assets",True,(255,255,255))
    txt8=font8.render("PROJECT STARTED APRIL 1, 2020",True,(87,191,218))
    txt9=font8.render("PROJECT FINISHED JUNE 7, 2020",True,(87,191,218))
    
    
    x=0
    running=True
    global click
    while running:
        click=False
        for e in event.get():
            if e.type==QUIT:
                running=False
            if e.type==MOUSEBUTTONUP:
                click=True
        global mx,my,mb,keys
        mx,my=mouse.get_pos()
        mb=mouse.get_pressed()
        keys=key.get_pressed()
        updateMusic(False)
        x=drawBackground(background,x,0.5)

        if backButtonRect.collidepoint(mx,my) and click or keys[27]:
            sounds[BUTTON].play()
            return "MENU"

        screen.blit(backButton,(backButtonRect[:2]))
        screen.blit(board,(90,10))
        screen.blit(title0,(150,-17))
        screen.blit(title1,(150,-17))
        
        screen.blit(txt0a,(171,72))
        screen.blit(txt0b,(170,70))
        screen.blit(txt1,(150,120))
        screen.blit(txt2,(150,150))
        screen.blit(txt3,(150,170))
        screen.blit(txt4,(150,190))
        screen.blit(txt5,(150,210))
        screen.blit(txt6,(150,230))
        screen.blit(txt7,(150,250))
        screen.blit(txt8,(150,460))
        screen.blit(txt9,(150,495))
        

        myClock.tick(60)
        display.flip()
    quit()


""" \\\\\\\\\\\\\\\\\\\\\\\\\\\\ MENU //////////////////////////////// """
    

def menu():#menu is the central page that leads to all the other pages, simply click on the desired page you would like to go to
    #GUI is kept neat and simple
    myClock=time.Clock()
    titleText=["ARCHERS","ADVENTURE"]
    text=["PLAY","ARMORY","ABOUT","SETTINGS","INSTRUCTIONS"]
    background=image.load("misc resources/menuBackground.png").convert()
    board=transform.scale(image.load("misc resources/menuBoard.png"),(440,700))
    buttons=[]
    buttons.append(transform.scale(image.load("button/gui0.png"),(280,100)))
    buttons.append(transform.scale(image.load("button/guiH0.png"),(280,100)))
    buttons.append(transform.scale(image.load("button/gui0.png"),(280,100)))
    buttons.append(transform.scale(image.load("button/guiH0.png"),(280,100)))
    buttons.append(transform.scale(image.load("button/gui0.png"),(280,100)))
    buttons.append(transform.scale(image.load("button/guiH0.png"),(280,100)))
    buttons.append(transform.scale(image.load("button/gui4.png"),(90,90)))
    buttons.append(transform.scale(image.load("button/guiH4.png"),(90,90)))
    buttons.append(transform.scale(image.load("button/gui5.png"),(90,90)))
    buttons.append(transform.scale(image.load("button/guiH5.png"),(90,90)))
    buttons.append(transform.scale(image.load("button/gui6.png"),(90,90)))
    buttons.append(transform.scale(image.load("button/guiH6.png"),(90,90)))
    buttonRects=[Rect(500,250,280,100),Rect(500,360,280,100),Rect(500,470,280,100),Rect(500,580,90,90),Rect(595,580,90,90),Rect(690,580,85,85)]
    x=0

    running=True
    while running:
        for e in event.get():
            if e.type==QUIT:
                running=False
        mx,my=mouse.get_pos()
        mb=mouse.get_pressed()
        updateMusic(False)
        x=drawBackground(background,x,0.5)
        screen.blit(board,(400,150))
        for rect,state in zip(buttonRects,text):
            if rect.collidepoint(mx,my) and mb[0]==1:
                sounds[BUTTON].play()
                return state
        for i,rect in enumerate(buttonRects):
            if rect.collidepoint(mx,my):
                screen.blit(buttons[i*2+1],rect[:2])
            else:
                screen.blit(buttons[i*2],rect[:2])
                
        if buttonRects[5].collidepoint(mx,my) and mb[0]==1:
            break

        titlePic00=font20.render(titleText[0],True,(255,255,255))
        titlePic01=font21.render(titleText[0],True,(57, 121, 184))
        titlePic10=font20.render(titleText[1],True,(255,255,255))
        titlePic11=font21.render(titleText[1],True,(57, 121, 184))
        titlePic00=transform.rotate(titlePic00,25)
        titlePic01=transform.rotate(titlePic01,25)
        titlePic10=transform.rotate(titlePic10,25)
        titlePic11=transform.rotate(titlePic11,25)
        
        txtPic10=font10.render(text[0],True,(255,255,255))
        txtPic11=font11.render(text[0],True,(67, 141, 168))
        txtPic20=font10.render(text[1],True,(255,255,255))
        txtPic21=font11.render(text[1],True,(67, 141, 168))
        txtPic30=font10.render(text[2],True,(255,255,255))
        txtPic31=font11.render(text[2],True,(67, 141, 168))

        screen.blit(titlePic00,(0,0))
        screen.blit(titlePic01,(0,0))
        screen.blit(titlePic10,(0,15))
        screen.blit(titlePic11,(0,15))
        screen.blit(txtPic10,(520,265))
        screen.blit(txtPic11,(520,265))
        screen.blit(txtPic20,(520,375))
        screen.blit(txtPic21,(520,375))
        screen.blit(txtPic30,(520,485))
        screen.blit(txtPic31,(520,485))

        myClock.tick(60)
        display.flip()
    quit()
        

#all fonts being loaded in
font.init()
font10=font.Font("font1/8-bit Arcade In.ttf",80)
font11=font.Font("font1/8-bit Arcade Out.ttf",80)
font20=font.Font("font1/8-bit Arcade In.ttf",140)
font21=font.Font("font1/8-bit Arcade Out.ttf",140)
font30=font.Font("font1/8-bit Arcade In.ttf",40)
font31=font.Font("font1/8-bit Arcade Out.ttf",39)
font40=font.Font("font1/8-bit Arcade In.ttf",70)
font41=font.Font("font1/8-bit Arcade Out.ttf",69)
font5=font.Font("font2/aAntiCorona.ttf",50)
font6=font.Font("font2/aAntiCorona.ttf",15)
font7=font.Font("font2/aAntiCorona.ttf",30)
font8=font.Font("font2/aAntiCorona.ttf",25)
font9=font.Font("font2/aAntiCorona.ttf",20)


"""                       \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ STATE MACHINE ///////////////////////////////// """

#state machine just keeps track of the state of the game and takes in a new one once the state ends
#for example the state begins with menu() which return PLAY which cause the play() state to be called which return GAMEWON which cause the gameWon()
#state to be called and so on
while state!="EXIT":
    #print(page)
    if state=="MENU":
        state=menu()
    if state=="PLAY":
        state=game()
    if state=="ARMORY":
        state=armory()
    if state=="GAMEOVER":
        state=gameOver()
    if state=="GAMEWON":
        state=gameWon()
    if state=="SETTINGS":
        state=settings()
    if state=="INSTRUCTIONS":
        state=instructions()
    if state=="ABOUT":
        state=about()
