from kthread import KThread
from time import time, sleep

class ThreadedDataManager:
    def __init__(self, thread_amount=8):
        self.a = thread_amount
        self.td = [(None, None, None)]*thread_amount
        #      (data, thrd, time)
        self.data = list()
        self.dp = lambda d: None
        self.kc = lambda d, s: False
        self.os = lambda d: None

    def setDataProcess(self, func):
        self.dp = func

    def setKillingCondition(self, func):
        self.kc = func

    def setTimeout(self, tp):
        k = lambda d, s: False if (time() - s) < tp else True
        self.setKillingCondition(k)

    def setOnSuccess(self, func):
        self.os = func

    def append(self, d):
        self.data.append(d)
    
    def setData(self, data):
        self.data = data

    def start(self):
        total = len(self.data)
        all_thread_finished = True
        while self.data or not all_thread_finished:
            print('[{0}/{1}]'.format(total-len(self.data), total))
            all_thread_finished = True
            for i in range(self.a):
                d, t, s = self.td[i]
                if t and t.isAlive():
                    if self.kc(d, s):
                        t.terminate(); print('thread killed!!!')
                        self.data.append(d)
                    else:
                        all_thread_finished = False
                        continue
                elif t:
                    t.join()
                    self.os(d)
                if not self.data: continue # else new thread
                nd = self.data.pop(0)
                nt = KThread(target=self.dp, args=(nd,))
                ns = time()
                self.td[i] = (nd, nt, ns)
                nt.start()
            sleep(2)
