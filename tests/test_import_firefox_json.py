import json
from buku import import_firefox_json


def test_load_from_empty():
    """test method."""
    # Arrange
    data = json.loads("{}")

    # Act
    items = import_firefox_json(data)

    # Assert
    count = sum(1 for _ in items)
    assert 0 == count

def test_load_full_entry():
    """test method."""
    
    # Arrange
    data = json.loads("""
        {
            "title" : "title",
            "children": [
                {
                  "dateAdded": 1269200039653000,
                  "guid": "xxxydfalkj",
                  "id": 113,
                  "index": 0,
                  "lastModified": 1305978154986000,
                  "title": "title",
                  "type": "text/x-moz-place",
                  "typeCode": 1,
                  "tags" : "x,y",
                  "uri": "http://uri.com/abc?234&536",
                  "annos" : [{
                         "name": "bookmarkProperties/description",
                         "value": "desc"
                   }]
                }]
        }""")

    # Act
    items = import_firefox_json(data)

    # Assert
    result = []
    for item in items:
        result.append(item)

    assert 1 == len(result)
    assert 'http://uri.com/abc?234&536' == result[0][0]
    assert 'title' == result[0][1]
    assert ',x,y,' == result[0][2]
    assert 'desc' == result[0][3]


def test_load_no_typecode():
    """test method."""
    # Arrange
    data = json.loads("""
        {
            "title" : "title",
            "children": [
                {
                    "title" : "title1",
                    "uri" : "http://uri1",
                    "annos" : [{
                         "name": "bookmarkProperties/description",
                         "value": "desc"
                     }]
                }]
        }""")

    # Act
    items = import_firefox_json(data)

    # Assert
    result = []
    for item in items:
        result.append(item)

    assert 0 == len(result)


def test_load_invalid_typecode():
    """test method."""
    # Arrange
    data = json.loads("""
        {
            "title" : "title",
            "children": [
                {
                    "title" : "title1",
                    "typeCode" : 99,
                    "uri" : "http://uri1",
                    "annos" : [{
                         "name": "bookmarkProperties/description",
                         "value": "desc"
                     }]
                }]
        }""")
    # Act
    items = import_firefox_json(data)

    # Assert
    result = []
    for item in items:
        result.append(item)

    assert 0 == len(result)


def test_load_one_child():
    """test method."""

    # Arrange
    data = json.loads("""
        {
            "title" : "title",
            "typeCode" : 2,
            "children": [
                {
                    "title" : "title1",
                    "typeCode" : 1,
                    "uri" : "http://uri1",
                    "annos" : [{
                         "name": "bookmarkProperties/description",
                         "value": "desc"
                      }]
                 }
            ]
        } """)

    # Act
    items = import_firefox_json(data)

    # Assert
    result = []
    for item in items:
        result.append(item)

    assert 1 == len(result)
    assert 'http://uri1' == result[0][0]
    assert 'title1' == result[0][1]
    assert ',' == result[0][2]
    assert 'desc' == result[0][3]

def test_load_one_container_child():
    """test method."""

    # Arrange
    data = json.loads("""
        {
            "title" : "title",
            "typeCode" : 2,
            "children": [
                {
                    "title":"bookmark folder",
                    "typeCode":2
                } ]
         }""")

    # Act
    items = import_firefox_json(data)

    # Assert
    result = []
    for item in items:
        result.append(item)

    assert 0 == len(result)

def test_load_many_children():
    """test method."""

    # Arrange
    data = json.loads("""
            {
                "title":"Weitere Lesezeichen",
                "typeCode":2,
                "children": [
                    {"title":"title1","typeCode":1,"uri":"http://uri1.com/#more-74"},
                    {"title":"title2","typeCode":1,"uri":"http://uri2.com/xyz"},
                    {"title":"title3","typeCode":1,"uri":"http://uri3.com"}
                ]
            } """)

    # Act
    items = import_firefox_json(data)

    # Assert
    result = []
    for item in items:
        result.append(item)

    assert 3 == len(result)

def test_load_hierarchical_container():
    """test method."""

    # Arrange
    data = json.loads("""
        {
            "title" : "title",
            "typeCode" : 2,
            "children": [
                    {
                        "title" : "title",
                        "typeCode" : 2,
                        "children": [
                            {"title":"title1","typeCode":1,"uri":"http://uri1.com/#more-74"},
                            {"title":"title2","typeCode":1,"uri":"http://uri2.com/xyz"},
                            {"title":"title3","typeCode":1,"uri":"http://uri3.com"}
                        ]
                    },
                    {"title":"title4","typeCode":1,"uri":"http://uri4.com/#more-74"},
                    {"title":"title5","typeCode":1,"uri":"http://uri5.com/xyz"},
                    {"title":"title6","typeCode":1,"uri":"http://uri6.com"}
            ]
        }
                      """)

    # Act
    items = import_firefox_json(data)

    # Assert
    result = []
    for item in items:
        result.append(item)

    assert 6 == len(result)
    assert 'http://uri1.com/#more-74' == result[0][0]
    assert 'http://uri2.com/xyz' == result[1][0]
    assert 'http://uri3.com' == result[2][0]
    assert 'http://uri4.com/#more-74' == result[3][0]
    assert 'http://uri5.com/xyz' == result[4][0]
    assert 'http://uri6.com' == result[5][0]

def test_load_separator():
    """test method."""

    # Arrange
    data = json.loads("""
        {
            "title" : "title",
            "typeCode" : 2,
            "children": [
                {
                  "title": "",
                  "type": "text/x-moz-place-separator",
                  "typeCode": 3
                } ]
         }""")

    # Act
    items = import_firefox_json(data)

    # Assert
    result = []
    for item in items:
        result.append(item)

    assert 0 == len(result)

def test_load_multiple_tags():
    """test method."""
    # Arrange
    data = json.loads("""
        {
            "title" : "title",
            "children": [
                {
                    "title" : "title1",
                    "uri" : "http://uri1",
                    "tags" : "tag1, tag2",
                    "typeCode": 1,
                    "annos" : [{
                         "name": "bookmarkProperties/description",
                         "value": "desc"
                     }]
                }]
        }""")

    # Act
    items = import_firefox_json(data)

    # Assert
    result = []
    for item in items:
        result.append(item)

    assert 1 == len(result)
    assert ",tag1,tag2," == result[0][2]
