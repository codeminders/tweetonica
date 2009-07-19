from google.appengine.api import memcache

LOCK_NAMESPACE='LCK'

class MCLock:
    """ Memcache-based simple atomic locking service.
    It is using the fact that memcache add/delete operations
    are atomic. Locks are not re-enterant (you could not obtain
    it several times). Also it is possible to unlock a lock
    which have not been set by you, so use with caution!
    """

    def __init__(self, name, timeout=0, namespace=LOCK_NAMESPACE):
        """ Construct new lock.
        Args
        name - lock name
        timeot - expiration timeout. 0 means do not expire
        namespace - optinal lock namespace. 
        """
        self.name = name
        self.timeout = timeout
        self.namespace = namespace

    def lock(self):
        """ Attempts to obtain lock.

        Returns:
        True - if lock have been obtained, False otherwise
        (meaning somebody else already holding this lock)
        """
        return memcache.add(self.name,
                            "",
                            time=self.timeout,
                            namespace=self.namespace)

    def unlock(self):
        """ Attempts to release lock.

        Returns:

        The return value is 0 on network failure,
        1 if you try to release lock which have not been previously obtained,
        and 2 if the lock have been successfuly released.
        This can be used as a boolean value, where a network failure
        is the only bad condition.
        """
        return memcache.delete(self.name,
                               namespace=self.namespace)
