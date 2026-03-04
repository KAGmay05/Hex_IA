def get_neighbors( board, row, col):
    size = board.size

    if row % 2 == 0:
       directions = [
           (-1,0),
           (-1,-1),
           (0,-1),
           (0,1),
           (1,0),
           (1,-1)
       ]

    else :
        directions = [
            (-1,0),
            (-1,1),
            (0,-1),
            (0,1),
            (1,0),
            (1,1)
        ]   

    neighbors = []

    for dr, dc in directions:
        nr, nc = row + dr, col + dc
        if 0 <= nr < size and 0 <= nc < size:
            neighbors.append((nr,nc))

def has_won(board: HexBoard, player_id: int) -> bool:
    size = board.size
    visited = set()

    def dfs_visit(row, col):
        visited.add((row, col))

        if player_id == 1 and row == size - 1:
            return True
        if player_id == 2 and col == size - 1:
            return True
        
        for nr, nc in get_neighbors(board,row,col):
            if (nr, nc) not in visited and board.board[nr][nc] == player_id:
                if dfs_visit(nr, nc):
                    return True
                
        return False

    if player_id == 1:
        for row in range(size):
            if board.board[row][0] == 1 and (row, 0) not in visited:
                if dfs_visit(row, 0):
                    return True
                
                else:
                    for col in range(size):
                        if board.board[0][col] == 2 and (0, col) not in visited:
                            if dfs_visit(0, col):
                                return True               




