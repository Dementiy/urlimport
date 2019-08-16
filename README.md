# urlimport
Loading python modules and packages from a remote machine. Inspired by [httpimport](https://github.com/operatorequals/httpimport).

# Usage

```python
with github_repo('kragniz', 'json-sempai'):
    from jsonsempai import magic
    import tester
    print(tester.hello)
```
