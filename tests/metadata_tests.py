"""
Unit tests for the metadata parts.
"""


import logging
import sys

from lxml import html
from lxml.etree import XPath

from trafilatura.json_metadata import normalize_authors, normalize_json
from trafilatura.metadata import check_authors, extract_metadata, extract_metainfo, extract_url, normalize_tags

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def test_titles():
    '''Test the extraction of titles'''
    tests = [
        ('<html><body><h3 class="title">T</h3><h3 id="title"></h3></body></html>', None),
        ('<html><head><title>Test Title</title><meta property="og:title" content=" " /></head><body><h1>First</h1></body></html>', 'First'),
        ('<html><head><title>Test Title</title><meta name="title" content=" " /></head><body><h1>First</h1></body></html>', 'First'),
        ('<html><head><title>Test Title</title></head><body></body></html>', 'Test Title'),
        ('<html><body><h1>First</h1><h1>Second</h1></body></html>', 'First'),
        ('<html><body><h1>   </h1><div class="post-title">Test Title</div></body></html>', 'Test Title'),
        ('<html><body><h2 class="block-title">Main menu</h2><h1 class="article-title">Test Title</h1></body></html>', 'Test Title'),
        ('<html><body><h2>First</h2><h1>Second</h1></body></html>', 'Second'),
        ('<html><body><h2>First</h2><h2>Second</h2></body></html>', 'First'),
        ('<html><body><title></title></body></html>', None)
    ]

    for doc, expected_title in tests:
        metadata = extract_metadata(doc)
        assert metadata.title == expected_title

    metadata = extract_metadata(r'''<html><body><script type="application/ld+json">{"@context":"https:\/\/schema.org","@type":"Article","name":"Semantic satiation","url":"https:\/\/en.wikipedia.org\/wiki\/Semantic_satiation","sameAs":"http:\/\/www.wikidata.org\/entity\/Q226007","mainEntity":"http:\/\/www.wikidata.org\/entity\/Q226007","author":{"@type":"Organization","name":"Contributors to Wikimedia projects"},"publisher":{"@type":"Organization","name":"Wikimedia Foundation, Inc.","logo":{"@type":"ImageObject","url":"https:\/\/www.wikimedia.org\/static\/images\/wmf-hor-googpub.png"}},"datePublished":"2006-07-12T09:27:14Z","dateModified":"2020-08-31T23:55:26Z","headline":"psychological phenomenon in which repetition causes a word to temporarily lose meaning for the listener"}</script>
<script>(RLQ=window.RLQ||[]).push(function(){mw.config.set({"wgBackendResponseTime":112,"wgHostname":"mw2373"});});</script></html>''')
    assert metadata.title == 'Semantic satiation'
    metadata = extract_metadata('<html><head><title> - Home</title></head><body/></html>')
    assert metadata.title == '- Home'
    metadata = extract_metadata('<html><head><title>My Title » My Website</title></head><body/></html>')
    assert metadata.title == "My Title"  # TODO: and metadata.sitename == "My Website"


