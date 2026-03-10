from player import Player
from board import HexBoard
import random
import time
import heapq
from math import sqrt, log

def get_neighbors(board, row, col):
    size = board.size

    # even-r layout: even rows shifted right
    if row % 2 == 0:
        directions = [
            (-1, 0), (-1, 1),
            (0, -1), (0, 1),
            (1, 0), (1, 1)
        ]
    else:
        directions = [
            (-1, -1), (-1, 0),
            (0, -1), (0, 1),
            (1, -1), (1, 0)
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


class _UF:
    __slots__ = ['parent', 'rank']

    def __init__(self, n):
        total = n * n + 4
        self.parent = list(range(total))
        self.rank = [0] * total

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1

    def connected(self, a, b):
        return self.find(a) == self.find(b)


class _MCTSNode:
    __slots__ = ['move', 'parent', 'player_just_moved', 'children',
                 'wins', 'visits', 'untried_moves', 'amaf_wins', 'amaf_visits']

    def __init__(self, move=None, parent=None, player_just_moved=None):
        self.move = move
        self.parent = parent
        self.player_just_moved = player_just_moved
        self.children = []
        self.wins = 0.0
        self.visits = 0
        self.untried_moves = []
        self.amaf_wins = {}
        self.amaf_visits = {}

    def select_child_rave(self, exploration=0.7, rave_const=300):
        log_parent = log(self.visits)
        best_score = float('-inf')
        best_child = None

        for c in self.children:
            exploit = c.wins / c.visits
            explore = exploration * sqrt(log_parent / c.visits)
            uct = exploit + explore

            an = self.amaf_visits.get(c.move, 0)
            if an > 0:
                amaf = self.amaf_wins[c.move] / an
                beta = an / (an + c.visits + an * c.visits / rave_const)
                score = (1 - beta) * uct + beta * amaf
            else:
                score = uct

            if score > best_score:
                best_score = score
                best_child = c

        return best_child

    def add_child(self, move, player_just_moved):
        child = _MCTSNode(move=move, parent=self, player_just_moved=player_just_moved)
        self.untried_moves.remove(move)
        self.children.append(child)
        return child


class SmartPlayer(Player):

    def __init__(self, player_id):
        super().__init__(player_id)
        self.opponent = 3 - player_id
        self.time_limit = 2.0

    def play(self, board):
        size = board.size

        if all(board.board[r][c] == 0 for r in range(size) for c in range(size)):
            return (size // 2, size // 2)

        self._neighbors = {}
        for r in range(size):
            for c in range(size):
                self._neighbors[(r, c)] = get_neighbors(board, r, c)

        all_empties = [(r, c) for r in range(size) for c in range(size) if board.board[r][c] == 0]

        if len(all_empties) == 1:
            return all_empties[0]

        for r, c in all_empties:
            board.board[r][c] = self.player_id
            if has_won(board, self.player_id):
                board.board[r][c] = 0
                return (r, c)
            board.board[r][c] = 0

        for r, c in all_empties:
            board.board[r][c] = self.opponent
            if has_won(board, self.opponent):
                board.board[r][c] = 0
                return (r, c)
            board.board[r][c] = 0

        root = _MCTSNode(player_just_moved=self.opponent)
        root.untried_moves = list(all_empties)

        start = time.time()
        sim_count = 0

        while time.time() - start < self.time_limit:
            node = root
            state = board.clone()

            while not node.untried_moves and node.children:
                node = node.select_child_rave()
                state.place_piece(node.move[0], node.move[1], node.player_just_moved)

            if node.untried_moves:
                next_player = 3 - node.player_just_moved
                move = random.choice(node.untried_moves)
                state.place_piece(move[0], move[1], next_player)
                node = node.add_child(move, next_player)

                node.untried_moves = [
                    (r, c) for r in range(size) for c in range(size)
                    if state.board[r][c] == 0
                ]

            p1_moves, p2_moves, winner = self._simulate_uf(state, 3 - node.player_just_moved, size)
            sim_count += 1

            while node is not None:
                node.visits += 1
                if node.player_just_moved == winner:
                    node.wins += 1

                ptm = 3 - node.player_just_moved
                won = (winner == ptm)
                moves_for_ptm = p1_moves if ptm == 1 else p2_moves
                aw = node.amaf_wins
                av = node.amaf_visits
                for mv in moves_for_ptm:
                    if mv in av:
                        av[mv] += 1
                        if won:
                            aw[mv] += 1
                    else:
                        av[mv] = 1
                        aw[mv] = 1.0 if won else 0.0

                node = node.parent

        if not root.children:
            return root.untried_moves[0] if root.untried_moves else None

        return max(root.children, key=lambda c: c.visits).move

    def _simulate_uf(self, board, next_player, size):
        brd = [row[:] for row in board.board]  
        nbrs = self._neighbors
        nn = size * size
        TOP, BOTTOM, LEFT, RIGHT = nn, nn + 1, nn + 2, nn + 3

        uf1 = _UF(size)  # player 1: LEFT-RIGHT
        uf2 = _UF(size)  # player 2: TOP-BOTTOM

       
        for r in range(size):
            for c in range(size):
                cell = brd[r][c]
                if cell == 0:
                    continue
                idx = r * size + c
                if cell == 1:
                    if c == 0:
                        uf1.union(idx, LEFT)
                    if c == size - 1:
                        uf1.union(idx, RIGHT)
                    for nr, nc in nbrs[(r, c)]:
                        if brd[nr][nc] == 1:
                            uf1.union(idx, nr * size + nc)
                else:
                    if r == 0:
                        uf2.union(idx, TOP)
                    if r == size - 1:
                        uf2.union(idx, BOTTOM)
                    for nr, nc in nbrs[(r, c)]:
                        if brd[nr][nc] == 2:
                            uf2.union(idx, nr * size + nc)

        empties = []
        for r in range(size):
            for c in range(size):
                if brd[r][c] == 0:
                    empties.append((r, c))

        random.shuffle(empties)
        p1_moves = []
        p2_moves = []
        current = next_player

        for r, c in empties:
            brd[r][c] = current
            idx = r * size + c

            if current == 1:
                p1_moves.append((r, c))
                if c == 0:
                    uf1.union(idx, LEFT)
                if c == size - 1:
                    uf1.union(idx, RIGHT)
                for nr, nc in nbrs[(r, c)]:
                    if brd[nr][nc] == 1:
                        uf1.union(idx, nr * size + nc)
            else:
                p2_moves.append((r, c))
                if r == 0:
                    uf2.union(idx, TOP)
                if r == size - 1:
                    uf2.union(idx, BOTTOM)
                for nr, nc in nbrs[(r, c)]:
                    if brd[nr][nc] == 2:
                        uf2.union(idx, nr * size + nc)

            current = 3 - current

        # Player 1 wins if LEFT connected to RIGHT
        winner = 1 if uf1.connected(LEFT, RIGHT) else 2
        return p1_moves, p2_moves, winner
