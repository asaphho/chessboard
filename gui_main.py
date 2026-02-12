from os import path
from classes.move import LegalMove
import tkinter as tk
from tkinter import messagebox, simpledialog
import sys
from classes.position import Position
from utils.board_functions import square_color_int
from simple_bot.bot1.evaluation import quick_evaluate
from classes.bot import Bot
from version import software_version
from classes.game import Game
from typing import List, Dict
from PIL import Image, ImageTk
import platform

UNHANDLED_ERROR_MESSAGE = 'Something went wrong. :( Immediately after closing this popup, please submit an issue on https://github.com/asaphho/chessboard with the moves of the game up to this point, and describe what you attempted to do.'

TITLE = f'chessboard v{software_version}'
FEN_SYMBOL_TO_PIECE = {'P': 'wpawn', 'K': 'wking', 'Q': 'wqueen', 'B': 'wbishop', 'N': 'wknight', 'R': 'wrook',
                       'p': 'bpawn', 'k': 'bking', 'q': 'bqueen', 'b': 'bbishop', 'n': 'bknight', 'r': 'brook',
                       '1': 'empty'}

intro_text = ('Enter moves in standard algebraic notation, or click on a piece and then a destination square to move it.\n'
              'If using notation, always use uppercase for non-pawn pieces. \n'
              'For castling notation, use the letter O (both upper and lower case accepted) and not the number 0.\n'
              'Give all files in lowercase. Do not include any spaces.\n ')

ALL_SQUARE_KEYS = []
for i in '01234567':
    for j in '01234567':
        ALL_SQUARE_KEYS.append(i+j)


class MainMenuWindow:
    """Main menu window for selecting game mode"""
    
    def __init__(self):
        self.result = None
        self.window = tk.Tk()
        self.window.title(TITLE)
        self.window.geometry("300x150")
        set_window_icon(self.window)
        
        tk.Label(self.window, text="Select an option to continue.").pack(pady=10)
        
        tk.Button(self.window, text="Human VS Human", 
                 command=self.human_vs_human, width=20).pack(pady=5)
        tk.Button(self.window, text="Play against bot", 
                 command=self.play_bot, width=20).pack(pady=5)
        tk.Button(self.window, text="Quit to desktop", 
                 command=self.quit, width=20).pack(pady=5)
        
        self.window.protocol("WM_DELETE_WINDOW", self.quit)
    
    def human_vs_human(self):
        self.result = {'exit': False, 'bot': False, 'bot_color': 'b', 'opening_book': None}
        self.window.destroy()
    
    def play_bot(self):
        self.window.destroy()
        bot_window = BotMenuWindow()
        bot_window.window.mainloop()
        if bot_window.result is None:
            # User cancelled, show main menu again
            self.__init__()
            self.window.mainloop()
        else:
            self.result = bot_window.result
    
    def quit(self):
        self.result = {'exit': True, 'bot': False, 'bot_color': 'b', 'opening_book': None}
        self.window.destroy()


class BotMenuWindow:
    """Bot configuration menu"""
    
    def __init__(self):
        self.result = None
        self.window = tk.Tk()
        self.window.title(TITLE)
        self.window.geometry("300x150")
        set_window_icon(self.window)
        
        # Color selection
        tk.Label(self.window, text="Play as:").pack(pady=10)
        
        self.color_var = tk.StringVar(value='w')
        color_frame = tk.Frame(self.window)
        color_frame.pack()
        tk.Radiobutton(color_frame, text="White", variable=self.color_var, 
                      value='w').pack(side=tk.LEFT)
        tk.Radiobutton(color_frame, text="Black", variable=self.color_var, 
                      value='b').pack(side=tk.LEFT)
        
        # Opening book checkbox
        self.opening_book_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.window, text="Let bot use opening book", 
                      variable=self.opening_book_var).pack(pady=10)
        
        # Buttons
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="OK", command=self.ok, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.cancel, width=10).pack(side=tk.LEFT, padx=5)
        
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)
    
    def ok(self):
        bot_color = 'b' if self.color_var.get() == 'w' else 'w'
        opening_book_path = get_opening_book_path() if self.opening_book_var.get() else None
        self.result = {'exit': False, 'bot': True, 'bot_color': bot_color, 'opening_book': opening_book_path}
        self.window.destroy()
    
    def cancel(self):
        self.result = None
        self.window.destroy()


