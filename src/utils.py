from colorama import Fore


def echo_error(msg, exit_now=False):
    print(Fore.RED + '[x]  ' + msg + Fore.RESET)
    if exit_now:
        exit()


def echo_ok(msg):
    print(Fore.GREEN + '[*]  ' + msg + Fore.RESET)


def parse_result(resp):
    '''
    resp: Swaks 在终端界面输出的内容
    '''
    try:
        resp = resp.split('\n')
        '<-  250'
        if resp[-5][:7] == '<-  250':
            return True
        else:
            return resp[-5]
    except:
        return resp
        