def test_authors():
    '''Test the extraction of author names'''
    # normalization
    assert normalize_authors(None, 'abc') == 'Abc'
    assert normalize_authors(None, 'Steve Steve 123') == 'Steve Steve'
    assert normalize_authors(None, 'By Steve Steve') == 'Steve Steve'
    assert normalize_json('Test \\nthis') == 'Test this'
    assert normalize_json('\\uD800\\uDC00Hello\\uDBFF\\uDFFF') == 'Hello'
    assert normalize_json('Test \u3010ABC\u3011') == 'Test 【ABC】'
    assert normalize_json("Seán Federico O'Murchú") == "Seán Federico O'Murchú"

    # blacklist
    metadata = extract_metadata('<html><head><meta itemprop="author" content="Jenny Smith"/></head><body></body></html>', author_blacklist={'Jenny Smith'})
    assert metadata.author is None

    # extraction
    begin, end = '<html><head>', '</head><body></body></html>'
    htmldocs = [
        f'{begin}<meta itemprop="author" content="Jenny Smith"/>{end}',
        f'{begin}<meta itemprop="author" content="Jenny Smith"/><meta itemprop="author" content="John Smith"/>{end}',
        f'{begin}<meta itemprop="author" content="Jenny Smith und John Smith"/>{end}',
        f'{begin}<meta name="author" content="Jenny Smith"/><meta name="author" content="John Smith"/>{end}',
        f'{begin}<meta name="author" content="Jenny Smith and John Smith"/>{end}',
        f'{begin}<meta name="author" content="Jenny Smith"/>{end}',
        f'{begin}<meta name="author" content="Hank O&#39;Hop"/>{end}',
        f'{begin}<meta name="author" content="Jenny Smith ❤️"/>{end}',
        f'{begin}<meta name="citation_author" content="Jenny Smith and John Smith"/>{end}',
        f'{begin}<meta property="author" content="Jenny Smith"/><meta property="author" content="John Smith"/>{end}',
        f'{begin}<meta itemprop="author" content="Jenny Smith and John Smith"/>{end}',
        f'{begin}<meta name="article:author" content="Jenny Smith"/>{end}',
    ]
    expected_authors = [
        'Jenny Smith',
        'Jenny Smith; John Smith',
        'Jenny Smith; John Smith',
        'Jenny Smith; John Smith',
        'Jenny Smith; John Smith',
        'Jenny Smith',
        'Hank O\'Hop',
        'Jenny Smith',
        'Jenny Smith; John Smith',
        'Jenny Smith; John Smith',
        'Jenny Smith; John Smith',
        'Jenny Smith',
    ]


    for doc, expected_author in zip(htmldocs, expected_authors):
        metadata = extract_metadata(doc)
        assert metadata.author == expected_author

    begin, end = '<html><body>', '</body></html>'
    htmldocs = [
        f'{begin}<a href="" rel="author">Jenny Smith</a>{end}',
        f'{begin}<a href="" rel="author">Jenny "The Author" Smith</a>{end}',
        f'{begin}<span class="author">Jenny Smith</span>f{end}',
        f'{begin}<h4 class="author">Jenny Smith</h4>f{end}',
        f'{begin}<h4 class="author">Jenny Smith — Trafilatura</h4>f{end}',
        f'{begin}<span class="wrapper--detail__writer">Jenny Smith</span>f{end}',
        f'{begin}<span id="author-name">Jenny Smith</span>f{end}',
        f'{begin}<figure data-component="Figure"><div class="author">Jenny Smith</div></figure>f{end}',
        f'{begin}<div class="sidebar"><div class="author">Jenny Smith</div></figure>f{end}',
        f'{begin}<div class="quote"><p>My quote here</p><p class="quote-author"><span>—</span> Jenny Smith</p></div>f{end}',
        f'{begin}<span class="author">Jenny Smith and John Smith</span>f{end}',
        f'{begin}<a class="author">Jenny Smith</a>f{end}',
        f'{begin}<a class="author">Jenny Smith <div class="title">Editor</div></a>f{end}',
        f'{begin}<a class="author">Jenny Smith from Trafilatura</a>f{end}',
        f'{begin}<meta itemprop="author" content="Fake Author"/><a class="author">Jenny Smith from Trafilatura</a>f{end}',
        f'{begin}<a class="username">Jenny Smith</a>f{end}',
        f'{begin}<div class="submitted-by"><a>Jenny Smith</a></div>f{end}',
        f'{begin}<div class="byline-content"><div class="byline"><a>Jenny Smith</a></div><time>July 12, 2021 08:05</time></div>f{end}',
        f'{begin}<h3 itemprop="author">Jenny Smith</h3>f{end}',
        f'{begin}<div class="article-meta article-meta-byline article-meta-with-photo article-meta-author-and-reviewer" itemprop="author" itemscope="" itemtype="http://schema.org/Person"><span class="article-meta-photo-wrap"><img src="" alt="Jenny Smith" itemprop="image" class="article-meta-photo"></span><span class="article-meta-contents"><span class="article-meta-author">By <a href="" itemprop="url"><span itemprop="name">Jenny Smith</span></a></span><span class="article-meta-date">May 18 2022</span><span class="article-meta-reviewer">Reviewed by <a href="">Robert Smith</a></span></span></div>f{end}',
        f'{begin}<div data-component="Byline">Jenny Smith</div>f{end}',
        f'{begin}<span id="author">Jenny Smith</span>f{end}',
        f'{begin}<span id="author">Jenny Smith – The Moon</span>f{end}',
        f'{begin}<span id="author">Jenny_Smith</span>f{end}',
    ]
    expected_authors = [
        'Jenny Smith',
        'Jenny Smith',
        'Jenny Smith',
        'Jenny Smith',
        'Jenny Smith',
        'Jenny Smith',
        'Jenny Smith',
        None,
        None,
        None,
        'Jenny Smith; John Smith',
        'Jenny Smith',
        'Jenny Smith',
        'Jenny Smith',
        'Jenny Smith',
        'Jenny Smith',
        'Jenny Smith',
        'Jenny Smith',
        'Jenny Smith',
        'Jenny Smith',
        'Jenny Smith',
        'Jenny Smith',
        'Jenny Smith',
        'Jenny Smith',
    ]

    for doc, expected_author in zip(htmldocs, expected_authors):
        metadata = extract_metadata(doc)
        assert metadata.author == expected_author

    htmldocs = [
        f'{begin}<span itemprop="author name">Shannon Deery, Mitch Clarke, Susie O’Brien, Laura Placella, Kara Irving, Jordy Atkinson, Suzan Delibasic</span>f{end}',
        f'{begin}<address class="author">Jenny Smith</address>f{end}',
        f'{begin}<author>Jenny Smith</author>f{end}',
        '<html><head><meta data-rh="true" property="og:author" content="By &lt;a href=&quot;/profiles/amir-vera&quot;&gt;Amir Vera&lt;/a&gt;, Seán Federico O&#x27;Murchú, &lt;a href=&quot;/profiles/tara-subramaniam&quot;&gt;Tara Subramaniam&lt;/a&gt; and Adam Renton, CNN"/></head><body>f{end}',
        f'{begin}<div class="author"><span class="profile__name"> Jenny Smith </span> <a href="https://twitter.com/jenny_smith" class="profile__social" target="_blank"> @jenny_smith </a> <span class="profile__extra lg:hidden"> 11:57AM </span> </div>f{end}',
        f'{begin}<p class="author-section byline-plain">By <a class="author" rel="nofollow">Jenny Smith For Daily Mail Australia</a></p>f{end}',
        f'{begin}<div class="o-Attribution__a-Author"><span class="o-Attribution__a-Author--Label">By:</span><span class="o-Attribution__a-Author--Prefix"><span class="o-Attribution__a-Name"><a href="//web.archive.org/web/20210707074846/https://www.discovery.com/profiles/ian-shive">Ian Shive</a></span></span></div>f{end}',
        f'{begin}<div class="ArticlePage-authors"><div class="ArticlePage-authorName" itemprop="name"><span class="ArticlePage-authorBy">By&nbsp;</span><a aria-label="Ben Coxworth" href="https://newatlas.com/author/ben-coxworth/"><span>Ben Coxworth</span></a></div></div>f{end}',
        f'{begin}<div><strong><a class="d1dba0c3091a3c30ebd6" data-testid="AuthorURL" href="/by/p535y1">AUTHOR NAME</a></strong></div>f{end}'
    ]
    expected_authors = [
        'Shannon Deery; Mitch Clarke; Susie O’Brien; Laura Placella; Kara Irving; Jordy Atkinson; Suzan Delibasic',
        'Jenny Smith',
        'Jenny Smith',
        "Amir Vera; Seán Federico O'Murchú; Tara Subramaniam; Adam Renton; CNN",
        'Jenny Smith',
        'Jenny Smith',
        'Ian Shive',
        'Ben Coxworth',
        'AUTHOR NAME'
    ]

    for doc, expected_author in zip(htmldocs, expected_authors):
        metadata = extract_metadata(doc)
        assert metadata.author == expected_author

    # check authors string
    blacklist = {"A", "b"}
    assert check_authors("a; B; c; d", blacklist) == "c; d"
    assert check_authors("a;B;c;d", blacklist) == "c; d"


