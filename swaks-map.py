import argparse
import os
import tempfile
from colorama import Fore
from time import sleep, strftime, localtime
from jinja2 import Template
from validate_email import validate_email


def parse_vars(vars):
    if not vars:
        return {}
    ret = {}
    for var in vars:
        k, v = var.split('=')
        ret[k] = v
    return ret


def make_inst(args, mail_to, tf):
    '''
    args: ArgumentParser.parse_args()
    mail_to: 收件人邮箱
    tf: 临时文件实例，用于存储生成的临时邮件内容
    '''
    options = []
    # 制定了 EML 时，发送 EML
    if args.eml:
        if not os.path.isfile(args.eml):
            raise FileNotFoundError('EML file not found.')
        else:
            options.append(f'--data {args.eml}')
    # 指定了 HTML 时，渲染 HTML 模板进行发送
    if args.html:
        if not os.path.isfile(args.html):
            raise FileNotFoundError('HTML file not found.')
        with open(args.html, 'r') as html_file:
            html = html_file.read()
        template = Template(html)
        vars = parse_vars(args.vars)
        # -> 注入内置变量
        now_time = localtime()
        to_user, to_domain = mail_to.split('@')
        vars['to_user'] = to_user
        vars['to_domain'] = to_domain
        vars['mail_to'] = mail_to
        vars['date'] = strftime('%Y-%m-%d', now_time)
        vars['time'] = strftime('%H:%M:%S', now_time)
        vars['datetime'] = strftime('%Y-%m-%d %H:%M:%S', now_time)
        # <- 注入结束
        content = template.render(vars)
        tf.write(content.encode('utf-8'))
        tf.flush()
        options.append('--attach-type text/html')
        options.append(f'--attach-body @{tf.name}')
        options.append(f'--header \'Subject: {args.subject}\'')
    # 发送普通文本
    else:
        options.append(f'--body \'{args.body}\'')
        options.append(f'--header \'Subject: {args.subject}\'')
    # 通过指定的 SMTP 账号发送邮件
    if args.au and args.ap and args.server:
        options.append(f'--server {args.server}')
        options.append(f'--au {args.au}')
        options.append(f'--ap {args.ap}')
    if args.mail_from:
        options.append(f'--from {args.mail_from}')
    # 加上 UA
    options.append('--header-X-Mailer \'Swaks Map v0.1 github.com/wowtalon/swaks-map/\'')
    return ' '.join(options)


def parse_result(resp):
    '''
    resp: Swaks 在终端界面输出的内容
    '''
    resp = resp.split('\n')
    '<-  250'
    if resp[-5][:7] == '<-  250':
        return True
    else:
        return resp[-5]


def send_mail(mail_to):
    '''
    调用 Swaks 发送邮件

    mail_to: 收件人邮箱
    '''
    tf = tempfile.NamedTemporaryFile()
    # 构造发送邮件的参数
    inst = make_inst(args, mail_to, tf)
    cmd = f'swaks --to {mail_to} {inst}'
    # print(cmd)
    # os.system(cmd)
    resp = os.popen(cmd).read()
    tf.close()
    ret = parse_result(resp)
    if ret is True:
        print(Fore.GREEN + f'[*] 发送到 {mail_to} 成功' + Fore.RESET)
    else:
        print(Fore.RED + f'[x] 发送到 {mail_to} 失败\n[x] {ret}' + Fore.RESET)
    return resp


def run(args):
    '''
    入口函数
    '''
    with open(args.output, 'a+') as output_file:
        # 逐个账号发送邮件
        for email in args.to:
            if args.delay > 0:
                sleep(args.delay)
            if validate_email(email):
                resp = send_mail(email)
                output_file.write(resp)
                continue
            if os.path.isfile(email):
                with open(email, 'r') as email_file:
                    for mail_to in email_file:
                        if args.delay > 0:
                            sleep(args.delay)
                        mail_to = mail_to.replace('\n', '')
                        resp = send_mail(mail_to)
                        output_file.write(resp)
                continue
            else:
                raise ValueError('Email invalid.')


if __name__ == '__main__':
    banner = '''
   _____               __              __  ___          
  / ___/      ______ _/ /_______      /  |/  /___ _____ 
  \__ \ | /| / / __ `/ //_/ ___/_____/ /|_/ / __ `/ __ \\
 ___/ / |/ |/ / /_/ / ,< (__  )_____/ /  / / /_/ / /_/ /
/____/|__/|__/\__,_/_/|_/____/     /_/  /_/\__,_/ .___/ 
                                               /_/ 
V0.1 By wowtalon(https://github.com/wowtalon/swaks-map)
'''
    print(banner)
    parser = argparse.ArgumentParser()
    mail_group = parser.add_argument_group('邮件配置')
    mail_group.add_argument('--mail-from', help='指定发件人的邮箱账号')
    mail_group.add_argument('--to', help='指定邮件接收人的邮箱账号或包含多个邮箱账号的文件', action='append', required=True)
    mail_group.add_argument('--header', help='指定邮件header', action='append')
    mail_group.add_argument('--body', help='指定想要发送邮件内容', default='Hello, World!')
    mail_group.add_argument('--subject', help='指定想要发送邮件标题', default='Test Mail From Swaks-Map')
    eml_group = parser.add_argument_group('EML模板')
    eml_group.add_argument('--eml', help='指定想要发送的EML文件')
    eml_group.add_argument('--html', help='指定想要发送的HTML模板')
    eml_group.add_argument('--vars', help='指定HTML模板中的变量，格式为key=val，如--vars \'name=张三\'', action='append')
    smtp_group = parser.add_argument_group('SMTP配置')
    smtp_group.add_argument('--server', help='指定SMTP服务器')
    smtp_group.add_argument('--au', help='指定SMTP账号')
    smtp_group.add_argument('--ap', help='指定SMTP密码')
    output_group = parser.add_argument_group('输出配置')
    output_group.add_argument('--output', help='指定输出结果文件名', default='result.txt')
    misc_group = parser.add_argument_group('其他配置')
    misc_group.add_argument('--delay', help='指定发送时间间隔，单位：秒，默认值为1', type=int, default=1)
    args = parser.parse_args()
    run(args)
