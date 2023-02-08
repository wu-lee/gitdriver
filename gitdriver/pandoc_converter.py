import json
import pandoc
from urllib.parse import urlparse, parse_qs
from pandocfilters import applyJSONFilters, toJSONFilter, Span, Header, Link

def convert(input_filename, output_extension):
    output_filename = input_filename[:input_filename.rindex('.')] + '.' + output_extension
    doc = pandoc.read(file=input_filename, format='html')
    if output_extension == 'md':
        # pandoc.write(doc, output_filename, format='markdown', filters=['filter_markdown.py'])
        json_doc = json.dumps(pandoc.write_json_v2(doc))
        json_doc_cleaned = applyJSONFilters([filter_attr], json_doc, format="")
        doc_cleaned = pandoc.read_json_v2(json.loads(json_doc_cleaned))
    else:
        doc_cleaned = doc
    pandoc.write(doc_cleaned, output_filename)
    return output_filename

def filter_attr(key, value, format, meta):
    # remove ugly attributes that don't render in markdown
    if key == 'Header':
        return Header(value[0] + 1, ['','',''], value[2])
    if key == 'Span':
        return Span(['','',''], value[1])
    if key == 'Link':
        url = value[2][0]
        # Google Drive hides all the URLs as 'https://www.google.com/url?q=' and appends random tracking things
        u = urlparse(url)
        query = parse_qs(u.query, keep_blank_values=True)
        if 'q' in query:
            real_url = query['q'][0]
        else:
            # links to comments or other relative links
            real_url = url
        return Link(['','',''], value[1], [real_url, ''])
  
if __name__ == '__main__':
    toJSONFilter(filter_attr)