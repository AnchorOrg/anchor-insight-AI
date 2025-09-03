<!-- delz : delete this file when merging to the main. -->

- [ ] ENVIRONMENT -> APP_ENV
- [ ] the /home/u24/u24_dev/u24-anchor-reference/anchor-insight-AI/docs/anchor-insight-AI.hoppscotch.json . need to know how to use this file. 
- [ ] Need to come up with a way that I can quickly build the docker file.

- [ ]  fix the below error 
```log
  ⎿  ========================================                                                                                                                         
      Anchor Insight AI - Docker Setup
     ========================================
     … +51 lines (ctrl+r to expand)
  ⎿ time="2025-08-29T22:28:46+09:00" level=warning msg="/home/u24/u24_dev/u24-anchor-reference/anchor-insight-AI/src/docker-compose.yml: the attribute `version` is ob
    solete, it will be ignored, please remove it to avoid potential confusion"
```


- [ ] remove those wrong onboarding guide 
example
```shell
(anchor-insight-AI) u24@Lysander:~/u24_dev/u24-anchor-reference/anchor-insight-AI$ python src/app/main.py # this doesn't start the application at all. 
Traceback (most recent call last):
  File "/home/u24/u24_dev/u24-anchor-reference/anchor-insight-AI/src/app/main.py", line 20, in <module>
    from src.config.settings import get_settings
ModuleNotFoundError: No module named 'src'
(anchor-insight-AI) u24@Lysander:~/u24_dev/u24-anchor-reference/anchor-insight-AI$ python ./src/app/main.py 
Traceback (most recent call last):
  File "/home/u24/u24_dev/u24-anchor-reference/anchor-insight-AI/./src/app/main.py", line 20, in <module>
    from src.config.settings import get_settings
ModuleNotFoundError: No module named 'src'
```