# Chessboard

A Python chess program I made myself as a coding exercise. Starts a new game of chess when run. Can move by clicking on a piece and then the destination square (for the GUI), or give the move in standard
algebraic notation, for both the black and white sides (no bot to play against). Does not allow illegal moves. Can be run 
on a CLI or on a GUI. Enforces the following game-ending conditions:

- Checkmate: The side to move has no legal moves and is under check. The other side wins.
- Stalemate: The side to move has no legal moves and is not under check. Game ends in a draw.
- Draw by repetition: The same position has arisen three times in the game with the same side to move and the same moves
available to each side.
- 50-move draw: 50 consecutive moves made by each side without a pawn move or capture. If the move that triggers this 
condition also delivers checkmate, the checkmate takes precedence. Otherwise, game ends in a draw.
- Draw by reduction: Either both sides have only a king left, or one side has only a king left and the 
other side has only a king and a minor piece (knight or bishop) left. 

Additional features:
- Flip board: Flips the orientation of the board on the GUI.
- Show moves: Shows the moves played in the current game in standard algebraic notation.
- Show FEN: Displays the [FEN](https://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation) of the current position.
- Restart game: Starts a new game. All data for the current game is lost.
- Take back last move: Reverses the most recently-played move. Can be repeated until the starting position is reached again. Data on moves that have been taken back are lost.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Executable Release](#executable-release)
- [Dependencies](#dependencies)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Installation

To clone this repository and install its dependencies (the dependencies are needed only for the GUI):

```bash
git clone https://github.com/asaphho/chessboard.git
cd chessboard
pip install -r requirements.txt
```

If you wish to compile the gui_main.py script into an executable on your own system, you need to install the dependencies. 
Additionally, you need a [license to use PySimpleGUI](https://docs.pysimplegui.com/en/latest/documentation/installing_licensing/license_keys/).
You will also need to install [pyinstaller](https://pypi.org/project/pyinstaller/).

Once these are settled, navigate to the project folder:
```bash
cd /.../chessboard
```

For Windows, run the following command:
```bash
pyinstaller --onefile --windowed --add-data ".\images:images" --icon .\images\icon.ico gui_main.py
```
If the compilation is successful, the file gui_main.exe should appear in the dist folder in the project folder.

For macOS, the command is
```bash
pyinstaller --onefile --windowed --add-data "./images:images" --icon ./images/icon.icns gui_main.py
```

If the compilation is successful, the executable gui_main.app should appear in the dist folder in the project folder.

## Usage

As mentioned, chessboard can be run on a CLI or on a GUI. To run it on the CLI, you simply need to run the main.py script
using Python 3.8 and above, without the need for any installation of the project dependencies.

```bash
python main.py
```

If you wish to run gui_main.py, you need to install the dependencies and possess a PySimpleGUI license (see [Installation](#installation)).

## Executable Release

This project is also available as a standalone executable. You can download the latest release from the [Releases page](https://github.com/asaphho/chessboard/releases).
You will not need to install pyinstaller, PySimpleGUI, or get a PySimpleGUI license to use the executable.

To use the executable:
1. Download the appropriate file for your operating system.
2. Run the executable file.

## Dependencies

This project uses the following main dependencies:
- PySimpleGUI (Hobbyist License)
- Pyinstaller as a development dependency

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- This project uses [PySimpleGUI](https://github.com/PySimpleGUI/PySimpleGUI) under a Hobbyist License.
Image assets are sourced from Wikimedia Commons. Specific attributions:
  - By Cburnett - Own work, Public Domain, https://commons.wikimedia.org/w/index.php?curid=1496742
  - By Cburnett - Own work, Public Domain, https://commons.wikimedia.org/w/index.php?curid=1496741
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496738
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496737
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496734
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496732
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496714
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496713
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496712
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496711
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496603
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496602
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496601
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496600
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496684
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496683
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496682
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496681
  - By Cburnett, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496656
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496655
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496654
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496652
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496597
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496596
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496595
  - By Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1496594
  - By Rfc1394 - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250445
  - By en:User:Rfc1394 - This W3C-unspecified vector image was created with Inkscape ., CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250444
  - By Rfc1394 - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250153
  - By en:User:Rfc1394 - This W3C-unspecified vector image was created with Inkscape ., CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250152
  - By en:User:Rfc1394 - This W3C-unspecified vector image was created with Inkscape ., CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250450
  - en:User:Rfc1394, CC BY-SA 3.0 <https://creativecommons.org/licenses/by-sa/3.0>, via Wikimedia Commons
  - By en:User:Rfc1394 - This W3C-unspecified vector image was created with Inkscape ., CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250158
  - By en:User:Rfc1394 - This W3C-unspecified vector image was created with Inkscape ., CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250157
  - By en:User:Rfc1394 - This W3C-unspecified vector image was created with Inkscape ., CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250453
  - By en:User:Rfc1394 - This W3C-unspecified vector image was created with Inkscape ., CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250452
  - By en:User:Rfc1394 - This W3C-unspecified vector image was created with Inkscape ., CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25249732
  - By en:User:Rfc1394 - This W3C-unspecified vector image was created with Inkscape ., CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250159
  - By Rfc1394 - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250441
  - By en:User:Rfc1394 - This W3C-unspecified vector image was created with Inkscape ., CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250442
  - By Rfc1394 - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250150
  - By Rfc1394 - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250151
  - By en:User:Rfc1394 - This W3C-unspecified vector image was created with Inkscape ., CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250448
  - By en:User:Rfc1394 - This W3C-unspecified vector image was created with Inkscape ., CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250447
  - By en:User:Rfc1394 - This W3C-unspecified vector image was created with Inkscape ., CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250154
  - By en:User:Rfc1394 - This W3C-unspecified vector image was created with Inkscape ., CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250276
  - By en:User:Rfc1394 - This W3C-unspecified vector image was created with Inkscape ., CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250449
  - By en:User:Rfc1394 - This W3C-unspecified vector image was created with Inkscape ., CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250446
  - By en:User:Rfc1394 - This W3C-unspecified vector image was created with Inkscape ., CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250156
  - By en:User:Rfc1394 - This W3C-unspecified vector image was created with Inkscape ., CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=25250155


---

