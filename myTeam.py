# myTeam.py
# ---------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

from captureAgents import CaptureAgent
import random, time, util, math
from game import Directions
import game
from util import nearestPoint

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'OAgent', second = 'DAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

'''
  DAgent
  Defensive strategy: Prioritize defending nodes
'''



class OAgent(CaptureAgent):
  def __init__( self, index, timeForComputing = .1 ):
    # Agent index for querying state
    self.index = index
    self.top = None
    # Whether or not you're on the red team
    self.red = None
    # Agent objects controlling you and your teammates
    self.agentsOnTeam = None
    # Maze distance calculator
    self.distancer = None
    # A history of observations
    self.observationHistory = []
    # Time to spend each turn on computing maze distances
    self.timeForComputing = timeForComputing
    # Access to the graphics
    self.display = None
    self.currentGoal = None
    self.retreatNodes = []
    self.capsuleLocations = []
    self.lastRetreat = None
    self.midpoint = None
    self.touched = 0
  
  def getActionFromMinDistance(self, gameState, goal_pos):
    mindist = float('inf')
    chosen_action = None
    for action in gameState.getLegalActions(self.index):
      successor = self.getSuccessor(gameState, action)
      succ_pos = successor.getAgentState(self.index).getPosition()
      md = self.getMazeDistance(succ_pos, goal_pos)
      if md < mindist:
        chosen_action = action
        mindist = md
    return chosen_action
  
  def getInitialGoal(self, gameState):
    food = self.getFood(gameState).asList()
    width = gameState.data.layout.width / 4
    height = gameState.data.layout.height / 2
    # Set retreatNodes
    pos1, pos2, pos3 = None, None, None
    if self.red:
      pos1 = (2*width-2, 2*height-2)
      while gameState.hasWall(pos1[0], pos1[1]):
        pos1 = (pos1[0], pos1[1]-1)
      pos2 = (2*width-2, 2)
      while gameState.hasWall(pos2[0], pos2[1]):
        pos2 = (pos2[0], pos2[1]+1)
      pos3 = (2*width-2, height)
      while gameState.hasWall(pos3[0], pos3[1]):
        pos3 = (pos3[0]. pos3[1]+1)
    else:
      pos1 = (2*width+2, 2*height-2)
      while gameState.hasWall(pos1[0], pos1[1]):
        pos1 = (pos1[0], pos1[1]-1)
      pos2 = (2*width+2, 2)
      while gameState.hasWall(pos2[0], pos2[1]):
        pos2 = (pos2[0], pos2[1]+1)
      pos3 = (2*width+2, height)
      while gameState.hasWall(pos3[0], pos3[1]):
        pos3 = (pos3[0]. pos3[1]+1)
    self.midpoint = pos3
    self.retreatNodes.append(pos1)
    self.retreatNodes.append(pos2)
    quadrant_food = [f for f in food if f[0] <= 3 * width and f[1] >= height]
    if len(quadrant_food) == 0:
      quadrant_food = [f for f in food if f[0] <= 3 * width and f[1] >= height]
    if len(quadrant_food) == 0:
      return food[0]
    ret_food = None
    if self.red:
      ret_food = max(quadrant_food, key=lambda f: f[1])
    ret_food = min(quadrant_food, key=lambda f: f[1])
    if isinstance(ret_food, list):
      return random.choice(ret_food)
    return ret_food
  
  def enemyInSight(self, gameState):
    opponents = self.getOpponents(gameState)
    width = gameState.data.layout.width/2
    current_position = gameState.getAgentPosition(self.index)
    if self.red and current_position[0] < width:
      return None
    elif not self.red and current_position[0] >= width:
      return None
    opponent_positions = [gameState.getAgentPosition(i) for i in opponents if gameState.getAgentPosition(i) is not None]
    if len(opponent_positions) == 0:
      return None
    # height = gameState.data.layout.height
    opps = None
    if self.red:
      opps = [opp for opp in opponent_positions if opp[0] >= width]
    else:
      opps = [opp for opp in opponent_positions if opp[0] < width]
    return opps if len(opps) > 0 else None
  
  def run(self, gameState, current_position, enemy_pos):
    addCapsules = self.getCapsules(gameState) + self.retreatNodes
    if self.currentGoal not in addCapsules:
      print addCapsules
      retreat = min(addCapsules, key=lambda n: self.getMazeDistance(n, current_position))
      print retreat
      if isinstance(retreat, list):
        retreat = retreat[0]
      self.currentGoal = retreat
    retreatDistance = self.getMazeDistance(self.currentGoal, current_position)
    qval = float('inf')
    return_action = None
    self.touches = 0
    for action in gameState.getLegalActions(self.index):
      if action == Directions.STOP:
        continue
      successor = self.getSuccessor(gameState, action)
      succ_pos = successor.getAgentState(self.index).getPosition()
      dist = self.getMazeDistance(succ_pos, enemy_pos)
      enemy_there = 1 if enemy_pos == current_position else 0
      qvalp = -10 * dist + retreatDistance + 100000*enemy_there
      print 'Action: ' + str(action) + ' qvalp: ' + str(qvalp)
      if qvalp < qval:
        qval = qvalp
        return_action = action
    return return_action
  
  def fetchNextGoal(self, gameState, current_position):
    if current_position in self.retreatNodes:
      self.lastRetreat = current_position
      if self.touched == 0:
        self.touched = 1
        return self.midpoint
    if current_position == self.midpoint:
      for retreat in self.retreatNodes:
        if retreat != self.lastRetreat:
          return retreat
    # Find the nearest food and set it as the goal
    foods = self.getFood(gameState).asList()
  #  print current_position
  #   print foods
    min_food = min(foods, key=lambda f: self.getMazeDistance(current_position, f))
    self.touched = 0
    if isinstance(min_food, list):
      return min_food[0]
    return min_food

  # def current_goal_in_territory
  
  def chooseAction(self, gameState):
    if self.currentGoal is None:
      self.currentGoal = self.getInitialGoal(gameState)
    current_position = gameState.getAgentState(self.index).getPosition()
    enemies_in_sight = self.enemyInSight(gameState)
    if enemies_in_sight is not None:
      min_enemy_pos = min(enemies_in_sight, key=lambda e: self.getMazeDistance(e, current_position))
      if isinstance(min_enemy_pos, list):
        min_enemy_pos = min_enemy_pos[0]
      if self.getMazeDistance(current_position, min_enemy_pos) <= 2:
        return self.run(gameState, current_position, min_enemy_pos)
    if current_position == gameState.getInitialAgentPosition(self.index):
      self.currentGoal = self.fetchNextGoal(gameState, current_position)
    if current_position == self.currentGoal:
      self.currentGoal = self.fetchNextGoal(gameState, current_position)
    return self.getActionFromMinDistance(gameState, self.currentGoal)

  def getSuccessor(self, gameState, action):
     """
     Finds the next successor which is a grid position (location tuple).
     """
     successor = gameState.generateSuccessor(self.index, action)
     pos = successor.getAgentState(self.index).getPosition()
     if pos != nearestPoint(pos):
       # Only half a grid position was covered
       return successor.generateSuccessor(self.index, action)
     else:
       return successor


