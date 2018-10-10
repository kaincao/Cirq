from typing import Tuple, List, TypeVar, Generic, Iterable, Iterator, Any

TItem = TypeVar('TItem')


class BucketPriorityQueue(Generic[TItem]):
    """A priority queue for when priorities are integers over a small range.

    Items are dequeued in ascending priority order. Items with the same priority
    are dequeued in FIFO order.

    Works by having an explicit list for each priority (from the current min
    priority to the current max priority). Enqueued items are placed into the
    list corresponding to their bucket (after adding more buckets if necessary).
    Dequeued items come from the lowest list containing items, and result in
    empty buckets at the bottom end of the range being removed.

    Let P be the length of the priority range, and N be the number of items that
    are enqueued and dequeued. If the priority of items being enqueued is never
    smaller than the priority of previously dequeued items (the "monotonic use
    case"), then the worst case runtime complexity is O(N+P). In more general
    use the worst case runtime complexity is O(N*P).
    """

    def __init__(self,
                 items: Iterable[Tuple[int, TItem]] = (),
                 *,
                 drop_duplicates: bool=False):
        """Initializes a new priority queue."""
        self._buckets = []  # type: List[List[TItem]]
        self._offset = 0
        self._len = 0
        self._drop_set = set() if drop_duplicates else None

        for p, e in items:
            self.enqueue(p, e)

    @property
    def drop_duplicates(self) -> bool:
        return self._drop_set is not None

    def __bool__(self) -> bool:
        """Returns whether or not the priority queue contains any items."""
        return bool(self._len)

    def __len__(self) -> int:
        """Returns how many items are in the priority queue."""
        return self._len

    def __iter__(self) -> Iterator[Tuple[int, TItem]]:
        for i, bucket in enumerate(self._buckets):
            for item in bucket:
                yield i + self._offset, item

    def enqueue(self, priority: int, item: TItem) -> bool:
        """Adds an item to the priority queue.

        Args:
            priority: The priority of the item. Lower priorities dequeue before
                higher priorities.
            item: The item associated with the given priority.

        Returns:
            True if the item was enqueued. False if drop_duplicates is
            set and the item is already in the queue.
        """
        if self.drop_duplicates:
            if (priority, item) in self._drop_set:
                return False
            self._drop_set.add((priority, item))

        # First enqueue initializes self._offset.
        if not self._buckets:
            self._buckets.append([item])
            self._offset = priority
            self._len = 1
            return True

        # Where is the bucket this item is supposed to go into?
        i = priority - self._offset

        # Extend bucket list backwards if needed.
        if i < 0:
            self._buckets[:0] = [[] for _ in range(-i)]
            self._offset = priority
            i = 0

        # Extend bucket list forwards if needed.
        while i >= len(self._buckets):
            self._buckets.append([])

        # Finish by adding item to the intended bucket's list.
        self._buckets[i].append(item)
        self._len += 1
        return True

    def dequeue(self) -> Tuple[int, TItem]:
        """Removes and returns an item from the priority queue.

        Returns:
            A tuple whose first element is the priority of the dequeued item
            and whose second element is the dequeued item.

        Raises:
            ValueError:
                The queue is empty.
        """
        if self._len == 0:
            raise ValueError('BucketPriorityQueue is empty.')

        # Drop empty buckets at the front of the queue.
        while self._buckets and not self._buckets[0]:
            self._buckets.pop(0)
            self._offset += 1

        # Pull item out of the front bucket.
        item = self._buckets[0].pop(0)
        priority = self._offset
        self._len -= 1
        if self.drop_duplicates:
            self._drop_set.remove((priority, item))

        # Note: do not eagerly clear out empty buckets after pulling the item!
        # Doing so increases the worst case complexity of "monotonic" use from
        # O(N+P) to O(N*P).

        return priority, item

    def __str__(self):
        lines = [
            '{}: {},'.format(p, e)
            for p, e in self
        ]
        return 'BucketPriorityQueue {' + _indent(lines) + '\n}'

    def __repr__(self):
        return '{!r}(items={!r}, drop_duplicates={!r})'.format(
            type(self),
            list(self),
            self._drop_set is not None)

    __hash__ = None

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return (self.drop_duplicates == other.drop_duplicates and
                list(self) == list(other))

    def __ne__(self, other):
        return not self == other


def _indent(lines: List[Any]) -> str:
    paragraph = ''.join('\n' + str(line) for line in lines)
    return paragraph.replace('\n', '\n    ')