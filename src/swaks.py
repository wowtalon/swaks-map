import os
import re
import tempfile
from base64 import b64decode, b64encode
from copy import deepcopy
from jinja2 import Template
from time import strftime, localtime
from eml_parser import EmlParser


def eml_base64(text):
    '''
    将文本 base64 编码后发送，可以解决中文乱码的问题
    '''
    text = b64encode(text.encode('utf-8')).decode('utf-8')
    return f'=?UTF-8?B?{text}?='


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
    '''
    发送普通文本邮件
    '''
    options = make_options(args)
    options.append(f'--body \'{args.body}\'')
    return invoke_swaks(mail_to, options)


def make_tpl_options(mail_to, args):
    '''
    从 HTML 模板发送邮件
    '''
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
    tf = tempfile.NamedTemporaryFile()
    content = template.render(vars)
    tf.write(content.encode('utf-8'))
    tf.flush()
    options.append('--attach-type text/html')
    options.append(f'--attach-body @{tf.name}')
    resp = invoke_swaks(mail_to, options)
    tf.close()
    return resp


def make_eml_option(mail_to, args):
    '''
    从 EML 文件发送邮件
    '''
    if not os.path.isfile(args.eml):
        raise FileNotFoundError('EML file not found.')
    else:
        options = make_options(args)
        with open(args.eml, 'rb') as eml:
            raw_email = eml.read()
        # 解析 EML 文件
        parser = EmlParser(include_raw_body=True, include_attachment_data=True)
        eml = parser.decode_email_bytes(raw_email)
        header = deepcopy(eml['header'])
        # 去除无用的 header
        for h_key in header:
            if h_key not in ['to', 'from', 'content-type', 'x-mailer', 'subject']:
                del eml['header'][h_key]
        # 从 EML 中提取邮件标题
        subject = eml_base64(header['subject'])
        options.append(f'--header \'Subject: {subject}\'')
        tf_attach = []
        # 从 EML 中提取附件
        if 'attachment' in eml:
            for attach in eml['attachment']:
                _tf_attach = tempfile.NamedTemporaryFile()
                _tf_attach.write(b64decode(attach['raw']))
                _tf_attach.flush()
                tf_attach.append(_tf_attach)
                filename = eml_base64(attach["filename"])
                options.append(f'--attach-name \'{filename}\'')
                options.append(f'--attach @{_tf_attach.name}')
        # 从 EML 中提取正文
        tf_body = tempfile.NamedTemporaryFile()
        for body in eml['body']:
            if body['content_type'] == 'text/html':
                # 处理编码问题
                try:
                    # 尝试查找编码，找不到编码时默认使用 utf8
                    encoding = body['content_header']['content-type'][0].replace('\'', '"')
                    encoding = re.findall('charset="(.*)"', encoding, re.IGNORECASE)[0]
                except:
                    encoding = 'utf-8'
                tf_body.write(body['content'].encode(encoding))
                tf_body.flush()
                break
        options.append('--attach-type text/html')
        options.append(f'--attach-body @{tf_body.name}')
        resp =  invoke_swaks(mail_to, options)
        # 关闭临时文件
        tf_body.close()
        for _tf_attach in tf_attach:
            _tf_attach.close()
        return resp


def invoke_swaks(mail_to, options):
    # 拼接 swaks 指令，调用 swaks 发送邮件
    options = ' '.join(options)
    cmd = f'swaks --to {mail_to} {options}'
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