def test_url():
    '''Test URL extraction'''
    htmldocs = [
        '<html><head><meta property="og:url" content="https://example.org"/></head><body></body></html>',
        '<html><head><link rel="canonical" href="https://example.org"/></head><body></body></html>',
        '<html><head><meta name="twitter:url" content="https://example.org"/></head><body></body></html>',
        '<html><head><link rel="alternate" hreflang="x-default" href="https://example.org"/></head><body></body></html>',
        '<html><head><link rel="canonical" href="/article/medical-record"/></head><body></body></html>'
        '<html><head><base href="https://example.org" target="_blank"/></head><body></body></html>',
    ]
    default_urls = [None, None, None, None, "https://example.org", None]
    expected_url = 'https://example.org'

    for doc, default_url in zip(htmldocs, default_urls):
        metadata = extract_metadata(doc, default_url)
        assert metadata.url == expected_url

    # test on partial URLs
    url = extract_url(html.fromstring('<html><head><link rel="canonical" href="/article/medical-record"/><meta name="twitter:url" content="https://example.org"/></head><body></body></html>'))
    assert url == 'https://example.org/article/medical-record'


def test_description():
    '''Test the extraction of descriptions'''
    metadata = extract_metadata('<html><head><meta itemprop="description" content="Description"/></head><body></body></html>')
    assert metadata.description == 'Description'
    metadata = extract_metadata('<html><head><meta property="og:description" content="&amp;#13; A Northern Territory action plan, which includes plans to support development and employment on Aboriginal land, has received an update. &amp;#13..." /></head><body></body></html>')
    assert metadata.description == 'A Northern Territory action plan, which includes plans to support development and employment on Aboriginal land, has received an update. ...'


def test_dates():
    '''Simple tests for date extraction (most of the tests are carried out externally for htmldate module)'''
    tests = [
        ('<html><head><meta property="og:published_time" content="2017-09-01"/></head><body></body></html>',
        '2017-09-01', False),
        ('<html><head><meta property="og:url" content="https://example.org/2017/09/01/content.html"/></head><body></body></html>',
        '2017-09-01', False),
        ('<html><head><meta property="og:url" content="https://example.org/2017/09/01/content.html"/></head><body></body></html>',
        '2017-09-01', False),
        ('<html><body><p>Veröffentlicht am 1.9.17</p></body></html>', '2017-09-01', True),
        ('<html><body><p>Veröffentlicht am 1.9.17</p></body></html>', '2017-09-01', False),
    ]

    for doc, expected, extensive in tests:
        metadata = extract_metadata(doc, extensive=extensive)
        assert metadata.date == expected


def test_sitename():
    '''Test extraction of site name'''
    tests = [
        ('<html><head><meta name="article:publisher" content="@"/></head><body/></html>', None),
        ('<html><head><meta name="article:publisher" content="The Newspaper"/></head><body/></html>', 'The Newspaper'),
        ('<html><head><meta property="article:publisher" content="The Newspaper"/></head><body/></html>', 'The Newspaper'),
        ('<html><head><title>sitemaps.org - Home</title></head><body/></html>', 'sitemaps.org'),
    ]

    for doc, expected in tests:
        metadata = extract_metadata(doc)
        assert metadata.sitename == expected


