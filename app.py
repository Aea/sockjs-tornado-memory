"""
    sockjs-tornado benchmarking server. Works as a simple chat server
    without HTML frontend and listens on port 8080 by default.
"""
import os
import json
import sys
import resource
import datetime

from tornado import web, ioloop

from sockjs.tornado import SockJSRouter, SockJSConnection


class EchoConnection(SockJSConnection):
    """Echo connection implementation"""
    clients = set()
    total = 0

    def on_open(self, info):
        # When new client comes in, will add it to the clients list
        self.clients.add(self)
        EchoConnection.total += 1

    def on_message(self, msg):
        # For every incoming message, broadcast it to all clients
        self.broadcast(self.clients, msg)

    def on_close(self):
        # If client disconnects, remove him from the clients list
        self.clients.remove(self)

    @classmethod
    def dump_stats(cls, path):
        fp = open(path, "a")
        json.dump({"clients": len(cls.clients), "total": cls.total, 
            "memory": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / float(1024**2),
            "datetime": datetime.datetime.now().isoformat()}, fp)
        fp.write("\n")
        fp.close()

if __name__ == '__main__':
    options = dict()

    if len(sys.argv) > 1:
        options['immediate_flush'] = False

    # 1. Create SockJSRouter
    EchoRouter = SockJSRouter(EchoConnection, '/broadcast', options)

    # 2. Create Tornado web.Application
    app = web.Application(EchoRouter.urls)

    # 3. Make application listen on port 8080
    app.listen(8080)
    
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "result")
    if not os.path.exists(path):
        os.mkdir(path)
    
    path = os.path.join(path, datetime.datetime.now().isoformat())
    
    # 4. Every 1 second dump current client count
    ioloop.PeriodicCallback(lambda: EchoConnection.dump_stats(path), 1000).start()

    # 5. Start IOLoop
    ioloop.IOLoop.instance().start()