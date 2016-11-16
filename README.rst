*django-templatetag-handlebars* allows you to embed `Handlebars.js <http://handlebarsjs.com>`_ 
templates in your django templates.

Most of the template tag code comes from `Miguel Araujo's verbatim snippet <https://gist.github.com/893408>`_. 

=======
INSTALL
=======

::

    pip install django-templatetag-handlebars

=====
USAGE
=====

* Add ``templatetag_handlebars`` to your ``INSTALLED_APPS``

* Add the HTML footer:

::

    {% load templatetag_handlebars %}

    ...
    {% handlebars_js %}
    </body>

* Call the template tag, and write your Handlebars template :

::

    {% tplhandlebars "tpl-infos" %}
        {{total}} {% trans "result(s)." %}
        <p>{% trans "Min" %}: {{min}}</p>
        <p>{% trans "Max" %}: {{max}}</p>
    {% endtplhandlebars %}

* The following block with end-up in your page :

::

    <script type="text/x-handlebars" id="tpl-infos">

        {{total}} result(s).
        <p>Min: {{min}}</p>
        <p>Max: {{max}}</p>
    <script>

* Your rendered string is ready, and waiting to be inserted in your DOM :)

::

    10 result(s).
    <p>Min: 4</p>
    <p>Max: 5</p>

Advanced
========

* To enable compression, you need to define HANDLEBARS_COMPILER in your settings.  For example:

::

    HANDLEBARS_PRECOMPILE_TEMPLATES = True
    HANDLEBARS_COMPILER = "/usr/local/bin/handlebars -N {template_name} -m -i -"


A ``{% verbatim %}`` tag is available to escape a specific part. For 
example, you may want a subpart of your *Handlebars* template to be 
rendered by Django :

::

    <script type="text/x-handlebars" id="tpl-django-form">

        <form>
            {% verbatim %}
                {{#if id}}<h1>{{first}} {{last}}</h1>{{/if}}
                
                {% trans "Your id is" %} {{ id }}
            {% endverbatim %}
            {{ yourform.as_p }}
        </form>
    </script>


Using Ember.js
==============

In ``settings.py`` ensure to set the following attribute to ``True``. This is due to `Ember.js <http://emberjs.com/>`_ expecting a slightly different script id declaration

::

    USE_EMBER_STYLE_ATTRS = True


The script block will be rendered like ```<script type="text/x-handlebars" data-template-name="%s">```.

=======
AUTHORS
=======

    * Mathieu Leplatre <mathieu.leplatre@makina-corpus.com>
    * Miguel Araujo <https://github.com/maraujop>
    * Ross Crawford-d'Heureuse <https://github.com/stard0g101>
    * Patrick Michaud <https://github.com/vegitron>

|makinacom|_

.. |makinacom| image:: http://depot.makina-corpus.org/public/logo.gif
.. _makinacom:  http://www.makina-corpus.com


Similar tools
=============

* `django-handlebars by Sergii Iavorskyi <https://github.com/yavorskiy/django-handlebars>`_, which focuses on server-side Handlebars rendering.
* `django-handlebars by Chris Vigelius <https://bitbucket.org/chrisv/django-handlebars>`_, with templates in separate files, and served in one block.

=======
LICENSE
=======

    * Lesser GNU Public License
    * ``Handlebars.js`` is released under the MIT license - Copyright 2011 Yehuda Katz
