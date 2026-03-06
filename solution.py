from player import Player
from board import HexBoard
import random
import time
import heapq


def get_neighbors(board, row, col):
    size = board.size

    if row % 2 == 0:
        directions = [
            (-1,0),(-1,-1),
            (0,-1),(0,1),
            (1,0),(1,-1)
        ]
    else:
        directions = [
            (-1,0),(-1,1),
            (0,-1),(0,1),
            (1,0),(1,1)
        ]

    neighbors = []

    for dr,dc in directions:
        nr,nc=row+dr,col+dc
        if 0<=nr<size and 0<=nc<size:
            neighbors.append((nr,nc))

    return neighbors


def has_won(board, player_id):

    size=board.size
    visited=set()

    def dfs(r,c):

        visited.add((r,c))

        if player_id==1 and c==size-1:
            return True

        if player_id==2 and r==size-1:
            return True

        for nr,nc in get_neighbors(board,r,c):

            if (nr,nc) not in visited and board.board[nr][nc]==player_id:

                if dfs(nr,nc):
                    return True

        return False

    if player_id==1:

        for r in range(size):

            if board.board[r][0]==1:

                if dfs(r,0):
                    return True

    else:

        for c in range(size):

            if board.board[0][c]==2:

                if dfs(0,c):
                    return True

    return False


def shortest_path(board,player):

    size=board.size
    pq=[]
    dist={}

    opponent=3-player

    if player==1:

        for r in range(size):

            cost=0

            if board.board[r][0]==opponent:
                cost=100
            elif board.board[r][0]==0:
                cost=1

            heapq.heappush(pq,(cost,r,0))
            dist[(r,0)]=cost

    else:

        for c in range(size):

            cost=0

            if board.board[0][c]==opponent:
                cost=100
            elif board.board[0][c]==0:
                cost=1

            heapq.heappush(pq,(cost,0,c))
            dist[(0,c)]=cost


    while pq:

        cost,r,c=heapq.heappop(pq)

        if player==1 and c==size-1:
            return cost

        if player==2 and r==size-1:
            return cost

        for nr,nc in get_neighbors(board,r,c):

            cell=board.board[nr][nc]

            if cell==opponent:
                new_cost=cost+100
            elif cell==0:
                new_cost=cost+1
            else:
                new_cost=cost

            if (nr,nc) not in dist or new_cost<dist[(nr,nc)]:

                dist[(nr,nc)]=new_cost
                heapq.heappush(pq,(new_cost,nr,nc))

    return 100


def evaluate(board,player):

    opponent=3-player

    my_dist=shortest_path(board,player)
    opp_dist=shortest_path(board,opponent)

    return opp_dist-my_dist


class SmartPlayer(Player):

    def __init__(self,player_id):

        super().__init__(player_id)

        self.opponent=3-player_id
        self.time_limit=2.0


    def play(self,board):

        start=time.time()

        moves = self.get_candidate_moves(board)

        best_move=random.choice(moves)
        best_score=-999999

        while time.time()-start<self.time_limit:

            move = random.choice(moves[:min(20,len(moves))])

            new_board=board.clone()
            new_board.place_piece(move[0],move[1],self.player_id)

            score=self.rollout(new_board)

            if score>best_score:
                best_score=score
                best_move=move

        return best_move


    def rollout(self, board):

      current = self.opponent

      while True:

        if has_won(board, self.player_id):
            return 1

        if has_won(board, self.opponent):
            return -1

        moves = self.get_candidate_moves(board)

        if not moves:
            return evaluate(board, self.player_id)

        best_move = None
        best_score = -999999

        for move in moves:

            new_board = board.clone()
            new_board.place_piece(move[0], move[1], current)

            score = evaluate(new_board, current)

            if score > best_score:
                best_score = score
                best_move = move

        board.place_piece(best_move[0], best_move[1], current)

        current = 3 - current
    
   
    def get_candidate_moves(self, board):

      size = board.size
      candidates = set()

      for r in range(size):
        for c in range(size):

            if board.board[r][c] != 0:

                for nr, nc in get_neighbors(board, r, c):

                    if board.board[nr][nc] == 0:
                        candidates.add((nr, nc))

      if candidates:
        return list(candidates)

      return [
        (i, j)
        for i in range(size)
        for j in range(size)
        if board.board[i][j] == 0
      ]   