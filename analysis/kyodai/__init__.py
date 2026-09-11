"""京大工 情報学科 受験分析の共有モジュール。

設計方針
--------
* 標準ライブラリのみ（numpy/scipy 不要）。`python3` があれば動く。
* 旧版にあった ``exec(open('other.py').read().split(...))`` 方式は廃止した。
  文字列分割による再利用は、片方を編集した瞬間に静かに壊れるため。
* 乱数を使う手続きは必ず seed を引数に取り、既定値を固定する。
"""
from . import stats, datasets, irt  # noqa: F401

__all__ = ["stats", "datasets", "irt"]