class DAgent(CaptureAgent):
  def __init__( self, index, timeForComputing = .1 ):
    # Agent index for querying state
    self.index = index
    self.top = None
    # Whether or not you're on the red team
    self.red = None
    # Agent objects controlling you and your teammates
    self.agentsOnTeam = None
    # Maze distance calculator
    self.distancer = None
    # A history of observations
    self.observationHistory = []
    # Time to spend each turn on computing maze distances
    self.timeForComputing = timeForComputing
    # Access to the graphics
    self.display = None
    self.currentGoal = None

  def getRemovedNode(self, gameState):
    current_obs = self.getCurrentObservation()
    previous_obs = self.getPreviousObservation()
    if previous_obs is None:
      return None
    previous_food, current_food = None, None
    if self.red:
      previous_food = previous_obs.getRedFood().asList()
      current_food = current_obs.getRedFood().asList()
    else:
      previous_food = previous_obs.getBlueFood().asList()
      current_food = current_obs.getBlueFood().asList()
    if len(previous_food) == len(current_food):
      return None
    return [food for food in previous_food if food not in current_food]

  def capsuleTriggered(self, gameState):
    history = [self.observationHistory[i] for i in range(-40, 0) if len(self.observationHistory) >= 40]
    current_obs = self.getCurrentObservation()
    enemy = self.enemyInSight(gameState)
    if enemy is None:
        return None
    triggered = False
    if history > 0:
        for hist in history:
            if self.red:
                hist_capList = hist.getRedCapsules()
                curr_capList = current_obs.getRedCapsules()
            else:
                hist_capList = hist.getBlueCapsules()
                curr_capList = current_obs.getBlueCapsules()
            if  len(hist_capList) == len(curr_capList):
              continue
            else:
                triggered = True
    if triggered:
        return self.getActionFromMaxDistance(gameState,enemy[0])
    else:
        return None


  def getFarthestFood(self, gameState):
    current_obs = self.getCurrentObservation()
    current_position = gameState.getAgentState(self.index).getPosition()
    current_food = None
    if self.red:
      current_food = current_obs.getRedFood().asList()
    else:
      current_food = current_obs.getBlueFood().asList()
    maxpos = max(current_food, key=lambda pos: self.getMazeDistance(current_position, pos))
    if isinstance(maxpos, list):
      maxpos = random.choice(maxpos)
    return maxpos

  def enemyInSight(self, gameState):
    opponents = self.getOpponents(gameState)
    opponent_positions = [gameState.getAgentPosition(i) for i in opponents if gameState.getAgentPosition(i) is not None]
    if len(opponent_positions) == 0:
      return None
    width = gameState.data.layout.width/2
    # height = gameState.data.layout.height
    opps = None
    if self.red:
      opps = [opp for opp in opponent_positions if opp[0] < width]
    else:
      opps = [opp for opp in opponent_positions if opp[0] >= width]
    return opps if len(opps) > 0 else None

  def estimateNextAttackNode(self, last_known_location):
    current_obs = self.getCurrentObservation()
    current_food = None
    if self.red:
      current_food = current_obs.getRedFood().asList()
    else:
      current_food = current_obs.getBlueFood().asList()
    minpos = min(current_food, key=lambda pos: self.getMazeDistance(last_known_location, pos))
    if isinstance(minpos, list):
        minpos = random.choice(minpos)
    return minpos

  def getActionFromMinDistance(self, gameState, goal_pos):
    mindist = float('inf')
    chosen_action = None
    for action in gameState.getLegalActions(self.index):
      successor = self.getSuccessor(gameState, action)
      succ_pos = successor.getAgentState(self.index).getPosition()
      md = self.getMazeDistance(succ_pos, goal_pos)
      if md < mindist:
        chosen_action = action
        mindist = md
    return chosen_action

  def getActionFromMaxDistance(self, gameState, goal_pos):
    print goal_pos
    maxdist = float('-inf')
    chosenAction = None
    for action in gameState.getLegalActions(self.index):
        successor = self.getSuccessor(gameState, action)
        succ_pos = successor.getAgentState(self.index).getPosition()
        md = self.getMazeDistance(succ_pos, goal_pos)
        print 'Action: ' + str(action) + ' md: ' + str(md)
        if md > maxdist:
            chosenAction = action
            maxdist = md
    return chosenAction

  def chooseAction(self, gameState):
    current_position = gameState.getAgentState(self.index).getPosition()
    capsuleTriggered = self.capsuleTriggered(gameState)
    if capsuleTriggered is not None:
        return capsuleTriggered
    enemies_in_sight = self.enemyInSight(gameState)
    if enemies_in_sight is not None:
      minpos = min(enemies_in_sight, key=lambda pos: self.getMazeDistance(current_position, pos))
      if isinstance(minpos, list):
        minpos = random.choice(minpos)
      return self.getActionFromMinDistance(gameState, minpos)

    enemy_locations = self.getRemovedNode(gameState)
    if enemy_locations is not None:
      minpos = min(enemy_locations, key=lambda pos: self.getMazeDistance(current_position, pos))
      if isinstance(minpos, list):
        minpos = random.choice(minpos)
      self.currentGoal = self.estimateNextAttackNode(minpos)
      return self.getActionFromMinDistance(gameState, minpos)
    if current_position == self.currentGoal:
        self.currentGoal = self.patrol(gameState)
    if self.currentGoal is None:
      self.currentGoal = self.getFarthestFood(gameState)
    # print self.currentGoal
    return self.getActionFromMinDistance(gameState, self.currentGoal)

  def patrol(self, gameState):
      foodList = self.getFoodYouAreDefending(gameState).asList()

      closest_food = None
      pos = gameState.getAgentPosition(self.index)
      midDist = gameState.data.layout.width/2
      minDist1 = float("-inf")
      minDist2 = float("inf")
      for food in foodList:
          if self.red:
              if food[0] > minDist1:
                  minDist1 = food[0]
                  closest_food = food
          else:
              if food[0] < minDist2:
                  minDist2 = food[0]
                  closest_food = food
      return closest_food

  def getSuccessor(self, gameState, action):
     """
     Finds the next successor which is a grid position (location tuple).
     """
     successor = gameState.generateSuccessor(self.index, action)
     pos = successor.getAgentState(self.index).getPosition()
     if pos != nearestPoint(pos):
       # Only half a grid position was covered
       return successor.generateSuccessor(self.index, action)
     else:
       return successor


