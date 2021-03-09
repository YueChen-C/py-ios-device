"""
@Date    : 2021-03-09
@Author  : liyachao
"""
import socket
import time

from zeroconf import ServiceInfo, _TYPE_A, _TYPE_AAAA, DNSAddress, _TYPE_SRV, DNSService, _CLASS_IN, \
    _TYPE_TXT, DNSText, Zeroconf, DNSQuestion, _TYPE_ANY, DNSOutgoing, _FLAGS_QR_QUERY, _LISTENER_TIME


def current_time_millis() -> float:
    """Current system time in milliseconds"""
    return time.time() * 1000


class MyServiceInfo(ServiceInfo):
    def __init__(self, type_: str, name: str):
        super().__init__(type_, name)

    def update_record(self, zc: 'Zeroconf', now: float, record) -> None:
        """Updates service information from a DNS record"""
        if record is not None and not record.is_expired(now):
            if record.type in [_TYPE_A, _TYPE_AAAA]:
                assert isinstance(record, DNSAddress)
                # if record.name == self.name:
                if record.name == self.server:
                    try:
                        _addr: str = list(map(socket.inet_ntoa, [record.address]))[0]
                    except OSError:
                        return
                    if not _addr.startswith("169") and record.address not in self._addresses:
                        self._addresses.append(record.address)
            elif record.type == _TYPE_SRV:
                assert isinstance(record, DNSService)
                if record.name == self.name:
                    self.server = record.server
                    self.port = record.port
                    self.weight = record.weight
                    self.priority = record.priority
                    # self.address = None
                    self.update_record(zc, now, zc.cache.get_by_details(self.server, _TYPE_A, _CLASS_IN))
                    self.update_record(zc, now, zc.cache.get_by_details(self.server, _TYPE_AAAA, _CLASS_IN))
            elif record.type == _TYPE_TXT:
                assert isinstance(record, DNSText)
                if record.name == self.name:
                    self._set_text(record.text)

    def local_update_record(self, zc: 'Zeroconf', now: float, record) -> None:
        """Updates service information from a DNS record"""
        if record is not None and not record.is_expired(now):
            if record.type in [_TYPE_A, _TYPE_AAAA]:
                assert isinstance(record, DNSAddress)
                # if record.name == self.name:
                if record.name == self.server:
                    if record.address not in self._addresses:
                        self._addresses.append(record.address)
            elif record.type == _TYPE_SRV:
                assert isinstance(record, DNSService)
                if record.name == self.name:
                    self.server = record.server
                    self.port = record.port
                    self.weight = record.weight
                    self.priority = record.priority
                    # self.address = None
                    self.local_update_record(zc, now, zc.cache.get_by_details(self.server, _TYPE_A, _CLASS_IN))
                    self.local_update_record(zc, now, zc.cache.get_by_details(self.server, _TYPE_AAAA, _CLASS_IN))
            elif record.type == _TYPE_TXT:
                assert isinstance(record, DNSText)
                if record.name == self.name:
                    self._set_text(record.text)

    def request(self, zc: 'Zeroconf', timeout: float, local=False) -> bool:
        """Returns true if the service could be discovered on the
        network, and updates this object with details discovered.
        """
        now = current_time_millis()
        delay = _LISTENER_TIME
        next_ = now
        last = now + timeout

        record_types_for_check_cache = [(_TYPE_SRV, _CLASS_IN), (_TYPE_TXT, _CLASS_IN)]
        if self.server is not None:
            record_types_for_check_cache.append((_TYPE_A, _CLASS_IN))
            record_types_for_check_cache.append((_TYPE_AAAA, _CLASS_IN))
        for record_type in record_types_for_check_cache:
            cached = zc.cache.get_by_details(self.name, *record_type)
            if cached:
                if local:
                    self.local_update_record(zc, now, cached)
                else:
                    self.update_record(zc, now, cached)

        if self.server is not None and self.text is not None and self._addresses:
            return True

        try:
            zc.add_listener(self, DNSQuestion(self.name, _TYPE_ANY, _CLASS_IN))
            while self.server is None or self.text is None or not self._addresses:
                if last <= now:
                    return False
                if next_ <= now:
                    out = DNSOutgoing(_FLAGS_QR_QUERY)
                    cached_entry = zc.cache.get_by_details(self.name, _TYPE_SRV, _CLASS_IN)
                    if not cached_entry:
                        out.add_question(DNSQuestion(self.name, _TYPE_SRV, _CLASS_IN))
                        out.add_answer_at_time(cached_entry, now)
                    cached_entry = zc.cache.get_by_details(self.name, _TYPE_TXT, _CLASS_IN)
                    if not cached_entry:
                        out.add_question(DNSQuestion(self.name, _TYPE_TXT, _CLASS_IN))
                        out.add_answer_at_time(cached_entry, now)

                    if self.server is not None:
                        cached_entry = zc.cache.get_by_details(self.server, _TYPE_A, _CLASS_IN)
                        if not cached_entry:
                            out.add_question(DNSQuestion(self.server, _TYPE_A, _CLASS_IN))
                            out.add_answer_at_time(cached_entry, now)
                        cached_entry = zc.cache.get_by_details(self.name, _TYPE_AAAA, _CLASS_IN)
                        if not cached_entry:
                            out.add_question(DNSQuestion(self.server, _TYPE_AAAA, _CLASS_IN))
                            out.add_answer_at_time(cached_entry, now)
                    zc.send(out)
                    next_ = now + delay
                    delay *= 2

                zc.wait(min(next_, last) - now)
                now = current_time_millis()
        finally:
            zc.remove_listener(self)

        return True
