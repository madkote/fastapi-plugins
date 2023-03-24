# Changes
## 0.12.0 (2023-03-24)
- `[feature]` `Annotated` support
## 0.11.0 (2022-09-19)
- `[feature]` `redis-py` replaces `aioredis`
## 0.10.0 (2022-07-07)
- `[feature]` Update `aioredis` to `2.x.x`
- `[feature]` Add `fakeredis` optionally for development purpose
## 0.9.1 (2022-06-16)
- `[fix]` Fix empty router prefix for control plugin
## 0.9.0 (2021-09-27)
- `[feature]` Logging plugin
- `[feature]` Middleware interface - register middleware at application
## 0.8.2 (2021-09-23)
- `[fix]` Fix dependency for aioredis
## 0.8.1 (2021-03-31)
- `[fix]` Fix settings for Python 3.7
## 0.8.0 (2021-03-31)
- `[feature]` Settings plugin
## 0.7.0 (2021-03-29)
- `[feature]` Control plugin with Health, Heartbeat, Environment and Version
## 0.6.1 (2021-03-24)
- `[fix]` Bump `aiojobs`to get rid of not required dependencies
## 0.6.0 (2020-11-26)
- `[feature]` Memcached
## 0.5.0 (2020-11-25)
- [bug] remove `__all__` since no API as such ([#6][i6]).
- [typo] Fix typos in README ([#7][i7]).
- [feature] Add Redis TTL ([#8][i8]).
## 0.4.2 (2020-11-24)
- [bug] Fix Redis URL ([#4][i4]). 
## 0.4.1 (2020-06-16)
- Refactor requirements
## 0.4.0 (2020-04-09)
- structure and split dependencies to `extra`
## 0.3.0 (2020-04-07)
- Scheduler: tasks scheduler based on `aiojobs`
## 0.2.1 (2020-04-06)
- Redis: pre-start
## 0.2.0 (2019-12-11)
- Redis: sentinels
## 0.1.0 (2019-11-20)
- Initial release: simple redis pool client

[i4]: https://github.com/madkote/fastapi-plugins/pull/4
[i6]: https://github.com/madkote/fastapi-plugins/pull/6
[i7]: https://github.com/madkote/fastapi-plugins/pull/7
[i8]: https://github.com/madkote/fastapi-plugins/issues/8
