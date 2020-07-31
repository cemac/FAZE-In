from flask import render_template

# Error Pages ----------------------------------------------------------------
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html.j2'), 404


def page_not_allowed(e):
    # note that we set the 403 status explicitly
    return render_template('403.html.j2'), 403


def internal_error(error):
    app.logger.error('Server Error: %s', (error))
    return render_template('500.html.j2'), 500


def unhandled_exception(e):
    app.logger.error('Unhandled Exception: %s', (e))
    return render_template('500.html.j2'), 501
