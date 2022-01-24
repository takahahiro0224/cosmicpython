from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

"""
https://www.cosmicpython.com/book/chapter_01_domain_model.html

在庫管理アプリ

- 在庫を発注する時に注文表を作成する
- バッチに注文表を割り当てると割り当て可能な在庫がその分減る
- 同じバッチに再度注文票を割り当てることができない
- 倉庫の在庫を出荷中の在庫より優先的に割り当てる
- 出荷中であればETAの早い順に割り当てる


OrderLine（注文票）
    orderid: 注文id
    sku: 商品コード
    qty: 量

Batch（在庫のバッチ）
    ref: 一意のid（出荷中・倉庫にあるなどの情報が入っている）
    sku: 商品コード
    qty: 量
    eta: 到着予定日（出荷中であれば）
"""


class OutOfStock(Exception):
    pass


# domain service
def allocate(line: OrderLine, batches: List[Batch]) -> str:
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
        batch.allocate(line)
        return batch.reference
    except StopIteration:
        raise OutOfStock(f"Out of stock for sku")


# value objects
# For value objects, the hash should be based on all the value attributes,
# and we should ensure that the objects are immutable. We get this for free by specifying @frozen=True on the dataclass.
@dataclass(frozen=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int


# entitiy objects
class Batch:
    def __init__(self, ref: str, sku: str, qty: int, eta: Optional[date]) -> None:
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations = set()

    def allocate(self, line: OrderLine) -> None:
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine) -> None:
        if line in self._allocations:
            self._allocations.remove(line)

    @property
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.qty

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __hash__(self):
        return hash(self.reference)

    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta
