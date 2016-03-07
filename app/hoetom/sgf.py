# coding: utf-8
import re
import json
from app.html import *


if __name__ == '__main__':
    url = 'http://www.hoetom.com/matchviewer_html_2011.jsp?id=135333'
    pattern = r'var steps = (\[.*\]);'
    with HtmlClient() as client:
        sgfhtml = client.get(url=url, encoding='GB18030')
        print(sgfhtml)
        print(sgfhtml.get_title())
        sgfsearch = re.search(pattern, sgfhtml.text, re.I)
        if sgfsearch:
            sgfstr = sgfsearch.group(1)
            print(sgfstr)
            sgfjson = json.loads(sgfstr)
            print(sgfjson)
            for step in sgfjson:
                print()