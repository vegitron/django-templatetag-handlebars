from django.conf import settings
from django import template
from templatetag_handlebars import verbatim_tags, VerbatimNode
from HTMLParser import HTMLParser
import subprocess
import tempfile
import re

register = template.Library()

"""

Code to manage compiling/compressing handlebars templates

"""

# XXX - make it so this only runs offline.  crazy slow.

class CompressNode(template.Node):
    def __init__(self, text_and_nodes):
        self.text_and_nodes = text_and_nodes

    def render(self, context):
        raw_content = VerbatimNode(self.text_and_nodes).render(context)
        if hasattr(settings, "HANDLEBARS_COMPILER"):
            return self.compiled_render(raw_content)
        else:
            return raw_content

    def compiled_render(self, raw_content):
        parser = HandlebarScriptParser()
        parser.feed(raw_content)

        non_template_content = parser.get_non_template_content()
        raw_templates = parser.get_templates()

        compile_root = tempfile.mkdtemp()

        content_parts = []
        content_parts.append('<script type="text/javascript">')

        for template in raw_templates:
            compressed = compress_template(
                            compile_root,
                            template.name,
                            template.raw_content)

            content_parts.append(compressed)

        content_parts.append("</script>")
        content_parts.append(non_template_content)

        return "".join(content_parts)


class HandlebarScriptParser(HTMLParser):
    in_template = False
    template_name = ""
    template_content = ""
    non_template_content_parts = []
    handlebar_templates = []

    def get_templates(self):
        return self.handlebar_templates

    def get_non_template_content(self):
        return "".join(self.non_template_content_parts)

    def handle_starttag(self, tag, attrs):
        template_name = None
        script_type = None

        for attr in attrs:
            if "id" == attr[0]:
                template_name = attr[1]
            elif "type" == attr[0]:
                script_type = attr[1]

        if "script" == tag and template_name is not None and "text/x-handlebars-template" == script_type:
            self.in_template = True
            self.template_name = template_name
            self.template_content = ""

        else:
            self.non_template_content_parts.append("<")
            self.non_template_content_parts.append(tag)
            for attr in attrs:
                self.non_template_content_parts.append(" ")
                self.non_template_content_parts.append(attr[0])
                self.non_template_content_parts.append('="')
                self.non_template_content_parts.append(attr[1])
                self.non_template_content_parts.append('"')
            self.non_template_content_parts.append(">")

    def handle_endtag(self, tag):
        if "script" == tag and True == self.in_template:
            # print "Content for %s: %s" % (self.template_name, self.template_content)
            template = HandlebarTemplate()
            template.name = self.template_name
            template.raw_content = self.template_content
            self.handlebar_templates.append(template)

            self.template_content = ""
            self.template_name = ""
            self.in_template = False

        else:
            self.non_template_content_parts.append("</")
            self.non_template_content_parts.append(tag)
            self.non_template_content_parts.append(">")

    def handle_data(self, data):
        if True == self.in_template:
            self.template_content = data

        else:
            if re.search(r'\S', data, re.MULTILINE):
                self.non_template_content_parts.append(data)


class HandlebarTemplate(object):
    name = ""
    raw_content = ""


@register.tag
def compress_handlebars(parser, token):
    text_and_nodes = verbatim_tags(parser, token, "endcompress_handlebars")
    return CompressNode(text_and_nodes)


def compress_template(compress_path, name, content):
    raw_path = "%s/%s" % (compress_path, name)
    compiled_path = "%s/%s.compiled" % (compress_path, name)

    f = open(raw_path, "wb")
    f.write(content)
    f.close()

    if not hasattr(settings, "HANDLEBARS_COMPILER"):
        raise Exception("Missing configuration: HANDLEBARS_COMPILER")


    handlebars_command = settings.HANDLEBARS_COMPILER
    handlebars_command = handlebars_command.replace('{infile}', raw_path)
    handlebars_command = handlebars_command.replace('{outfile}', compiled_path)

    proc = subprocess.Popen(handlebars_command, shell=True)

    if proc.wait() != 0:
        raise Exception("Unable to run %s", handlebars_command)

    f = open(compiled_path, "rb")
    content = f.read()
    f.close()

    return content
