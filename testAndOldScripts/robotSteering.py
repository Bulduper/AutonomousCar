from pynput import keyboard  # using module keyboard

def fun(abc):
    print('preesed')
def on_press(key):
    try:
        print('alphanumeric key {0} pressed'.format(key.char))
    except AttributeError:
        print('special key {0} pressed'.format(key))

    with keyboard.Listener(
        on_press=on_press) as listener:
        listener.join()

while True:
    pass        
# value = print('Enter the command to be sent to robot: \n')

# while True:  # making a loop
#     try:  # used try so that if user pressed other than the given key error will not be shown
#         if keyboard.is_pressed('q'):  # if key 'q' is pressed 
#             print('You Pressed A Key!')
#     except:
#         break  # if user pressed a key other than the given key the loop will break
    




