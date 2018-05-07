"""
Othello / Reversi

This program creates a "Othello" game, also known as "Reversi." 
If you are unfamiliar with the game, rules may be found at
https://en.wikipedia.org/wiki/Reversi.

By default, one player will be human and the other player will be a computer
player, whose AI is contained in the file "othelloplayer.py". This will have a
class called ComputerPlayer, that has two public methods. The __init__() method
will take an int that indicates the number of plies to look ahead, and an
int that is the value of the player's tiles.  The pick_move() method will take a 
2D int list of the board's current layout. It will return a tuple location, x and y,
indicating the space it wishes to play. (Note that if a play would flip no tiles, 
playing there is an invalid move.)

This file originally was developed by Adam Smith for use in a Connect 4 game.
It has been adapted by Jasper Raynolds for Othello/Reversi.
"""
__author__ = "Adam A. Smith, edits made by Jasper Raynolds"
__license__ = "MIT"
__date__ = "May 2018"

import sys
import random
from functools import partial

################################################################################
# CONSTANTS
################################################################################

DEFAULT_PLAYER1_COLOR = "#ffffff" # black
DEFAULT_PLAYER2_COLOR = "#000000" # white
BOARD_COLOR = "#00ff00" # green
BACKGROUND_COLOR = "#000000" # black
SQUARE_SIZE = 75
DEFAULT_AI_LEVEL = 4
DEFAULT_AI_FILE = "othelloplayer"
PLAYERS = {1: "White", 2: "Black"}

HALF_SQUARE = SQUARE_SIZE // 2

class HumanPlayer:
	pass

################################################################################
# APPLICATION CLASS & GRAPHICS STUFF
################################################################################

