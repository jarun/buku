import os
import re
from babel.messages.frontend import CommandLineInterface as pybabel
try:
    from buku import __version__
except ImportError:
    __version__ = None

DOMAIN = 'messages'
DIR = os.path.dirname(__file__)
BUKUSERVER = os.path.dirname(DIR)
MAPPING = os.path.join(DIR, 'babel.cfg')
TEMPLATE = os.path.join(DIR, 'messages.pot')
CUSTOM = os.path.join(DIR, 'messages_custom.pot')

_EOL, _STR_EOL, _G_STR_EOL = r'$\r?\n?', r'"[^\r\n]*"$\r?\n?', r'"([^\r\n]*)"$\r?\n?'
STRINGS = {
    r'\bPROJECT VERSION\b': __version__ or '???',
    r'(?<=for )PROJECT\b': 'bukuserver',
    r'(?<=as the )PROJECT(?= project)': 'buku',
    r'\bORGANIZATION\b': 'buku',
    f'^# FIRST AUTHOR <EMAIL@ADDRESS>, [0-9]+.{_EOL}': '',
    f'^#, fuzzy{_EOL}': '',
    r'(?<=^"POT-Creation-Date: ).*(?=\\n"$)': '2024-09-12 00:00+0000',  # avoid git updates of unchanged translations
}
OLD_BLANK = re.compile(f'^(?:#~ msgctxt {_STR_EOL})?#~ msgid {_STR_EOL}#~ msgstr ""{_EOL}(?:{_EOL})?', re.MULTILINE)
OLD = re.compile(f'^(?:#~ msgctxt {_G_STR_EOL})?#~ msgid {_G_STR_EOL}#~ msgstr {_G_STR_EOL}(?:{_EOL})?', re.MULTILINE)

def replace_obsolete(text):
    '''Removes *blank* obsolete entries, and restores re-added *blank* values from old obsolete ones'''
    text = re.sub(OLD_BLANK, '', text)
    for obsolete in re.finditer(OLD, text):
        _ctxt, _id, _str = obsolete.groups()
        ctxt_re = ('' if _ctxt is None else f'msgctxt "{re.escape(_ctxt)}"{_EOL}')
        if m := re.search(f'^{ctxt_re}msgid "{re.escape(_id)}"{_EOL}msgstr "()"{_EOL}', text, re.MULTILINE):
            text = (text[:m.start(1)] + _str + text[m.end(1):]).replace(obsolete.group(0), '', 1)
    return text

def translations_generate():
    '''Generates and patches the messages.pot template file'''
    pybabel().run(['', 'extract', '--no-wrap', f'--mapping-file={MAPPING}',
                   '--keywords=_ _l _p:1c,2 _lp:1c,2 lazy_gettext', f'--output-file={TEMPLATE}', BUKUSERVER])
    print(f'patching PO template file at {TEMPLATE}')
    with open(TEMPLATE, encoding='utf-8') as fin:
        text = fin.read()
    for k, v in STRINGS.items():
        text = re.sub(k, v, text, count=1, flags=re.MULTILINE)
    with open(CUSTOM, encoding='utf-8') as fin:
        with open(TEMPLATE, 'w', encoding='utf-8') as fout:
            fout.write(text + fin.read())

def translations_update(new_locales=[], generate=True, domain=DOMAIN, fuzzy=False):
    '''Updates all existing translations (*/LC_MESSAGES/messages.po) based on messages.pot'''
    generate and translations_generate()
    command = (['', 'update', '--no-wrap'] + ([] if fuzzy else ['--no-fuzzy-matching']) +
               [f'--domain={domain}', f'--input-file={TEMPLATE}', f'--output-dir={DIR}'])
    pybabel().run(command)
    for locale in new_locales:
        try:  # trying an update first, to prevent clearing an existing translation
            pybabel().run(command + ['--init-missing', f'--locale={locale}'])
        except FileNotFoundError:
            pybabel().run(['', 'init', '--no-wrap', f'--domain={domain}', f'--input-file={TEMPLATE}',
                           f'--output-dir={DIR}', f'--locale={locale}'])
    # handling obsolete entries (removing blank and restoring re-added keys)
    for locale in os.listdir(DIR):
        filename = os.path.join(DIR, locale, 'LC_MESSAGES', f'{domain}.po')
        if os.path.isfile(filename) and os.access(filename, os.W_OK):
            with open(filename, encoding='utf-8') as fin:
                text = fin.read()
            if text != (stripped := replace_obsolete(text)):
                print(f'processing obsolete entries from catalog {filename}')
                with open(filename, 'w', encoding='utf-8') as fout:
                    fout.write(stripped)

def translations_compile(update=False, generate=True, domain=DOMAIN, new_locales=[], fuzzy=False):
    '''Compiles all existing translations'''
    update and translations_update(generate=generate, domain=DOMAIN, new_locales=new_locales, fuzzy=fuzzy)
    pybabel().run(['', 'compile', f'--domain={domain}', f'--directory={DIR}'])
