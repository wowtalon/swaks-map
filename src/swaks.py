import datetime
import json
import os
from copy import deepcopy
import tempfile
from jinja2 import Template
from time import strftime, localtime
from eml_parser import EmlParser
from base64 import b64decode


def parse_vars(vars: list):
    '''
    将命令行传入的变量列表解析为字典，方便后面使用 Jinja2 渲染
    vars: 格式为['varname=varvalue', ...]
    '''
    if not vars:
        return {}
    ret = {}
    for var in vars:
        k, v = var.split('=')
        ret[k] = v
    return ret


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


def make_text_options(mail_to, args):
    options = make_options(args)
    options.append(f'--body \'{args.body}\'')
    return invoke_swaks(mail_to, options)


def make_tpl_options(mail_to, args ):
    tf = tempfile.NamedTemporaryFile()
    vars = parse_vars(args.vars)
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
    resp = invoke_swaks(mail_to, options)
    tf.close()
    return resp


def json_serial(obj):
  if isinstance(obj, datetime.datetime):
      serial = obj.isoformat()
      return serial


def make_eml_option(mail_to, args):
    if not os.path.isfile(args.eml):
        raise FileNotFoundError('EML file not found.')
    else:
        options = make_options(args)
        with open(args.eml, 'rb') as eml:
            raw_email = eml.read()
        parser = EmlParser(include_raw_body=True, include_attachment_data=True)
        eml = parser.decode_email_bytes(raw_email)
        header = deepcopy(eml['header'])
        for h_key in header:
            if h_key not in ['to', 'from', 'content-type', 'x-mailer', 'subject']:
                del eml['header'][h_key]
        # print(json.dumps(eml, default=json_serial))
        # print(eml['attachment'])
        # print(parse)
        tf_attach = []
        if 'attachment' in eml:
            for attach in eml['attachment']:
                print(attach['filename'])
                _tf_attach = tempfile.NamedTemporaryFile()
                _tf_attach.write(b64decode(attach['raw']))
                _tf_attach.flush()
                tf_attach.append(_tf_attach)
                options.append(f'--attach @{_tf_attach.name}')
                options.append(f'--attach-name \'{attach["filename"]}\'')
        tf_body = tempfile.NamedTemporaryFile()
        for body in eml['body']:
            if body['content_type'] == 'text/html':
                tf_body.write(body['content'].encode('utf-8'))
                tf_body.flush()
                break
        options.append('--attach-type text/html')
        options.append(f'--attach-body @{tf_body.name}')
        # options.append(f'--data @{args.eml}')
        resp =  invoke_swaks(mail_to, options)
        tf_body.close()
        for _tf_attach in tf_attach:
            _tf_attach.close()
        return resp


def invoke_swaks(mail_to, options):
    options = ' '.join(options)
    cmd = f'swaks --to {mail_to} {options}'
    # return cmd + '\n'
    print(cmd)
    resp = os.popen(cmd).read()
    return resp


def send_mail(mail_to, args):
    resp = ''
    if args.html:
        resp = make_tpl_options(mail_to, args)
    elif args.eml:
        resp = make_eml_option(mail_to, args)
    else:
        resp = make_text_options(mail_to, args)
    return resp
