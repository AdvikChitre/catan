import Board
import Bank

game_over = False

def main(players):
    numPlayers = len(players)

    # Game setup
        # setup states
    board = Board.setupBord()
    bank = Bank.setupBank(numPlayers)

    # Setup phase
        # Roll die for each player to get order
    playerOrder = [players]
        # place in order
        # place in reverse order + receive resources

    # Play phase
    turn = 0
    while(not game_over):
        turnPlayer = playerOrder[turn % numPlayers]
        # 1. check dev card
        # 2. roll
        # 3. distribute resources
        # 4. takeTurn till END
        # 5. check for victory

if __name__ == "__main__":
    main()
