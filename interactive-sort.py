# Requires ImageMagick and Kitty terminal
# This program uses Python's curses library to show you one image at a time in your terminal, and prompts you to press a key to move the image to the directory assigned to that key. You can add and remove keys by navigating through the menu.

import curses
from curses import wrapper
from os.path import join
from subprocess import call
import glob
import os
 
WK_DIR = 'unset'
SORT_KEYS = {
    }
MENU = ['Start', 'Choose Directory', 'Add Sorting Key', 'Remove Sorting Key', 'Quit']
keyPass = ''
# all ImageMagick file formats supported, TODO: add rest of supported formats
imgFormats = ['png', 'jpg', 'jpeg', 'tif', 'tiff', 'gif', 'svg', 'tga']

def getImages(imgDir):
    imgs = []
    for i in imgFormats:
        imgs.extend(list(glob.glob(str(imgDir) + '/*.' + i)))
    return imgs

def scrollDirs(dirList):
    scrollList = []
    for i in range(1, (len(dirList)//10)+2):
        scrollList.append([])
    group = -1
    index = 0
    for item in dirList:
        if len(scrollList[group]) % 10 == 0:
            group += 1
        scrollList[group].append(item)
        index += 1
    return scrollList

# this function works for both choosing the dir for keys and for the working directory by the 'context' argument
def chooseDirMenu(window, getDir, selection, dirGroup, context):
    context = context
    selection = selection
    window.clear()
    window.addstr('- Choose Directory\n- Press backspace to return to main menu.\n\n')
    showWkDir(window)
    newDir = ''
    walk = os.walk(getDir)
    walkDirs = []
    walkRoot = []
    dirGroup = dirGroup
    for root, dirs, files in walk:
        walkDirs.append(dirs)
        walkRoot.append(root)
        break
    try:
        walkDirs = scrollDirs(walkDirs[0])
    except IndexError:
        window.addstr(str(walk))
        window.addstr(walkDirs)
    if selection <= -1:
        if dirGroup == 0:
            dirGroup = len(walkDirs) - 1
        else:
            dirGroup -= 1
        selection = len(walkDirs[dirGroup]) - 1
    if selection >= len(walkDirs[dirGroup]):
        selection = 0
        if len(walkDirs) - 1 == dirGroup:
            dirGroup == 0
        else:
            dirGroup += 1
    # test
    # window.addstr('\n\n***test***\n')
    # window.addstr('walkDirs length: ' + str(len(walkDirs)) + '\nwalkDirs[dirGroup] length: ' + str(len(walkDirs[dirGroup])) + '\ndirGroup: ' + str(dirGroup) + '\n')
    # window.addstr('selection: ' + str(selection))
    # window.addstr('\n***test***\n\n')
    # /test
    window.addstr(os.path.realpath(root) + '\n---------\n\n')
    # add more indicator if dirGroup > 0
    if dirGroup > 0:
        window.addstr(u"\u25B2..." + '\n')
    try:
        for dirs in walkDirs[dirGroup]:
            if walkDirs[dirGroup].index(dirs) == selection:
                window.addstr(dirs + '\n', curses.color_pair(1))
            else:
                window.addstr(dirs + '\n')
    except curses.error:
        pass
    if walkDirs == [[]]:
        window.addstr('..')
    # add more indicator if walkDirs length > 1
    if len(walkDirs) - 1 > dirGroup:
        window.addstr(u"...\u25BC")
    keyPressed = window.getch()
    if keyPressed == curses.KEY_BACKSPACE:
        mainMenu(window, True, 0)
    if keyPressed == curses.KEY_DOWN:
        chooseDirMenu(window, getDir, selection + 1, dirGroup, context)
    elif keyPressed == curses.KEY_UP:
        chooseDirMenu(window, getDir, selection - 1, dirGroup, context)
    elif keyPressed == curses.KEY_LEFT:
        # go up in the directory tree
        if os.path.realpath(root) == '/home':
            chooseDirMenu(window, getDir, selection, dirGroup, context)
        else:
            newDir = os.path.join(getDir, '..')
            dirGroup = 0
            chooseDirMenu(window, newDir, 0, dirGroup, context)
    elif keyPressed == curses.KEY_RIGHT:
        # add selected dir to walk tree if not empty
        if walkDirs == [[]]:
            chooseDirMenu(window, getDir, 0, dirGroup, context)
        else:
            newDir = os.path.join(getDir, walkDirs[dirGroup][selection])
            dirGroup = 0
        chooseDirMenu(window, newDir, selection, dirGroup, context)
    elif keyPressed == curses.KEY_ENTER or keyPressed == 10 or keyPressed == 13:
        if walkDirs == [[]]:
            newDir = os.path.join(getDir, '..')
            chooseDirMenu(window, newDir, 0, dirGroup, context)
        else:
            if context == 'key':
                global keyPass
                keyPass = os.path.abspath(getDir + '/' + walkDirs[dirGroup][selection])
            else:
                window.clear()
                global WK_DIR
                WK_DIR = os.path.abspath(getDir + '/' + 
                walkDirs[dirGroup][selection])
                mainMenu(window, True, 0)
    else:
        chooseDirMenu(window, getDir, selection, dirGroup, context)

# helper function to show the current sorting keys set by the user
def showKeys(window):
    if SORT_KEYS != {}:
        window.addstr('keys:\n', curses.color_pair(2))
        for i in SORT_KEYS:
            window.addstr(str(i, 'utf-8') + ': -> ' + str(SORT_KEYS[i]) + '\n', curses.color_pair(2))
        window.addstr('\n')
# helper function to show the current working directory
def showWkDir(window):
    if WK_DIR != 'unset':
        window.addstr('image directory:\n' + str(WK_DIR) + '\n\n', curses.color_pair(3))

def addKeyMenu(window):
    window.clear()
    window.addstr('Add a sorting key.\nThis is a directory that images go\nwhen you press the key you choose.\n\nPress any a-z or 1-9 character\nto add a key.\n\nPress backspace to return to main menu.\n\n')
    showKeys(window)
    key = window.getch()
    if key == curses.KEY_BACKSPACE:
        mainMenu(window, True, 0)
    key = curses.unctrl(key)
    if key.isalnum():
        if key not in SORT_KEYS:
            window.clear()
            window.addstr('Now choose the directory\nthis key moves images to.')
            window.getch()
            chooseDirMenu(window, '.', 0, 0, 'key')
            keyDir = keyPass
            SORT_KEYS.setdefault(key, keyDir)
            mainMenu(window, True, 0)
    else:
        window.clear()
        window.addstr('Please use a-z or 0-9')
        window.getch()
        window.clear()
        addKeyMenu(window)

def removeKeyMenu(window, selection):
    window.clear()
    window.addstr('Press backspace to go to main menu\n\n')
    global SORT_KEYS
    if SORT_KEYS == {}:
        window.addstr('No sorting keys added yet...\n')
        window.getch()
        mainMenu(window, True, 0)
    sortKeys = list(SORT_KEYS)
    if selection <= -1:
        selection = len(sortKeys) - 1
    if selection >= len(sortKeys):
        selection = 0
    try:
        for keys in sortKeys:
            if sortKeys.index(keys) == selection:
                window.addstr(str(keys) + ': -> ' + str(SORT_KEYS[keys]) + '\n', curses.color_pair(1))
            else:
                window.addstr(str(keys) + ': -> ' + str(SORT_KEYS[keys]) + '\n')
    except curses.error:
        pass
    keyPressed = window.getch()
    if keyPressed == curses.KEY_BACKSPACE:
        mainMenu(window, True, 0)
    if keyPressed == curses.KEY_DOWN:
        removeKeyMenu(window, selection +1)
    elif keyPressed == curses.KEY_UP:
        removeKeyMenu(window, selection -1)
    elif keyPressed == curses.KEY_ENTER or keyPressed == 10 or keyPressed == 13:
        del SORT_KEYS[sortKeys[selection]]
        window.clear()
        window.addstr('key removed')
        window.getch()
        removeKeyMenu(window, 0)
    else:
        removeKeyMenu(window, selection)

def mainMenu(window, firstRun, selection):
    if firstRun == True:
        call(["kitty", "+kitten", "icat", "--clear"])
    window.clear()
    if firstRun == True:
        selection = 0
    if selection == 5:
        selection = 0
    if selection == -1:
        selection = 4
    for i in MENU:
        if MENU.index(i) == selection:
            window.addstr(i + '\n', curses.color_pair(1))
        else:
            window.addstr(i + '\n')
    window.addstr('\n\n')
    showWkDir(window)
    showKeys(window)
    keyPressed = window.getch()
    if keyPressed == curses.KEY_DOWN:
        mainMenu(window, False, selection + 1)
    elif keyPressed == curses.KEY_UP:
        mainMenu(window, False, selection - 1)
    elif keyPressed == curses.KEY_ENTER or keyPressed == 10 or keyPressed == 13:
        window.clear()
        mainSelect(window, selection)
    else:
        mainMenu(window, False, selection)

# helper funciton for the main menu handles user choice
def mainSelect(window, selection):
    if selection == 0:
        if WK_DIR == 'unset':
            window.clear()
            window.addstr('Please select a directory first.')
            window.getch()
            mainMenu(window, True, 0)
        else:
            window.clear()
            displayImg(window)
    if selection == 1:
        if WK_DIR == 'unset':
            chooseDirMenu(window, '.', 0, 0, 'working')
        else:
            chooseDirMenu(window, WK_DIR, 0, 0, 'working')
    if selection == 2:
        addKeyMenu(window)
    if selection == 3:
        removeKeyMenu(window, 0)
    if selection == 4:
        endProg(window)

# this function handles the main logic of moving the files according to user feedback
def imgAction(window, keyPressed, img):
    window.clear()
    window.addstr('\n\n')
    showWkDir(window)
    showKeys(window)
    window.addstr('\'.\': skip\n')
    window.addstr('\'q\': quit to main menu\n')
    if keyPressed in SORT_KEYS:
        imgFrom = str(img)
        imgTo = str(SORT_KEYS[keyPressed])
        existingFilePaths = glob.glob(imgTo + '/*')
        existingFileNames = []
        for file in existingFilePaths:
            existingFileNames.append(os.path.basename(file))
        if os.path.basename(imgFrom) in existingFileNames:
            overWriteWarning(window, imgFrom, imgTo, 1, keyPressed, existingFileNames, True)
        else:
            call(["mv", imgFrom, imgTo])
            window.clear()
            window.addstr('moved to' + str(SORT_KEYS[keyPressed]) + '\n\n')
            showWkDir(window)
            showKeys(window)
    elif str(keyPressed, 'utf-8') == '.':
        window.addstr('')
    elif str(keyPressed, 'utf-8') == 'q':
        mainMenu(window, True, 0)
    else:
        try:
            keyPressed2 = curses.unctrl(window.getch())
            window.clear()
            imgAction(window, keyPressed2, img)
        except curses.error:
            pass

# handles the event of a file with the same name is sorted into a folder
def overWriteWarning(window, imgFrom, imgTo, fileNum, keyPressed, existingFileNames, firstRun):
    window.clear()
    window.addstr(str(os.path.basename(imgFrom)) + ' already exists in ' + imgTo + '.\nRename file: \'y\'\nSkip: \'.\'\n')
    if firstRun == True:
        choice = window.getkey()
    else:
        choice = 'y'
    if choice == 'y':
        extSplit = os.path.splitext(imgFrom)
        renamedFile = extSplit[0] + '(' + str(fileNum) + ')' + extSplit[1]
        # if the renamed file with (num) added already exists, add to num
        if os.path.basename(renamedFile) in existingFileNames:
            overWriteWarning(window, imgFrom, imgTo, fileNum + 1, keyPressed, existingFileNames, False)
        else:
            call(["mv", imgFrom, imgTo + '/' + str(os.path.basename(renamedFile))])
            window.clear()
            window.addstr('moved to' + str(SORT_KEYS[keyPressed]) + '\n\n')
            showWkDir(window)
            showKeys(window)
    elif choice == '.':
        window.addstr('')
    else:
        overWriteWarning(window, imgFrom, imgTo, fileNum, keyPressed, existingFileNames, firstRun)

def displayImg(window):
    window.addstr('\n\n')
    showWkDir(window)
    showKeys(window)
    imgs = getImages(WK_DIR)
    window.addstr('\'.\': skip\n')
    window.addstr('\'q\': quit to main menu\n')
    for img in imgs:
        call(["kitty", "+kitten", "icat", "--clear"])
        call(["kitty", "+kitten", "icat", "--place", "30x50@45x1", img])
        keyPressed = window.getch()
        while keyPressed == curses.KEY_RESIZE:
            keyPressed = window.getch()
        keyPressed = curses.unctrl(keyPressed)
        if keyPressed == 'q':
            break
        imgAction(window, keyPressed, img)
    call(["kitty", "+kitten", "icat", "--clear"])
    mainMenu(window, True, 0)

def endProg(window):
    curses.nocbreak()
    window.keypad(False)
    curses.echo()
    curses.endwin()
    exit(0)

def main(sc):
    sc = curses.newwin(40, 42, 2, 2)
    sc.keypad(True)
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    mainMenu(sc, True, 0)

wrapper(main)