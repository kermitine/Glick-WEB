"""
Copyright (C) 2025 Ayrik Nabirahni. This file
is apart of the Glick project, and licensed under
the GNU AGPL-3.0-or-later. See LICENSE and README for more details.
"""

import time
import decrypter
import encrypter
import files.ascii as ascii
from files.vars import *



def mode_select_user_input():
    return input(str('Enter e for encryption. Enter d for decryption. Enter any number to exit.' + '\n'))
def get_mode():
    while True:
        mode_selected = mode_select_user_input()
        print('\n')
        if mode_selected in ['e', 'E']:
            return 'enc'
        elif mode_selected in ['d', 'D']:
            return 'dec'
        elif mode_selected in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
            print('Program Terminating...')
            time.sleep(1.5)
            return 'terminate'
        else:
            print('Unrecognized mode. Are you sure you typed the right character? Please try again.' + '\n')
            


def glick_main():
    print('Glickcrypt V' + version_gli + ' initialized')
    print('___________________________________')
    print('\n')
    mode = get_mode()
    if mode == 'dec':
        decrypter.decrypt_main()
    elif mode == 'enc':
        encrypter.encrypt_main()
    else:
        pass

    


if __name__ == '__main__':
    ascii.ascii_run()
    glick_main()