class ChessGUI:
    """Main chess GUI window"""
    
    def __init__(self, game: Game, bot_config: Dict):
        self.game = game
        self.bot_config = bot_config
        self.playing_against_bot = bot_config['bot']
        self.bot_color = bot_config['bot_color']
        
        if self.playing_against_bot:
            self.bot = Bot(quick_evaluate, breadth=3, aggression=1, fluctuation=0.15, 
                          assumed_opp_aggression=1, opening_book_path=bot_config['opening_book'])
        else:
            self.bot = None
        
        # State variables
        self.selected_square = None
        self.square_buttons = {}  # Maps square names to button widgets
        self.photo_images = {}  # Keep references to prevent garbage collection
        self.game_ended = False  # Track if game has ended
        self.game_ended_by_bot = False  # Track if bot made the game-ending move
        
        # Create main window
        self.window = tk.Tk()
        self.window.title(TITLE)
        set_window_icon(self.window)
        
        # Create UI elements
        self.create_widgets()
        
        # If bot plays white, make first move
        if self.playing_against_bot and self.bot_color == 'w':
            self.window.after(100, self.play_computer_move)
    
    def create_widgets(self):
        """Create all UI widgets"""
        
        # Top frame for intro text
        top_frame = tk.Frame(self.window)
        top_frame.pack(pady=10)
        tk.Label(top_frame, text=intro_text, justify=tk.LEFT).pack()
        
        # Side to move label
        self.to_move_label = tk.Label(self.window, text=self.get_side_to_move_text())
        self.to_move_label.pack()
        
        # Chessboard frame
        board_frame = tk.Frame(self.window, bg='gray')
        board_frame.pack(pady=10)
        
        # Create 8x8 grid of buttons
        self.create_board(board_frame)
        
        # Output text label
        self.output_label = tk.Label(self.window, text="", fg='blue')
        self.output_label.pack(pady=5)
        
        # Game end text label (initially hidden)
        self.game_end_label = tk.Label(self.window, text="", fg='red', font=('Arial', 12, 'bold'))
        self.game_end_label.pack(pady=5)
        
        # Input frame
        self.input_frame = tk.Frame(self.window)
        self.input_frame.pack(pady=10)
        
        self.input_prompt = tk.Label(self.input_frame, text=self.create_input_move_prompt())
        self.input_prompt.pack(side=tk.LEFT)
        
        self.input_entry = tk.Entry(self.input_frame, width=15)
        self.input_entry.pack(side=tk.LEFT, padx=5)
        self.input_entry.bind('<Return>', lambda e: self.enter_move())
        
        self.enter_button = tk.Button(self.input_frame, text="Enter move", command=self.enter_move)
        self.enter_button.pack(side=tk.LEFT)
        
        # Button frame
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Flip board", command=self.flip_board).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Show moves", command=self.show_moves).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Show FEN", command=self.show_fen).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Restart game", command=self.restart_game).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Take back last move", command=self.take_back_move).pack(side=tk.LEFT, padx=5)
    
    def create_board(self, parent):
        """Create the chessboard grid"""
        position = self.game.current_position
        ranks = '87654321' if not position.is_flipped() else '12345678'
        files = 'abcdefgh' if not position.is_flipped() else 'hgfedcba'
        
        for i in range(8):
            for j in range(8):
                square = f'{files[j]}{ranks[i]}'
                key = f'{i}{j}'
                
                # Create button with image
                btn = tk.Button(parent, borderwidth=0, highlightthickness=0,
                               command=lambda s=square, k=key: self.square_clicked(s, k))
                btn.grid(row=i, column=j, padx=0, pady=0)
                
                self.square_buttons[square] = btn
                self.update_square_image(square)
    
    def update_square_image(self, square: str, highlight: bool = False):
        """Update the image for a specific square"""
        image_path = get_image_path_from_square(self.game.current_position, square, highlight)
        
        try:
            # Load image using PIL
            img = Image.open(image_path)
            # Resize if needed (adjust size as needed)
            img = img.resize((80, 80), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            # Keep reference to prevent garbage collection
            self.photo_images[square] = photo
            
            # Update button
            self.square_buttons[square].config(image=photo)
        except Exception as e:
            print(f"Error loading image for {square}: {e}")
            self.square_buttons[square].config(text=square)
    
    def update_all_squares(self):
        """Update all square images"""
        for square in self.square_buttons.keys():
            self.update_square_image(square)
    
    def square_clicked(self, square: str, key: str):
        """Handle square click"""
        if self.game.check_game_end_conditions() != 'N':
            return  # Game is over
        
        to_move = self.game.current_position.to_move()
        
        # If no square selected, try to select this one
        if self.selected_square is None:
            if square in self.game.current_position.get_pieces_by_color(to_move).get_occupied_squares():
                self.selected_square = square
                self.update_square_image(square, highlight=True)
        else:
            # A square is already selected
            if square == self.selected_square:
                # Clicked same square, deselect
                self.update_square_image(square, highlight=False)
                self.selected_square = None
            else:
                # Try to make a move
                self.try_make_move(self.selected_square, square)
    
    def try_make_move(self, origin: str, destination: str):
        """Attempt to make a move from origin to destination"""
        to_move = self.game.current_position.to_move()
        all_legal_moves = self.game.current_position.get_all_legal_moves_for_color(to_move)
        possible_legal_moves = [move for move in all_legal_moves 
                               if move.origin_square == origin and move.destination_square == destination]
        
        if len(possible_legal_moves) == 0:
            self.output_label.config(text='Illegal move.')
            self.update_square_image(origin, highlight=False)
            self.selected_square = None
            return
        
        # Handle pawn promotion
        first_possible_move = possible_legal_moves[0]
        if first_possible_move.pawn_promotion_required():
            move = self.handle_pawn_promotion(possible_legal_moves, origin)
            if move is None:
                return
        else:
            move = first_possible_move
        
        # Make the move
        res = self.game.process_move(move)
        self.selected_square = None
        
        # Update display
        game_end_check = self.game.check_game_end_conditions()
        if game_end_check == 'N':
            self.update_after_move(res)
            # If playing against bot, make bot move
            if self.playing_against_bot:
                self.window.after(500, self.play_computer_move)
        else:
            self.handle_game_end(res, game_end_check)
    
    def handle_pawn_promotion(self, possible_moves: List[LegalMove], origin: str):
        """Handle pawn promotion selection"""
        result = simpledialog.askstring("Select promotion piece", 
                                       "Enter Q, R, N, or B for promotion piece:",
                                       initialvalue='Q')
        
        if result is None:
            self.update_square_image(origin, highlight=False)
            self.selected_square = None
            return None
        
        result = result[0].upper()
        matching_moves = [m for m in possible_moves if m.promotion_piece == result]
        
        if len(matching_moves) == 0:
            messagebox.showerror("Error", "Invalid promotion piece symbol")
            self.update_square_image(origin, highlight=False)
            self.selected_square = None
            return None
        
        return matching_moves[0]
    
    def enter_move(self):
        """Handle move entry via notation"""
        if self.selected_square is not None:
            self.output_label.config(text='Moving by notation is disabled when a piece has been selected.')
            return
        
        if self.game.check_game_end_conditions() != 'N':
            return  # Game is over
        
        input_notation = self.input_entry.get().strip()
        if input_notation == '':
            return
        
        try:
            res, move = self.game.process_input_notation(input_notation, return_move_for_gui=True)
        except Exception as e:
            self.output_label.config(text=str(e))
            return
        
        game_end_check = self.game.check_game_end_conditions()
        if game_end_check == 'N':
            self.update_after_move(res)
            # If playing against bot, make bot move
            if self.playing_against_bot:
                self.window.after(500, self.play_computer_move)
        else:
            self.handle_game_end(res, game_end_check)
    
    def update_after_move(self, message: str):
        """Update UI after a move is made (game continues)"""
        self.update_all_squares()
        self.output_label.config(text=message)
        self.input_entry.delete(0, tk.END)
        self.input_prompt.config(text=self.create_input_move_prompt())
        self.to_move_label.config(text=self.get_side_to_move_text())
    
    def handle_game_end(self, last_move_msg: str, game_end_text: str, ended_by_bot: bool = False):
        """Handle game end state"""
        self.game_ended = True
        self.game_ended_by_bot = ended_by_bot
        
        self.update_all_squares()
        self.output_label.config(text=last_move_msg)
        self.to_move_label.config(text='Game is over.')
        self.game_end_label.config(text=game_end_text)
        
        # Hide input widgets
        self.input_prompt.pack_forget()
        self.input_entry.pack_forget()
        self.enter_button.pack_forget()
    
    def play_computer_move(self):
        """Make the bot play a move"""
        self.output_label.config(text='Bot is thinking.')
        self.window.update()
        
        res, move = self.game.play_computer_move(self.bot, True)
        game_end_check = self.game.check_game_end_conditions()
        
        if game_end_check == 'N':
            self.update_after_move(res)
        else:
            self.handle_game_end(res, game_end_check, ended_by_bot=True)
    
    def flip_board(self):
        """Flip the board orientation"""
        self.game.current_position.flip_position()
        
        # Find and destroy old board frame FIRST
        old_board_frame = None
        for widget in self.window.winfo_children():
            if isinstance(widget, tk.Frame) and widget.cget('bg') == 'gray':
                old_board_frame = widget
                break
        
        # Clear the board buttons
        for btn in self.square_buttons.values():
            btn.destroy()
        self.square_buttons.clear()
        self.photo_images.clear()
        
        # Destroy the old frame
        if old_board_frame:
            old_board_frame.destroy()
        
        # Create new board frame
        board_frame = tk.Frame(self.window, bg='gray')
        board_frame.pack(before=self.output_label, pady=10)
        self.create_board(board_frame)
        
        self.selected_square = None
    
    def show_moves(self):
        """Show move history in a popup"""
        moves = self.game.show_moves(return_string_for_window=True)
        
        popup = tk.Toplevel(self.window)
        popup.title("Moves")
        popup.geometry("400x500")
        
        text_widget = tk.Text(popup, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert('1.0', moves)
        text_widget.config(state=tk.DISABLED)
        
        scrollbar = tk.Scrollbar(popup, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
    
    def show_fen(self):
        """Show current position FEN"""
        fen = self.game.current_position.generate_fen()
        self.output_label.config(text=fen)
    
    def restart_game(self):
        """Restart the game"""
        if messagebox.askyesno("Restart", "Are you sure you want to restart?"):
            # Remember if board was flipped before restart
            was_flipped = self.game.current_position.is_flipped()
            
            self.game.restart_game()
            self.selected_square = None
            self.game_ended = False
            self.game_ended_by_bot = False
            
            # Restore the flip state if it was flipped before
            if was_flipped and not self.game.current_position.is_flipped():
                self.game.current_position.flip_position()
            
            # Show input widgets if hidden
            if not self.input_prompt.winfo_ismapped():
                self.input_prompt.pack(side=tk.LEFT)
                self.input_entry.pack(side=tk.LEFT, padx=5)
                self.enter_button.pack(side=tk.LEFT)
            
            self.game_end_label.config(text='')
            
            # Update display (just update images, board layout unchanged)
            self.update_all_squares()
            
            # Update display
            if self.playing_against_bot and self.bot_color == 'w':
                self.output_label.config(text='Game restarted.')
                self.window.after(500, self.play_computer_move)
            else:
                self.output_label.config(text='Game restarted.')
            
            self.input_entry.delete(0, tk.END)
            self.input_prompt.config(text=self.create_input_move_prompt())
            self.to_move_label.config(text=self.get_side_to_move_text())
    
    def take_back_move(self):
        """Take back the last move"""
        # Special case: playing against bot as white at move 1
        if self.playing_against_bot and self.bot_color == 'w' and self.game.current_position.move_number == 1:
            self.output_label.config(text='Nothing to take back.')
            return
        
        # If game has ended, use special logic
        if self.game_ended:
            # Always take back 1 move
            text = self.game.take_back_last_move(silent=True)
            # If bot ended the game, take back a second move
            if self.playing_against_bot and self.game_ended_by_bot:
                text = self.game.take_back_last_move(silent=True)
            self.update_after_takeback(text)
        # Normal case: game is still ongoing
        elif not self.playing_against_bot:
            text = self.game.take_back_last_move(silent=True)
            self.update_after_takeback(text)
        else:
            # Playing against bot, take back two moves
            self.game.take_back_last_move(silent=True)
            text = self.game.take_back_last_move(silent=True)
            self.update_after_takeback(text)
    
    def update_after_takeback(self, text: str):
        """Update UI after taking back a move"""
        self.selected_square = None
        self.game_ended = False
        self.game_ended_by_bot = False
        
        # Show input widgets if hidden
        if not self.input_prompt.winfo_ismapped():
            self.input_prompt.pack(side=tk.LEFT)
            self.input_entry.pack(side=tk.LEFT, padx=5)
            self.enter_button.pack(side=tk.LEFT)
        
        self.game_end_label.config(text='')
        self.update_all_squares()
        self.output_label.config(text=text)
        self.input_entry.delete(0, tk.END)
        self.input_prompt.config(text=self.create_input_move_prompt())
        self.to_move_label.config(text=self.get_side_to_move_text())
    
    def get_side_to_move_text(self) -> str:
        """Get text showing whose turn it is"""
        side_to_move = self.game.current_position.to_move()
        side_to_move = 'White' if side_to_move == 'w' else 'Black'
        return f'{side_to_move} to move.'
    
    def create_input_move_prompt(self) -> str:
        """Create the move number prompt"""
        to_move = self.game.current_position.to_move()
        move_number = self.game.current_position.get_move_number()
        prompt = f'{move_number}'
        if to_move == 'w':
            prompt += '. '
        else:
            prompt += '... '
        return prompt
    
    def run(self):
        """Start the GUI main loop"""
        self.window.mainloop()


def get_square_color(curr_square: str) -> str:
    square_color_bit = square_color_int(curr_square)
    square_color = 'light' if square_color_bit == 0 else 'dark'
    return square_color


def get_path_to_image(filename: str) -> str:
    try:
        filepath = path.join(sys._MEIPASS, 'images', filename)
    except Exception:
        filepath = path.join('.', 'images', filename)
    return filepath


def get_opening_book_path() -> str:
    try:
        filepath = path.join(sys._MEIPASS, 'opening_book', 'fen_uci.json')
    except Exception:
        filepath = path.join('.', 'simple_bot', 'opening_book', 'fen_uci.json')
    return filepath


def get_image_path_from_square(position: Position, square: str, highlight: bool = False) -> str:
    square_color = get_square_color(square)
    square_occupant = position.look_at_square(square)
    piece = FEN_SYMBOL_TO_PIECE[square_occupant]
    hl_suffix = '_hl' if highlight else ''
    filename = f'{square_color}_{piece}{hl_suffix}.png'
    return get_path_to_image(filename)


def set_window_icon(window: tk.Tk) -> None:
    try:
        system = platform.system()
        if system == 'Windows':
            icon_path = get_path_to_image('icon.ico')
            window.iconbitmap(icon_path)
        elif system == 'Darwin':
            try:
                icon_path = get_path_to_image('icon.icns')
                window.iconbitmap(icon_path)
            except:
                icon_path = get_path_to_image('icon.png')
                icon_image = tk.PhotoImage(file=icon_path)
                window.iconphoto(False, icon_image)
        else:
            icon_path = get_path_to_image('icon.png')
            icon_image = tk.PhotoImage(file=icon_path)
            window.iconphoto(False, icon_image)
    except:
        pass


def main():
    # Show main menu
    menu = MainMenuWindow()
    menu.window.mainloop()
    
    if menu.result['exit']:
        sys.exit()
    
    # Start game
    new_game = Game()
    
    # Handle bot first move if needed
    if menu.result['bot'] and menu.result['bot_color'] == 'w':
        new_game.current_position.flip_position()
    
    # Create and run chess GUI
    gui = ChessGUI(new_game, menu.result)
    gui.run()


if __name__ == '__main__':
    main()