"""
  Idea 1 (Rush Strat):
    Basic Idea: Both agents available to us are on offense

    If the other team runs a standard 1 offense, 1 defense, we will be able to beat them.
    The idea is that one pacman runs diversion while the other scoops up pellets. When
    the diversion pacman (dp) dies, he runs an effecient defense back towards the other
    end of the field. The other pacman then becomes dp once the other pacman reenters the field.
"""

class Agent(CaptureAgent):
  def __init__( self, index, timeForComputing = .1 ):
    """
    Lists several variables you can query:
    self.index = index for this agent
    self.red = true if you're on the red team, false otherwise
    self.agentsOnTeam = a list of agent objects that make up your team
    self.distance = distance calculator (contest code provides this)
    self.observationHistory = list of GameState objects that correspond
        to the sequential order of states that have occurred so far this game
    self.timeForComputing = an amount of time to give each turn for computing maze distances
        (part of the provided distance calculator)
    """
    # Agent index for querying state
    self.index = index
    self.top = None
    # Whether or not you're on the red team
    self.red = None
    # Agent objects controlling you and your teammates
    self.agentsOnTeam = None
    # Maze distance calculator
    self.distancer = None
    # A history of observations
    self.observationHistory = []
    # Time to spend each turn on computing maze distances
    self.timeForComputing = timeForComputing
    # Access to the graphics
    self.display = None
    self.currentMPD = None
    self.currentGoal = None

  def isOnAttackingSide(self, gameState):
    ''' what if both ghosts choose defense?'''
    pos = gameState.getAgentPosition(self.index)
    if self.red:
      if pos[0] > gameState.data.layout.width/2:
        return True
    else:
      if pos[0] <= gameState.data.layout.width/2:
        return True
    return False

  def handleDefense(self, gameState):
    actions = [a for a in gameState.getLegalActions(self.index)] #if a != Directions.STOP]
    # for action in gameState.getLegalActions(self.index):
      # print 'Action: %s, dqval: %f' % (action, self.getDefenseQValue(gameState, action))
    a = max(gameState.getLegalActions(self.index), key=lambda action: self.getDefenseQValue(gameState, action))
    # print a
    return a

  def getMinPacmanDistance(self, gameState, action):
    successor = gameState.generateSuccessor(self.index, action)
    # Move in the direction of the nearest ghost
    opponents = self.getOpponents(successor)
    myPos = successor.getAgentState(self.index).getPosition()
    absoluteDistances = [(i, successor.getAgentPosition(i)) for i in opponents]
    actuals = [pos for pos in absoluteDistances if pos[1] is not None]
    if len(actuals) > 0:
      # print actuals
      dists = [(actual, self.getMazeDistance(myPos, actual[1])) for actual in actuals]
      return min(dists, key=lambda dist: dist[1])
    for i, pos in enumerate(absoluteDistances):
      if pos[1] is None:
        continue
      # dist = self.getMazeDistance(myPos, pos[1])
      absoluteDistances[i] = self.getMazeDistance(myPos, pos[1])
    ndistances = successor.getAgentDistances()
    # print 'ndistances: ' + str(ndistances)
    for i, tup in enumerate(absoluteDistances):
      if not isinstance(tup, tuple):
        continue
      opp_ind = tup[0]
      noisy_dist = ndistances[opp_ind]
      # Get the last 5 observations
      if len(self.observationHistory) < 6:
        absoluteDistances[i] = float('inf')
        continue
      ndists = []
      for obsi in range(-2, -7):
        obs = self.observationHistory[obsi]
        ndists.append(obs.getAgentDistances()[opp_ind])
      ndists.append(noisy_dist)
      # Find distance averaged over 5 observations and the newest one
      avg = sum(ndists)/len(ndists) if len(ndists) > 0 else None
      if avg is None:
        absoluteDistances[i] = float('inf')
        continue
      # print 'Action: %s, Ghost Index: %d Expected Distance: %d' % (action, i, avg)
      absoluteDistances[i] = avg
    # print absoluteDistances
    return min(absoluteDistances)

  def getMinFoodDistance(self, gameState, action):
    successor = gameState.generateSuccessor(self.index, action)
    foodList = self.getFood(successor).asList()
    myPos = successor.getAgentState(self.index).getPosition()
    return min([self.getMazeDistance(myPos, food) for food in foodList])

  def stateContainsEnemy(self, gameState, action):
    successor = gameState.generateSuccessor(self.index, action)
    opponents = self.getOpponents(gameState)
    successorPos = successor.getAgentState(self.index).getPosition()
    opponentPositions = [gameState.getAgentPosition(i) for i in opponents]
    opponentPositions = [(float(i[0]), float(i[1])) for i in opponentPositions if i is not None]
    # print opponentPositions
    # print successorPos
    if successorPos in opponentPositions:
      return 1
    return 0

  def setCurrentGoal(self, mpd, currentPos, height, width):
    positions = []
    dx = math.sqrt(mpd/2)
    if currentPos[1] + mpd < height - 1:
      # print currentPos[1] + mpd
      positions.append((currentPos[0], currentPos[1] + mpd))
    if currentPos[1] - mpd > -1:
      positions.append((currentPos[0], currentPos[1] - mpd))
    if self.red:
      positions.append((currentPos[0] + mpd, currentPos[1]))
      positions.append((currentPos[0] + dx, currentPos[1] + dx))
      positions.append((currentPos[0] + dx, currentPos[1] - dx))
    else:
      positions.append((currentPos[0] - mpd, currentPos[1]))
      positions.append((currentPos[0] - dx, currentPos[1] + dx))
      positions.append((currentPos[0] - dx, currentPos[1] - dx))
    self.currentGoal = random.choice(positions)

  def getDQVal(self, gameState, action):
    successor = self.getSuccessor(gameState, action)
    # mfd = self.getMinFoodDistance(gameState, action)
    mpd = self.getMinPacmanDistance(gameState, action)
    if isinstance(mpd, tuple):
      self.currentGoal = mpd[0][1]

      # print self.currentGoal
      return mpd[1]
    # Given a mpd
    dqval = 0
    currentPos = successor.getAgentPosition(self.index)
    # print 'MPD: ' + str(mpd)
    width = gameState.data.layout.width/2
    height = gameState.data.layout.height
    if mpd > 5:
      if self.currentMPD is None:
        self.currentMPD = mpd
        self.currentGoal = (width - 4, height - 4)
      else:
        if mpd < self.currentMPD + 8:
          self.currentMPD = mpd
          if self.currentGoal == (width - 4, height - 4):
            self.setCurrentGoal(mpd, currentPos, height, width)
        else:
          # print 'Current Position: ' + str(currentPos)
          positions = []
          if mpd == float('inf'):
            pass
            # self.currentGoal = (width - 4, height - 4)
          else:
            self.setCurrentGoal(mpd, currentPos, height, width)
    # print self.currentGoal
    flag = False
    # print self.distancer._distances
    diff = 1
    if self.red:
      diff = -1
    walls = gameState.getWalls()
    nonwalls = []
    for x in range(0, walls.width):
      for y in range(0, walls.height):
        if not gameState.hasWall(x, y):
          nonwalls.append((x, y))
    def distance(a, b):
      return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
    self.currentGoal =  min(nonwalls, key=lambda x: distance(self.currentGoal, x))
    dqval = self.distancer.getDistance(currentPos, self.currentGoal)
    if dqval == 0.0:
      self.setCurrentGoal(mpd, currentPos, height, width)
    # print self.currentGoal
    return dqval

  def getDefenseQValue(self, gameState, action):
    dqval = self.getDQVal(gameState, action)
    sce = self.stateContainsEnemy(gameState, action)
    if sce:
      return float('inf')
    return -dqval

  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    if not self.isOnAttackingSide(gameState):
      return self.handleDefense(gameState)
    actions = gameState.getLegalActions(self.index)

    '''
    You should change this in your own agent.
    '''

    values = [self.evaluate(gameState, a) for a in actions]
    # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]
    return random.choice(bestActions)

  def distanceToTeammates(self, gameState, action):
    successor = self.getSuccessor(gameState, action)
    my_team = self.getTeam(gameState)
    my_team_not_me = [i for i in my_team if i != self.index]
    mypos = successor.getAgentState(self.index).getPosition()
    dists = []
    for i in my_team_not_me:
      pos = gameState.getAgentPosition(i)
      if pos is None:
        continue
      dists.append(self.getMazeDistance(mypos, pos))
    return min(dists) if len(dists) > 0 else 0

  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)
    opponents = self.getOpponents(successor)
    myPos = successor.getAgentState(self.index).getPosition()
    absoluteDistances = map(lambda i: successor.getAgentPosition(i), opponents)
    # Compute distance to the nearest food
    foodList = self.getFood(successor).asList()
    if len(foodList) > 0: # This should always be True,  but better safe than sorry
      myPos = successor.getAgentState(self.index).getPosition()
      minDistanceFood = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['distanceToFood'] = minDistanceFood
      for i, pos in enumerate(absoluteDistances):
        if pos is None:
          continue
        dist = self.getMazeDistance(myPos, pos)
        absoluteDistances[i] = self.getMazeDistance(myPos, pos)
        capList = gameState.getCapsules()
        minDistanceCap = min([self.getMazeDistance(myPos, cap) for cap in capList]) if len(capList) > 0 else 0
        opponents_pos = map(lambda i: successor.getAgentPosition(i), opponents)
        close_opponents = [opp for opp in opponents_pos if opp is not None]
        opponent_nearby = len(close_opponents) != 0
        if opponent_nearby:
          features['distanceToOpp'] = minDistanceFood
          distances = [self.getMazeDistance(myPos, pos) for pos in close_opponents]
          walls = successor.getWalls()
          wall_counter = 0
          for i in range(-1, 2):
            for j in range(-1, 2):
              if i == j or -j == i:
                continue
              if successor.hasWall(int(myPos[0] + i), int(myPos[1] + j)):
                wall_counter += 1
          mindist = min(distances)
          if mindist < 4:
            if wall_counter == 3:
              features['wall_penalty'] = 1
            # print wall_countexw
            features['distanceToOpp'] = min(distances)
            features['distanceToFood'] = 0#minDistanceFood
        else:
          features['distanceToOpp'] = 0
    features['distanceToTeammate'] = self.distanceToTeammates(gameState, action)
    # print 'Distane to Teammate: ' + str(features['distanceToTeammate'])
    return features

  def getWeights(self, gameState, action):
     return {'successorScore': 100000, 'distanceToFood': -10, 'distanceToTeammate': 2, 'distanceToOpp': 20, 'wall_penalty': -100000}

  def evaluate(self, gameState, action):
   """
   Computes a linear combination of features and feature weights
   """
   features = self.getFeatures(gameState, action)
   weights = self.getWeights(gameState, action)
   return features * weights

  def getSuccessor(self, gameState, action):
     """
     Finds the next successor which is a grid position (location tuple).
     """
     successor = gameState.generateSuccessor(self.index, action)
     pos = successor.getAgentState(self.index).getPosition()
     if pos != nearestPoint(pos):
       # Only half a grid position was covered
       return successor.generateSuccessor(self.index, action)
     else:
       return successor

