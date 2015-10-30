This is a map generator for [CaaC](http://cityasacampus.org/). See the current
published version of the map [here](http://cityasacampus.org/map/)

Command-line usage:

```bash
(env) $ ./genmap.py output/topics.json output/map.svg -W 2048 -H 2048
```

Web server usage:

```bash
(env) $ ./server.py &
[...]
(env) $ curl -X POST http://localhost:5000/v1 -d'@output/topics.json' -H'Content-Type: application/json' > output/map.svg
```
