
from tiddlyweb.wikitext import render_wikitext
from creoleparser import text2html


def render(tiddler, environ):
    # XXX this pays no attention to path and it should when
    # creating links.
    return text2html(tiddler.text)


def init(config_in):
    config['wikitext.type_render_map']['text/x-creole'] = 'creolerender'


if __name__ == '__main__':
    from tiddlyweb.model.tiddler import Tiddler
    tiddler = Tiddler('foo')
    tiddler.text = '==Hello==\n[[Hello]]'

    print render_wikitext(tiddler, '', {'tiddlyweb.config': {'wikitext.type_render_map': {'text/x-creole': 'creolerender'}}})
    tiddler.type = 'text/x-creole'
    print render_wikitext(tiddler, '', {'tiddlyweb.config': {'wikitext.type_render_map': {'text/x-creole': 'creolerender'}}})
