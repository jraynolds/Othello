import random

def get_location_type(location, board_width):
	"""
	Returns the type of location passed, according to the width of the board
	provided. 
	"Corner" returns 3. 
	"Edge" returns 2.
	Otherwise returns 1.
	"""
	corners = (0, board_width - 1)
	if location[0] in corners and location[1] in corners:
		return 3
	if location[0] in corners or location[1] in corners:
		return 2
	return 1

class Othello:
	"""
	A game object to hold the board game Othello, also known as Reversi.

	Attributes:
		board:	a 2D list of integers representing the board state and the tokens on it. 
				1 for white, 2 for black, 0 for empty. Optional if width and height are given.
		width:	The width of the game board. Optional if board is given.
	"""
	def __init__(self, board, width=None):
		"""
		Constructor. Breaks if neither board nor width are provided.
		If a board is given, then it makes a deep copy.
		If width are given, it constructs a starting board state from the width.
		Width must be even. A square board is assumed.
		"""
		assert(board != None or width != None)

		if board:
			self.board = [[x for x in row] for row in board]
		else :
			assert(width != None)
			assert(width % 2 == 0)
			self.board = [[0 for _ in range(width)] for _ in range(width)]
			middle_top_left = (int(width/2) - 1, int(width/2) - 1)

			self.board[middle_top_left[1]][middle_top_left[0]] = 1
			self.board[middle_top_left[1] + 1][middle_top_left[0] + 1] = 1
			self.board[middle_top_left[1] + 1][middle_top_left[0]] = 2
			self.board[middle_top_left[1]][middle_top_left[0] + 1] = 2

	def play_move(self, location, player):
		"""
		Places the player's token at the location provided.
		Then flips all appropriate tokens at orthogonal and diagonal directions.
		"""
		self.board[location[1]][location[0]] = player

		flipped = self.get_flipped(location, player)

		for flip in flipped:
			self.board[flip[1]][flip[0]] = player

	def to_string(self):
		"""
		Converts the game state into an easy-to-read string.
		"""
		# symbols = {0: "0", 1: u'\u26ab', 2: u'\u26aa'}
		# symbols = {0: " ", 1: u'\u2713', 2: u'\u2713'}

		output = "  "
		for i in range(len(self.board[0])):
			output += str(i) + " "
		output = output[:-1] + "\n"

		i = 0
		for row in self.board:
			line = str(i) + " "
			for cell in row:
				line += str(cell) + " "
			output += line[:-1] + "\n"
			i += 1

		return output

	def _get_available_moves(self, player):
		"""
		Finds all available moves for a player. These are empty spaces adjacent to at least
		one pre-existing token, and where placing a token would flip at least one other.
		Note that a player can have no available play spots in normal play.
		"""
		available = []

		for y in range(len(self.board)):
			for x in range(len(self.board[0])):
				if self.board[y][x] == 0:
					if self.get_flipped((x, y), player):
						available.append((x,y))

		return available

	def is_on_board(self, location):
		"""
		Returns whether a location is a valid spot on the game board.
		"""
		return location[0] >= 0 and location[1] >= 0 and location[1] + 1 <= len(self.board) and location[0] + 1 <= len(self.board[0])

	def get_flipped(self, location, player):
		"""
		Returns a list of tokens that would be flipped to the given player's color if he
		were to play on the location given.
		These are tokens that become "sandwiched" by one of the player's color and the token
		he just placed, in any direction.
		"""
		flipped = []

		for x in range(-1, 2):
			for y in range(-1, 2):
				flip = []
				temp_loc = (location[0] + x, location[1] + y)
				while(True):
					if not self.is_on_board(temp_loc):
						flip = []
						break

					tile = self.board[temp_loc[1]][temp_loc[0]]
					if tile == 0:
						flip = []
						break
					if tile == player:
						break

					flip.append(temp_loc)
					temp_loc = (temp_loc[0] + x, temp_loc[1] + y)
				flipped.extend(flip)

		return flipped

	def get_children(self, player):
		"""
		Returns a list of all Othello states from available moves the given player can make.
		"""
		moves = self._get_available_moves(player)
		children = []

		for move in moves:
			child = Othello(self.board)
			child.play_move(move, player)
			children.append(child)

		return children

	def get_state_value(self, player):
		"""
		Returns the number of tokens the player has on the board.
		"""
		value = 0

		for row in self.board:
			for cell in row:
				if cell == player:
					value += 1

		return value

	def _is_state_terminal(self):
		"""
		Returns true if there are no spots, or if neither player can make a valid
		move.
		"""
		num_empties = self.get_state_value(0)

		if num_empties == 0:
			return True

		if self._get_available_moves(1):
			return False
		if self._get_available_moves(2):
			return False
			
		return True

	def get_best_move(self, player, plies):
		"""
		Returns the best move for a given player to take, looking ahead by a 
		given number of plies.
		"""
		moves = self._get_available_moves(player)

		best_move = (None, -float("inf"))
		for move in moves:
			if not move:
				continue
			child = Othello(self.board)
			child.play_move(move, player)
			score = child.negamax(player, plies - 1, -float("inf"), float("inf"), True)
			if score > best_move[1]:
				best_move = (move, score)

			if score == best_move[1]:
				# we prefer corner to edge to other locations.
				if not best_move[0] or get_location_type(move, len(self.board)) > get_location_type(best_move[0], len(self.board)):
					best_move = (move, score)

		return best_move[0]

	def negamax(self, player, depth, a, b, isPruning):
		"""
		Negamax function. Compares state values recursively.
		"""
		players = {1:2, 2:1}

		game_is_over = self._is_state_terminal()
		if depth == 0 or game_is_over:
			return self.get_state_value(player)

		best = -float("inf")

		children = self.get_children(players[player])
		random.shuffle(children)

		for child in children:
			value = child.negamax(players[player], depth-1, -b, -a, isPruning)
			best = max(best, value)

			# Prunes low-value children. Alpha-beta.
			if isPruning:
				a = max(a, value)
				if a >= b:
					break

		return -best

class ComputerPlayer:
	"""
	A computer player object to be called upon in order to pick ideal game moves.

	Attributes:
		player_ID: 			the number corresponding to the tiles this player lays. Must be 1 or 2.
		difficulty_level:	the number of plies this computer player will look ahead
							during its search. Defaults to 1, which only evaluates all immediate moves.
	"""
	def __init__(self, player_ID, difficulty_level):
		"""
		Constructor, takes a difficulty level (the # of plies to look
		ahead), and a player ID, either 1 or 2.
		"""
		self.player_ID = player_ID
		self.difficulty_level = difficulty_level

		assert (self.player_ID == 1 or self.player_ID == 2), "The player must be set to 1 or 2!"

		if self.difficulty_level == None or self.difficulty_level < 1:
			print("Difficulty level has been raised to its minimum of 1.")
			self.difficulty_level = 1

	def pick_move(self, board):
		"""
		Returns the best column for the player to play in, given the board state passed.
		"""
		othello = Othello(board)
		return othello.get_best_move(self.player_ID, self.difficulty_level)