def test_meta():
    '''Test extraction out of meta-elements'''
    doc = html.fromstring("<html><p class='test'>a</p><p class='other'>b</p><p type='this'>cde</p></html>")
    assert extract_metainfo(doc, [XPath(".//p[@class]")]) is None
    assert extract_metainfo(doc, [XPath(".//p[@type]")]) == "cde"

    metadata = extract_metadata('<html><head><meta property="og:title" content="Open Graph Title"/><meta property="og:author" content="Jenny Smith"/><meta property="og:description" content="This is an Open Graph description"/><meta property="og:site_name" content="My first site"/><meta property="og:url" content="https://example.org/test"/><meta property="og:type" content="Open Graph Type"/></head><body><a rel="license" href="https://creativecommons.org/">Creative Commons</a></body></html>')
    assert metadata.pagetype == 'Open Graph Type'
    assert metadata.title == 'Open Graph Title'
    assert metadata.author == 'Jenny Smith'
    assert metadata.description == 'This is an Open Graph description'
    assert metadata.sitename == 'My first site'
    assert metadata.url == 'https://example.org/test'
    assert metadata.license == 'Creative Commons'

    metadata = extract_metadata('<html><head><meta name="dc.title" content="Open Graph Title"/><meta name="dc.creator" content="Jenny Smith"/><meta name="dc.description" content="This is an Open Graph description"/></head><body></body></html>')
    assert metadata.title == 'Open Graph Title'
    assert metadata.author == 'Jenny Smith'
    assert metadata.description == 'This is an Open Graph description'

    metadata = extract_metadata('<html><head><meta itemprop="headline" content="Title"/></head><body></body></html>')
    assert metadata.title == 'Title'

    # catch errors
    metadata = extract_metadata('')
    target_slots = set(metadata.__slots__) - {"body", "commentsbody"}
    assert all(getattr(metadata, a) is None for a in target_slots)
    metadata = extract_metadata('<html><title></title></html>')
    assert metadata.sitename is None
    metadata = extract_metadata('<html><head><title>' + 'AAA'*10000 + '</title></head></html>')
    assert metadata.title.endswith('…') and len(metadata.title) == 10000
    assert extract_metadata('<html><head><meta otherkey="example" content="Unknown text"/></head></html>') is not None
    assert extract_metadata('<html><head><title></title><title></title><title></title></head></html>') is not None


def test_catstags():
    '''Test extraction of categories and tags'''
    assert normalize_tags("   ") == ""
    assert normalize_tags(" 1 &amp; 2 ") == "1 & 2"

    htmldocs = [
        '<html><body><p class="entry-categories"><a href="https://example.org/category/cat1/">Cat1</a>, <a href="https://example.org/category/cat2/">Cat2</a></p></body></html>',
        '<html><body><div class="postmeta"><a href="https://example.org/category/cat1/">Cat1</a></div></body></html>',
        '<html><body><p class="entry-tags"><a href="https://example.org/tags/tag1/">Tag1</a>, <a href="https://example.org/tags/tag2/">Tag2</a></p></body></html>',
        '<html><head><meta name="keywords" content="sodium, salt, paracetamol, blood, pressure, high, heart, &amp;quot, intake, warning, study, &amp;quot, medicine, dissolvable, cardiovascular" /></head></html>',
    ]
    attrs = ['categories', 'categories', 'tags', 'tags']
    expected = [
        ['Cat1', 'Cat2'],
        ['Cat1'],
        ['Tag1', 'Tag2'],
        ['sodium, salt, paracetamol, blood, pressure, high, heart, intake, warning, study, medicine, dissolvable, cardiovascular'],
    ]

    for doc, attr, expected_value in zip(htmldocs, attrs, expected):
        metadata = extract_metadata(doc)
        assert getattr(metadata, attr) == expected_value