class ReflexCaptureAgent(CaptureAgent):
  """
  A base class for reflex agents that chooses score-maximizing actions
  """
  def chooseAction(self, gameState):
    """
    Picks among the actions with the highest Q(s,a).
    """
    actions = gameState.getLegalActions(self.index)

    # You can profile your evaluation time by uncommenting these lines
    # start = time.time()
    values = [self.evaluate(gameState, a) for a in actions]
    # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]

    return random.choice(bestActions)

  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def evaluate(self, gameState, action):
    """
    Computes a linear combination of features and feature weights
    """
    features = self.getFeatures(gameState, action)
    weights = self.getWeights(gameState, action)
    return features * weights

  def getFeatures(self, gameState, action):
    """
    Returns a counter of features for the state
    """
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)
    return features

  def getWeights(self, gameState, action):
    """
    Normally, weights do not depend on the gamestate.  They can be either
    a counter or a dictionary.
    """
    return {'successorScore': 1.0}

class OffensiveReflexAgent(ReflexCaptureAgent):
  """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """



  def getWeights(self, gameState, action):
    return {'successorScore': 100, 'distanceToFood': -1}

class DummyAgent(CaptureAgent):
  """
  A Dummy agent to serve as an example of the necessary agent structure.
  You should look at baselineTeam.py for more details about how to
  create an agent as this is the bare minimum.
  """

  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).

    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)

    IMPORTANT: This method may run for at most 15 seconds.
    """

    '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
    CaptureAgent.registerInitialState(self, gameState)

    '''
    Your initialization code goes here, if you need any.
    '''


  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    actions = gameState.getLegalActions(self.index)

    '''
    You should change this in your own agent.
    '''

    return random.choice(actions)
