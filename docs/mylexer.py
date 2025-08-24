from pygments.lexer import RegexLexer
from pygments.token import Text, Comment, Keyword, Name

class FirstWordLexer(RegexLexer):
    name = "FirstWord"
    aliases = ["firstword"]
    filenames = ["*.fw"]

    tokens = {
        'root': [
            # Comments (everything after #)
            (r'#.*$', Comment.Single),

            # First word (up to first space)
            (r'^\s*([^\s#]+)', Keyword),  # highlight first token

            # Everything else on the line (non-comment)
            (r'[^#\n]+', Name),

            # Newlines
            (r'\n', Text),
        ]
    }
