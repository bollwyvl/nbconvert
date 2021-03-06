"""Module that pre-processes the notebook for export to HTML.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
import os
import io
import hashlib

from ipython_genutils import path
from traitlets import Unicode
from ipython_genutils.py3compat import str_to_bytes
from .base import Preprocessor

class CSSHTMLHeaderPreprocessor(Preprocessor):
    """
    Preprocessor used to pre-process notebook for HTML output.  Adds IPython notebook
    front-end CSS and Pygments CSS to HTML output.
    """
    highlight_class = Unicode('.highlight', config=True,
                              help="CSS highlight class identifier")

    def __init__(self, *pargs, **kwargs):
        Preprocessor.__init__(self, *pargs, **kwargs)
        self._default_css_hash = None

    def preprocess(self, nb, resources):
        """Fetch and add CSS to the resource dictionary

        Fetch CSS from IPython and Pygments to add at the beginning
        of the html files.  Add this css in resources in the 
        "inlining.css" key
        
        Parameters
        ----------
        nb : NotebookNode
            Notebook being converted
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            preprocessors to pass variables into the Jinja engine.
        """
        resources['inlining'] = {}
        resources['inlining']['css'] = self._generate_header(resources)
        return nb, resources

    def _generate_header(self, resources):
        """ 
        Fills self.header with lines of CSS extracted from IPython 
        and Pygments.
        """
        from pygments.formatters import HtmlFormatter
        header = []
        
        # Construct path to Jupyter CSS
        import nbconvert.resources
        sheet_filename = os.path.join(
            os.path.dirname(nbconvert.resources.__file__),
            'style.min.css',
        )
        
        # Load style CSS file.
        with io.open(sheet_filename, encoding='utf-8') as f:
            header.append(f.read())

        # Add pygments CSS
        formatter = HtmlFormatter()
        pygments_css = formatter.get_style_defs(self.highlight_class)
        header.append(pygments_css)

        # Load the user's custom CSS and IPython's default custom CSS.  If they
        # differ, assume the user has made modifications to his/her custom CSS
        # and that we should inline it in the nbconvert output.
        try:
            from notebook import DEFAULT_STATIC_FILES_PATH
        except ImportError:
            DEFAULT_STATIC_FILES_PATH = None
        
        config_dir = resources['config_dir']
        custom_css_filename = os.path.join(config_dir, 'custom', 'custom.css')
        if os.path.isfile(custom_css_filename):
            if DEFAULT_STATIC_FILES_PATH and self._default_css_hash is None:
                self._default_css_hash = self._hash(os.path.join(DEFAULT_STATIC_FILES_PATH, 'custom', 'custom.css'))
            if self._hash(custom_css_filename) != self._default_css_hash:
                with io.open(custom_css_filename, encoding='utf-8') as f:
                    header.append(f.read())
        return header

    def _hash(self, filename):
        """Compute the hash of a file."""
        md5 = hashlib.md5()
        with open(filename) as f:
            md5.update(str_to_bytes(f.read()))
        return md5.digest()
