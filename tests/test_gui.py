import PySimpleGUI as sg

layout = [[sg.Image('C:\\Users\\asaph\\PycharmProjects\\chessboard\\images\\light_empty.png'), sg.Image('C:\\Users\\asaph\\PycharmProjects\\chessboard\\images\\dark_empty.png')]]

window = sg.Window('Title', layout, element_padding=(0, 0))

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break

window.close()