# Does tkinter even exist on this computer? If not, don't do graphics.
try:
	import tkinter as tk
	from PIL import Image, ImageDraw, ImageTk
	do_graphics = True

	class App(tk.Tk):
		def __init__(self, players = None, player_colors = None, grid_size = 8):
			tk.Tk.__init__(self)
			self.title("Othello")
			self.configure(bg=BACKGROUND_COLOR)

			# parse the passed players to set the field holding the AIs
			if players == None or len(players) == 0: self.players = (None, HumanPlayer(), HumanPlayer())
			elif len(players) == 1: self.players = (None, HumanPlayer(), players[0])
			elif len(players) == 2: self.players = (None, players[0], players[1])
			elif len(players) == 3: self.players = players

			# parse the player color args, define the color strings we'll need
			if player_colors == None:
				player_color_tuples = (None, self._make_color_tuple(DEFAULT_PLAYER1_COLOR), self._make_color_tuple(DEFAULT_PLAYER2_COLOR))
			elif len(player_colors) == 2:
				player_color_tuples = (None, self._make_color_tuple(player_colors[0]), self._make_color_tuple(player_colors[1]))

			self.color_strs = (None, App._make_color_string(player_color_tuples[1]), App._make_color_string(player_color_tuples[2]))

			# make the necessary images
			self.overlay_image = self._make_board_image()
			self.disc1_image = self._make_disc_image(player_color_tuples[1])
			self.disc2_image = self._make_disc_image(player_color_tuples[2])
			self.wm_iconphoto(self, App._make_icon())
			
			# other data structures
			self.board = [[0 for x in range(grid_size)] for y in range(grid_size)]

			# start forming up the screen--here's the top banner
			self.top_banner = tk.Label(self, bg="#ffffff", font=("Arial", 20))
			self.top_banner.grid(column=1, row=1, columnspan=grid_size)

			# buttons
			self.buttons = []

			self.canvas = tk.Canvas(width = grid_size*SQUARE_SIZE, height = grid_size*SQUARE_SIZE, bg=BACKGROUND_COLOR, highlightthickness=0)
			self.canvas.grid(column=1, row=3, columnspan=grid_size)

			self.discs = {}
			# make the board
			for r in range(grid_size):
				for c in range(grid_size):
					self.canvas.create_image((c*SQUARE_SIZE+HALF_SQUARE,r*SQUARE_SIZE+HALF_SQUARE), image=self.overlay_image)

			# place initial tokens
			middle_top_left = (int(grid_size/2) - 1, int(grid_size/2) - 1, False)
			self._place_disc((middle_top_left[1], middle_top_left[0]), 1, False)
			self._place_disc((middle_top_left[1] + 1, middle_top_left[0] + 1), 1, False)
			self._place_disc((middle_top_left[1], middle_top_left[0] + 1), 2, False)
			self._place_disc((middle_top_left[1] + 1, middle_top_left[0]), 2, False)

			# black player goes 1st
			self._set_player(2)
					
		# actually make a play--modifies the board, and switches turns if game_started
		def _place_disc(self, location, player_num = None, game_started = True):
			# Clear all buttons
			for button in self.buttons:
				button.destroy()
			self.buttons = []

			if player_num == None: player_num = self.current_player

			# create the new disc
			if player_num == 1: image = self.disc1_image
			else: image = self.disc2_image
			new_disc = self.canvas.create_image((location[0]*SQUARE_SIZE + HALF_SQUARE, location[1]*SQUARE_SIZE + HALF_SQUARE), image=image)
			self.board[location[1]][location[0]] = player_num
			self.discs[location] = new_disc

			# flip disks
			for flip in self._get_flipped(location, player_num):
				self._flip_token(flip)

			if game_started:
				self._swap_player()

		# handle the UI aspect of the victory
		def _declare_victory(self):
			tokens = {1:0, 2:0}
			for row in self.board:
				for cell in row:
					if cell is not 0:
						tokens[cell] += 1

			winstring = " player wins,"
			if tokens[1] > tokens[2]:
				winstring = "White" + winstring
			elif tokens[2] > tokens[1]:
				winstring = "Black" + winstring
			else :
				winstring = "tie game,"
			winstring += " with " + str(max(tokens[1], tokens[2])) + " tokens!"

			self.top_banner.config(text=winstring)

		# switch players
		def _swap_player(self):
			if self.current_player == 1: self._set_player(2)
			else: self._set_player(1)

		# Returns a list of tokens that would be flipped to the given player's color if he
		# were to play on the location given.
		def _get_flipped(self, location, player):
			flipped = []

			for x in range(-1, 2):
				for y in range(-1, 2):
					flip = []
					temp_loc = (location[0] + x, location[1] + y)
					while(True):
						if not self._is_on_board(temp_loc):
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

		# Returns whether a location is a valid spot on the game board.
		def _is_on_board(self, location):
			return location[0] >= 0 and location[1] >= 0 and location[1] + 1 <= len(self.board) and location[0] + 1 <= len(self.board[0])

		# returns a list of all valid locations to play
		def _get_valid_moves(self, player):
			available = []

			for y in range(len(self.board)):
				for x in range(len(self.board[0])):
					if self.board[y][x] == 0:
						if self._get_flipped((x, y), player):
							available.append((x,y))

			return available

		# change to the specified player
		def _set_player(self, player_id):
			self.current_player = player_id
			valid_moves = self._get_valid_moves(player_id)
			if not valid_moves:
				# print("player " + str(player_id) + ", " + PLAYERS[player_id] + ", has no moves.")
				if not self._get_valid_moves(1) and not self._get_valid_moves(2):
					self._declare_victory()
					return
				else :
					self._swap_player()
					return

			# if the next player is human, set the banner & activate the appropriate buttons
			if type(self.players[player_id]) == HumanPlayer:
				self.top_banner.config(text=PLAYERS[self.current_player] + "'s turn")
				for move in valid_moves:
					b = tk.Button(self, text="play", command=partial(self._place_disc, move), highlightthickness=0)
					b.place(x=move[0]*SQUARE_SIZE + HALF_SQUARE - 13, y=move[1]*SQUARE_SIZE + HALF_SQUARE + HALF_SQUARE - 10)
					self.buttons.append(b)

			# if it's an AI, disable buttons & start up its turn
			else:
				self.top_banner.config(text=PLAYERS[self.current_player] + " player is thinking...")

				self.after(50, self._do_computer_turn)

		# flip a token
		def _flip_token(self, location):
			if self.board[location[1]][location[0]] == 1: 
				image = self.disc2_image
				self.board[location[1]][location[0]] = 2
			else: 
				image = self.disc1_image
				self.board[location[1]][location[0]] = 1
			new_disc = self.canvas.create_image((location[0]*SQUARE_SIZE + HALF_SQUARE, location[1]*SQUARE_SIZE + HALF_SQUARE), image=image)

		# let the computer take a turn
		def _do_computer_turn(self):
			# pass the player a tuple (so it can't mess with the original board)
			board_tuple = tuple([tuple(column) for column in self.board])
			move = self.players[self.current_player].pick_move(board_tuple)

			# checks to make sure that the AI has made a valid move
			assert self._is_on_board(move)
			assert self.board[move[1]][move[0]] == 0
			
			self.top_banner.config(text=PLAYERS[self.current_player] + " player is thinking...")
			self._place_disc(move)
			
		# take in a color string or tuple, return a tuple
		@staticmethod
		def _make_color_tuple(color, alpha=255):
			if type(color) == str:
				full_int = int(color.lstrip("#"), 16)
				red = full_int // 65536
				green = (full_int // 256) % 256
				blue = full_int % 256
				return (red, green, blue, alpha)
			if type(color) == tuple or type(color) == list:
				if len(color) == 3: return (color[0], color[1], color[2], 255)
				elif len(color) == 4: return tuple(color)

		# given a color tuple, return a string in the form "#rrggbb"
		@staticmethod
		def _make_color_string(color_tuple):
			return "#" +hex(256*65536 + 65536 * color_tuple[0] + 256 * color_tuple[1] + color_tuple[2])[3:]

		# make an image for one square in the board
		@staticmethod
		def _make_board_image():
			# start by making something double-size, so we can shrink it and get anti-aliasing
			im = Image.new("RGBA", (2*SQUARE_SIZE,2*SQUARE_SIZE), App._make_color_tuple(BOARD_COLOR))
			draw = ImageDraw.Draw(im)
			draw.rectangle([(0, 0), (2*SQUARE_SIZE, 2*SQUARE_SIZE)], fill=None, outline=(0, 0, 0, 0))
			return ImageTk.PhotoImage(im.resize((SQUARE_SIZE, SQUARE_SIZE), resample=Image.BICUBIC))

		# make a disc out of the passed color
		@staticmethod
		def _make_disc_image(color):
			im = Image.new("RGBA", (2*SQUARE_SIZE,2*SQUARE_SIZE), (0,0,0,0))
			draw = ImageDraw.Draw(im)

			offset = None
			if color == (255, 255, 255, 255):
				offset = (0, 0, 0, 255)
			color = App._make_color_tuple(color)
			dark = (color[0]//2, color[1]//2, color[2]//2, color[3])
	
			draw.ellipse((0, 0, 2*SQUARE_SIZE, 2*SQUARE_SIZE), color, dark)
			return ImageTk.PhotoImage(im.resize((SQUARE_SIZE, SQUARE_SIZE), resample=Image.BICUBIC))

		# make an 64x64 image of a black disc and a white disc
		@staticmethod
		def _make_icon():
			im = Image.new("RGBA", (100,100), (0,0,0,0))
			draw = ImageDraw.Draw(im)
			draw.ellipse((0, 0, 70, 70), "black")
			draw.ellipse((30, 30, 100, 100), "black") # the outline for the white disc
			draw.ellipse((34, 34, 96, 96), "white")
			return ImageTk.PhotoImage(im.resize((64, 64), resample=Image.BICUBIC))
			
# error to print out if we couldn't load up graphics
except ImportError:
	print("Warning: Could not find the tkinter or PIL module. Graphics disabled.", file=sys.stderr)
	do_graphics = False

################################################################################
# FUNCTIONS
################################################################################

def load_player(player_id, module_name = None, level = 1):
	"""
	Load up a ComputerPlayer class from the given module. A module of None means 
	a human player.
	"""
	class_name = "Player" +str(player_id)+ "Class"

	# if module_name is None, that means we have a human player
	if module_name == None:
		exec(class_name + " = HumanPlayer", globals())
		return HumanPlayer()

	# look for the file specified, see if we have a proper ComputerPlayer
	try:
		exec("from " +module_name+ " import ComputerPlayer as " +class_name, globals())
	except ImportError:
		print("Could not find ComputerPlayer in file \"" +module_name+ ".py\". Exiting.", file=sys.stderr)
		sys.exit(1)

	# print("success!")

	# make a local pointer to the ComputerPlayer class, and return a new instance
	exec("Player = " +class_name)
	return locals()["Player"](player_id, level)

def parse_command_line_args(args):
	"""
	Search the command-line args for the various options (see the help function).
	"""
	
	# print help message
	if "-h" in args or "--help" in args: print_help = True
	else: print_help = False

	# AI file
	if "-f" in args: ai_file = args[args.index("-f") + 1].rstrip(".py")
	else: ai_file = DEFAULT_AI_FILE
	
	# number of players
	if "-0" in args: players = (ai_file, ai_file)
	elif "-2" in args: players = (None, None)
	else: players = (None, ai_file)

	# level of players
	if "-l" in args:
		levels = args[args.index("-l") + 1].split(',')
		if len(levels) == 1: levels = (int(levels[0]), int(levels[0]))
		else: levels = (int(levels[0]), int(levels[1]))
	else: levels = (DEFAULT_AI_LEVEL, DEFAULT_AI_LEVEL)

	# colors
	if "-c" in args:
		color_string = args[args.index("-c") + 1]
		colors = color_string.split(',')
	else: colors = None
		
	return (print_help, players, levels, colors)

def print_help(output = sys.stderr):
	"""
	Print out a help screen for the user (probably to stderr).
	"""
	
	print("Usage: python3 " +sys.argv[0]+ " <options>", file=output)
	print("Options include:", file=output)
	print("\t-0\t0-player (computer-v-computer)", file=output)
	print("\t-1\t1-player (human-v-computer)", file=output)
	print("\t-2\t2-player (human-v-human)", file=output)
	print("\t-c\tuse colors (RRGGBB,RRGGBB)", file=output)
	print("\t-f\tuse a non-standard AI file", file=output)
	print("\t-h\tprint this help", file=output)
	print("\t-l\tset AI level (#,#)", file=output)
	#print("\t-n\tnon-graphics mode", file=output)

def play_game_in_ascii(player1, player2):
	"""
	ASCII game. Boring. May not implement this.
	"""
	pass

################################################################################
# PARSE COMMAND LINE & START PLAYING
################################################################################

do_print_help, player_files, levels, colors = parse_command_line_args(sys.argv[1:])

# help message for user, if -h or --help
if do_print_help:
	print_help()
	sys.exit(1)

# load up the player classes
if random.random() > .5:
	players = (load_player(1, player_files[1], levels[1]), load_player(2, player_files[0], levels[0]))
else :
	players = (load_player(1, player_files[0], levels[0]), load_player(2, player_files[1], levels[1]))

# hit it!
if do_graphics:
	print("starting graphics...")
	app = App(players, colors)
	app.mainloop()

else:
#    play_game_in_ascii(players[1], players[2])
	print("Sorry--this game is not implemented yet in ASCII.", file=sys.stderr)