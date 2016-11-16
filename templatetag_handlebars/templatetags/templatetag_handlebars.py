from django import template
from django.conf import settings
from django.utils import six
import subprocess
import codecs
import os

register = template.Library()

"""

    Most of this code was written by Miguel Araujo
    https://gist.github.com/893408

"""


def verbatim_tags(parser, token, endtagname):
    """
    Javascript templates (jquery, handlebars.js, mustache.js) use constructs like:

    ::

        {{if condition}} print something{{/if}}

    This, of course, completely screws up Django templates,
    because Django thinks {{ and }} means something.

    The following code preserves {{ }} tokens.

    This version of verbatim template tag allows you to use tags
    like url {% url name %}. {% trans "foo" %} or {% csrf_token %} within.
    """
    text_and_nodes = []
    while 1:
        token = parser.tokens.pop(0)
        if token.contents == endtagname:
            break

        if token.token_type == template.base.TOKEN_VAR:
            text_and_nodes.append('{{')
            text_and_nodes.append(token.contents)

        elif token.token_type == template.base.TOKEN_TEXT:
            text_and_nodes.append(token.contents)

        elif token.token_type == template.base.TOKEN_BLOCK:
            try:
                command = token.contents.split()[0]
            except IndexError:
                parser.empty_block_tag(token)

            try:
                compile_func = parser.tags[command]
            except KeyError:
                parser.invalid_block_tag(token, command, None)
            try:
                node = compile_func(parser, token)
            except template.TemplateSyntaxError as e:
                if not parser.compile_function_error(token, e):
                    raise
            text_and_nodes.append(node)

        if token.token_type == template.base.TOKEN_VAR:
            text_and_nodes.append('}}')

    return text_and_nodes


class VerbatimNode(template.Node):
    """
    Wrap {% verbatim %} and {% endverbatim %} around a
    block of javascript template and this will try its best
    to output the contents with no changes.

    ::

        {% verbatim %}
            {% trans "Your name is" %} {{first}} {{last}}
        {% endverbatim %}
    """
    def __init__(self, text_and_nodes):
        self.text_and_nodes = text_and_nodes

    def render(self, context):
        output = ""
        # If its text we concatenate it, otherwise it's a node and we render it
        for bit in self.text_and_nodes:
            if isinstance(bit, six.string_types):
                output += bit
            else:
                output += bit.render(context)
        return output


@register.tag
def verbatim(parser, token):
    text_and_nodes = verbatim_tags(parser, token, 'endverbatim')
    return VerbatimNode(text_and_nodes)


@register.simple_tag
def handlebars_js():
    # TODO - make this return the runtime version if using compressed
    # templates (override in config?)

    script_tags = []
    script_tags.append('<script src="%shandlebars-v1.3.0.js"></script>' % settings.STATIC_URL)
    script_tags.append('<script src="%shandlebars-util.js"></script>' % settings.STATIC_URL)
    return "".join(script_tags)

def get_compiled_js_name():
    return getattr(settings, "HANDLEBARS_COMPILED_STATIC_PATH", "compiled_templates.js")

class HandlebarsNode(VerbatimNode):
    """
    A Handlebars.js block is a *verbatim* block wrapped inside a
    named (``template_id``) <script> tag.

    ::

        {% tplhandlebars "tpl-popup" %}
            {{#ranges}}
                <li>{{min}} < {{max}}</li>
            {{/ranges}}
        {% endtplhandlebars %}

    """
    def __init__(self, template_id, text_and_nodes):
        super(HandlebarsNode, self).__init__(text_and_nodes)
        self.template_id = template_id

    def _render_compiled(self, output):
        if not hasattr(settings, "HANDLEBARS_COMPILER"):
            raise Exception("Missing configuration: HANDLEBARS_COMPILER")

        handlebars_command = settings.HANDLEBARS_COMPILER
        handlebars_command = handlebars_command.replace('{template_name}', self.template_id)
        proc = subprocess.Popen(handlebars_command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        out, err = proc.communicate(input=output.encode('utf8'))
        out = out.decode('utf-8')

        compiled_script_name = get_compiled_js_name()
        file_path = os.path.join(settings.STATIC_ROOT, compiled_script_name)

        with codecs.open(file_path, "a", encoding="utf-8") as handle:
            handle.write(out)

        return """<script type="text/javascript">%s</script>""" % out


    def render(self, context):
        output = super(HandlebarsNode, self).render(context)

        if getattr(settings, "HANDLEBARS_PRECOMPILE_TEMPLATES", False):
            return self._render_compiled(output)

        if getattr(settings, 'USE_EMBER_STYLE_ATTRS', False) is True:
            id_attr, script_type = 'data-template-name', 'text/x-handlebars'
        else:
            id_attr, script_type = 'id', 'text/x-handlebars-template'
        head_script = '<script type="%s" %s="%s">' % (script_type, id_attr,
                                                      self.template_id)
        return """
        %s
        %s
        </script>""" % (head_script, output)


@register.tag
def tplhandlebars(parser, token):
    text_and_nodes = verbatim_tags(parser, token, endtagname='endtplhandlebars')
    # Extract template id from token
    tokens = token.split_contents()
    stripquote = lambda s: s[1:-1] if s[:1] == '"' else s
    try:
        tag_name, template_id = map(stripquote, tokens[:2])
    except ValueError:
        raise template.TemplateSyntaxError(
            "%s tag requires exactly one argument" % token.split_contents()[0])
    return HandlebarsNode(template_id, text_and_nodes)
