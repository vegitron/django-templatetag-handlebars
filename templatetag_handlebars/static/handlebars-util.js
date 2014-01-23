Handlebars.load_template = function (name) {
    if (!Handlebars.templates) {
        Handlebars.templates = {};
    }
    if (!Handlebars.templates[name]) {
        var source = document.getElementById(name).innerHTML;
        var compiled = Handlebars.compile(source);
        Handlebars.templates[name] = compiled;
    }

    return Handlebars.templates[name];
};

