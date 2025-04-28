# Tutorial for Developer

## get buku database

```python
>>> import buku
>>> bdb = buku.BukuDb()
```

## simplest way to add url to buku

```python
>>> rec_id = bdb.add_rec('http://example.com')
>>> rec_id
40296
```

## get record id from url

```python
>>> url = 'https://example.com'
>>> rec_id = bdb.add_rec(url)
... if rec_id == -1:
...     rec_id = bdb.get_rec_id(url)
>>> rec_id
40296
```

## get url data from record id

```python
>>> rec = bdb.get_rec_by_id(40296)
>>> rec
(40296, 'http://example.com', 'Example Domain', ',', '', 0)
```

## get tag list

```python
rec[3].split(buku.delim)
```
