import os
from jinja2 import Template
from time import strftime, localtime


def make_options(args):
    '''
    args: ArgumentParser.parse_args()
    mail_to: 收件人邮箱
    tf: 临时文件实例，用于存储生成的临时邮件内容
    '''
    options = []
    # 通过指定的 SMTP 账号发送邮件
    if args.au and args.ap and args.server:
        options.append(f'--server {args.server}')
        options.append(f'--au {args.au}')
        options.append(f'--ap {args.ap}')
    if args.mail_from:
        options.append(f'--from {args.mail_from}')
    if args.attach:
        # TODO 中文附件名存在乱码的问题！
        options.append(f'--attach @{args.attach}')
    for header in args.header:
        options.append(f'--header \'{header}: {args.header[header]}\'')
    return options


def make_text_options(args):
    options = make_options(args)
    options.append(f'--body \'{args.body}\'')
    return options


def make_tpl_options(args, mail_to, vars, tf):
    options = make_options(args)
    if not os.path.isfile(args.html):
        raise FileNotFoundError('HTML file not found.')
    with open(args.html, 'r') as html_file:
        html = html_file.read()
    template = Template(html)
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
    return options


def make_eml_option(args):
    options = make_options(args)
    if not os.path.isfile(args.eml):
        raise FileNotFoundError('EML file not found.')
    else:
        options.append(f'--data @{args.eml}')
    return options


def invoke_swaks(mail_to, options):
    options = ' '.join(options)
    cmd = f'swaks --to {mail_to} {options}'
    # return cmd + '\n'
    resp = os.popen(cmd).read()
    return resp