def test_license():
    '''Test extraction of CC licenses'''
    # a rel
    metadata = extract_metadata('<html><body><p><a href="https://creativecommons.org/licenses/by-sa/4.0/" rel="license">CC BY-SA</a></p></body></html>')
    assert metadata.license == 'CC BY-SA 4.0'
    metadata = extract_metadata('<html><body><p><a href="https://licenses.org/unknown" rel="license">Unknown</a></p></body></html>')
    assert metadata.license == 'Unknown'
    # footer
    metadata = extract_metadata('<html><body><footer><a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA</a></footer></body></html>')
    assert metadata.license == 'CC BY-SA 4.0'
    # footer: netzpolitik.org
    metadata = extract_metadata('''<html><body>
<div class="footer__navigation">
<p class="footer__licence">
            <strong>Lizenz: </strong>
            Die von uns verfassten Inhalte stehen, soweit nicht anders vermerkt, unter der Lizenz
            <a href="http://creativecommons.org/licenses/by-nc-sa/4.0/">Creative Commons BY-NC-SA 4.0.</a>
        </p>
    </div>
</body></html>''')
    assert metadata.license == 'CC BY-NC-SA 4.0'
    # this is not a license
    metadata = extract_metadata('''<html><body><footer class="entry-footer">
	<span class="cat-links">Posted in <a href="https://sallysbakingaddiction.com/category/seasonal/birthday/" rel="category tag">Birthday</a></span>
	</footer></body></html>''')
    assert metadata.license is None
    # this is a license
    metadata = extract_metadata('''<html><body><footer class="entry-footer">
	<span>The license is <a href="https://example.org/1">CC BY-NC</a></span>
	</footer></body></html>''')
    assert metadata.license == 'CC BY-NC'


def test_images():
    '''Image extraction from meta SEO tags'''
    htmldocs = [
        '<html><head><meta property="image" content="https://example.org/example.jpg"></html>',
        '<html><head><meta property="og:image:url" content="example.jpg"></html>',
        '<html><head><meta property="og:image" content="https://example.org/example-opengraph.jpg" /><body/></html>',
        '<html><head><meta property="twitter:image" content="https://example.org/example-twitter.jpg"></html>',
        '<html><head><meta property="twitter:image:src" content="example-twitter.jpg"></html>',
        '<html><head><meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" /></html>',
    ]
    expected_images = [
        'https://example.org/example.jpg',
        'example.jpg',
        'https://example.org/example-opengraph.jpg',
        'https://example.org/example-twitter.jpg',
        'example-twitter.jpg',
        None,
    ]

    for doc, expected_image in zip(htmldocs, expected_images):
        metadata = extract_metadata(doc)
        assert metadata.image == expected_image


def test_document_as_dict():
    """Tests that the dict serialization works and preserves data."""

    htmldoc = """
    <html>
    <head>
        <title>Test Title</title>
        <meta itemprop="author" content="Jenny Smith" />
        <meta property="og:url" content="https://example.org" />
        <meta itemprop="description" content="Description" />
        <meta property="og:published_time" content="2017-09-01" />
        <meta name="article:publisher" content="The Newspaper" />
        <meta property="image" content="https://example.org/example.jpg" />
    </head>
    <body>
        <p class="entry-categories">
        <a href="https://example.org/category/cat1/">Cat1</a>,
        <a href="https://example.org/category/cat2/">Cat2</a>
        </p>
        <p>
        <a href="https://creativecommons.org/licenses/by-sa/4.0/" rel="license"
            >CC BY-SA</a
        >
        </p>
    </body>
    </html>
    """

    document = extract_metadata(htmldoc)
    dict_ = document.as_dict()
    assert dict_["title"] == "Test Title"
    assert dict_["author"] == "Jenny Smith"
    assert dict_["url"] == "https://example.org"
    assert dict_["description"] == "Description"
    assert dict_["sitename"] == "The Newspaper"
    assert dict_["date"] == "2017-09-01"
    assert dict_["categories"] == ["Cat1", "Cat2"]
    assert dict_["license"] == "CC BY-SA 4.0"
    assert dict_["image"] == "https://example.org/example.jpg"


if __name__ == '__main__':
    test_titles()
    test_authors()
    test_dates()
    test_meta()
    test_url()
    test_description()
    test_catstags()
    test_sitename()
    test_license()
    test_images()
    test_document_as_dict()
