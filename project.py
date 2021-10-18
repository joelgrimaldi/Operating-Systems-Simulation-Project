import sys
import math
import time
from copy import deepcopy
from queue import PriorityQueue



# code taken from:
# https://stackoverflow.com/questions/7287014/is-there-any-drand48-equivalent-in-python-or-a-wrapper-to-it
# to simulate c drand() in python
class Rand48(object):
    def __init__(self, seed):
        self.n = seed

    def seed(self, seed):
        self.n = seed

    def srand(self, seed):
        self.n = (int(seed) << 16) + 0x330e

    def next(self):
        self.n = (25214903917 * self.n + 11) & (2 ** 48 - 1)
        return self.n

    def drand(self):
        return self.next() / 2 ** 48

    # def lrand(self):
    #     return self.next() >> 17

    # def mrand(self):
    #     n = self.next() >> 16
    #     if n & (1 << 31):
    #         n -= 1 << 32
    #     return n


class Process(object):
    def __init__(self, name, arrival, burst, io):
        self.name = name                            # name of process
        self.arrival = arrival                      # arrival time
        self.burst = burst                          # burst time
        self.io = io                                # 
        self.burst_rem = deepcopy(burst)            # burst time remaining
        self.io_rem = deepcopy(io)                  # io remaining
        self.est_burst = 0                          # estimated burst time
        self.wait = []                              
        self.turnaround = []
        self.i = 0
        self.context_switch = 0
        self.preempt_ = 0
        self.cpu_start = -1
        self.cpu_end = -1
        self.status = "None"

    def get_est_burst(self):
        return self.est_burst

    def get_arrival(self):
        return self.arrival

    def set_est_burst(self, x):
        self.est_burst = x

    def get_name(self):
        return self.name

    def get_status(self):
        return self.status

    def get_ind(self):
        return self.i

    def get_preempt(self):
        return self.preempt_

    def get_burst_times(self, remaining):
        if remaining:
            return self.burst_rem
        else:
            return self.burst
    
    # def set_burst_time(self, index, time):
    #     self.burst[index] = time-self.burst[index]

    def get_io_times(self, remaining):
        if remaining:
            return self.io_rem
        else:
            return self.io

    def get_context_switch(self):
        return self.context_switch

    def add_context_switch(self, num):
        self.context_switch += num

    def get_wait(self):
        return self.wait

    def get_turn_around(self):
        return self.turnaround

    def arrive(self):
        if self.status == "None":
            self.status = "Ready"
            self.wait.append((self.arrival, 0))
        else:
            print("Status error! (status should be = 'none')")
            exit(1)

    def run(self, start):
        if self.status == "Context Switch Start":
            self.status = "Run"
            self.cpu_start = start
        else:
            print(self.name)
            print(self.status)
            print("Status error! (status should be = 'Context Switch Start')")
            exit(1)
        return self.burst_rem[self.i]

    def finish(self, end):
        if self.status == "Context Switch End":
            self.status = "IO"
            if self.i == len(self.burst) - 1:
                self.status = "Done"
            tmp = self.turnaround[-1][0]
            self.turnaround[-1] = (end - tmp, 1)
        else:
            print("Status error! (status should be = 'Context Switch End')")
            exit(1)

    def IO(self, end):
        if self.status == "IO":
            self.status = "Ready"
            self.i += 1
            self.wait.append((end, 0))
        else:
            print("Status error! (status should be = 'IO')")
            exit(1)

    def preempt(self, start, addPreempt = 1):
        if self.status == "Context Switch End":
            self.status = "Ready"
            self.wait.append((start, 0))
            if addPreempt:
                self.preempt_ += 1
        else:
            print(self.name)
            print(self.status)
            print("Status error! (status should be = 'Context Switch End')")
            exit(1)

    def context_switch_start(self, start):
        if self.status == "Ready":
            self.status = "Context Switch Start"
            self.turnaround.append((start, 0))
            tmp = self.wait[-1][0]
            self.wait[-1] = (start - tmp, 1)
        else:
            print(self.name)
            print(self.status)
            print("Status error! (status should be = 'ready')")
            exit(1)

    def context_switch_end(self, end):
        if self.status == "Run":
            self.status = "Context Switch End"
            self.burst_rem[self.i] -= end - self.cpu_start
            self.cpu_end = end
        else:
            print(self.name)
            print(self.status)
            print("Status error! (status should be = 'run')")
            exit(1)


class Scheduling(object):
    def __init__(self, all_proc, cs, tslice, alpha, lam):
        self.proc_SJF = all_proc[0]
        self.proc_FCFS = all_proc[1]
        self.proc_SRT = all_proc[2]
        self.proc_RR = all_proc[3]
        self.cs = cs
        self.tslice = tslice
        self.alpha = alpha
        self.lam = lam
        self.t = [0, 0, 0, 0]  # 0 for FCFS, 1 for SJF, 2 for SRT, 3 for RR


    def FCFS(self):
        tau = int(1/self.lam)
        proc_names = dict()
        proc_ = []
        events = []

        for p in self.proc_FCFS:
            p.set_est_burst(tau)
            proc_names[p.get_name()] = p
            proc_.append(p.get_name())
            events.append([p.get_arrival(), 0, p.get_name()])
            if len(p.get_burst_times(0)) != 1:
                print("Process {} (arrival time {} ms) {} CPU bursts (tau {:.0f}ms)".format(
                    p.get_name(), p.get_arrival(), len(p.get_burst_times(0)), tau
                ))
            else:
                print("Process {} (arrival time {} ms) {} CPU burst (tau {:.0f}ms)".format(
                    p.get_name(), p.get_arrival(), len(p.get_burst_times(0)), tau
                ))
        print("\ntime 0ms: Simulator started for FCFS [Q empty]")

        running = 'None'
        vacant = -1
        ready = []

        # events will hold events to be executed
        #  each list in event holds:
        #  [time process starts, function to be executed, name of process]

        # function of process
        #  0: process arriving, added to ready queue
        #  1: process switching out of CPU for I/O
        #  2: process completed I/O, added back to ready queue
        #  3: process executing CPU burst
        #  4: process completed CPU burst

        # note:
        #  the final CPU burst calls for the termination of the process

        while len(proc_) > 0:

            # Since the CPU is not running anything at this state
            #  grab the process with the lowest starting time

            events = sorted(events, key = lambda element: (element[0], element[1]*-1,element[2]))
            next_ = events.pop(0)
            self.t[0] = next_[0]
            pro = proc_names[next_[2]]
            
            # if the process is arriving
            if next_[1] == 0:
                ready.append([pro.get_est_burst(), pro.get_name()])
                pro.arrive()

                # print status
                self.print_(pro, ready, 0, 0)

                if self.t[0] > vacant or running == 'None':
                    running = pro.get_name()
                    pro.context_switch_start(self.t[0])
                    events.append((self.t[0] + self.cs, 3, pro.get_name()))
                    ready.pop(0)

            # if the process is executing a CPU burst
            elif next_[1] == 3:
                pro.run(self.t[0])
                ind = pro.get_burst_times(1)[pro.get_ind()]
                vacant = self.t[0] + self.cs + ind
                events.append((self.t[0] + ind, 4, pro.get_name()))

                # print status
                self.print_(pro, ready, 1, 0)

            # if the process completed a CPU burst
            elif next_[1] == 4:
                pro.context_switch_end(self.t[0])
                events.append((self.t[0] + self.cs, 1, pro.get_name()))

                self.print_(pro, ready, 2, 0)

                val = pro.get_burst_times(0)[pro.get_ind()]
                tau_tmp = math.ceil(self.alpha * val + (1 - self.alpha) * pro.get_est_burst())
                pro.set_est_burst(tau_tmp)
                pro.add_context_switch(1)

                self.print_(pro, ready, 20, 0)

            # if the process is being blocked by I/O
            elif next_[1] == 1:
                pro.finish(self.t[0])
                running = 'None'

                if len(ready) > 0:
                    new_ = proc_names[ready.pop(0)[1]]
                    new_.context_switch_start(next_[0])
                    running = new_.get_name()
                    events.append([self.t[0] + self.cs, 3, new_.get_name()])

                if pro.get_ind() >= len(pro.get_io_times(0)):
                    proc_.remove(pro.get_name())
                    continue

                exp = pro.get_io_times(0)[pro.get_ind()]
                events.append([self.t[0] + exp, 2, pro.get_name()])

            # if the process completes I/O
            elif next_[1] == 2:
                pro.IO(self.t[0])
                ready.append([pro.get_est_burst(), pro.get_name()])

                self.print_(pro, ready, 4, 0)

                if running == 'None' and self.t[0] >= vacant and len(ready) == 1:
                    ready.pop(0)
                    running = pro.get_name()
                    pro.context_switch_start(self.t[0])
                    events.append((self.t[0] + self.cs, 3, pro.get_name()))

        print("time {}ms: Simulator ended for FCFS [Q empty]".format(self.t[0]))
        return
    

    def SJF(self):
        tau = int(1/self.lam)
        proc_names = dict()
        proc_ = []
        events = []

        for p in self.proc_SJF:
            p.set_est_burst(tau)
            proc_names[p.get_name()] = p
            proc_.append(p.get_name())
            events.append([p.get_arrival(), 0, p.get_name()])
            
        print("\ntime 0ms: Simulator started for SJF [Q empty]")

        running = 'None'
        same_arrival_time = False
        vacant = -1
        ready = []

        # events will hold events to be executed
        #  each list in event holds:
        #  [time process starts, function to be executed, name of process]

        # function of process
        #  0: process arriving, added to ready queue
        #  1: process switching out of CPU for I/O
        #  2: process completed I/O, added back to ready queue
        #  3: process executing CPU burst
        #  4: process completed CPU burst

        # note:
        #  the final CPU burst calls for the termination of the process

        events = sorted(events, key = lambda element: (element[0], element[2]))

        while len(proc_) > 0:

            # if the cpu is not currently running anything
            # grab the job that arrives/arrived first
            
            if len(events) == 0 and same_arrival_time:
                ready.pop(0)
                running = pro.get_name()
                pro.context_switch_start(self.t[1])
                events.append((self.t[1] + self.cs, 3, pro.get_name()))
                same_arrival_time = False
            
            first_run = False
            events = sorted(events, key = lambda element: (element[0], element[1]*-1 ,element[2]))
            next_ = events.pop(0)
            self.t[1] = next_[0]
            pro = proc_names[next_[2]]

            # if process is arriving
            if next_[1] == 0:
                ready.append([pro.get_est_burst(), pro.get_name()])
                ready = sorted(ready, key=lambda element: (element[0], element[1]))
                pro.arrive()

                # PRINT SOMETHING
                self.print_tau(pro, ready, 0, 1)

                if self.t[1] > vacant or running == 'None':
                    running = pro.get_name()
                    pro.context_switch_start(self.t[1])
                    events.append((self.t[1] + self.cs, 3, pro.get_name()))
                    ready.pop(0)

            # if process is starting a CPU burst
            elif next_[1] == 3:
                pro.run(self.t[1])
                ind = pro.get_burst_times(1)[pro.get_ind()]
                vacant = self.t[1] + self.cs + ind
                events.append((self.t[1] + ind, 4, pro.get_name()))
                # PRINT SOMETHING
                self.print_tau(pro, ready, 1, 1)

            # if process completed a CPU burst
            elif next_[1] == 4:
                pro.context_switch_end(self.t[1])
                events.append((self.t[1] + self.cs, 1, pro.get_name()))

                self.print_tau(pro, ready, 2, 1)

                val = pro.get_burst_times(0)[pro.get_ind()]
                old_tau = pro.get_est_burst()
                tau_tmp = math.ceil(self.alpha * val + (1 - self.alpha) * pro.get_est_burst())
                pro.set_est_burst(tau_tmp)
                pro.add_context_switch(1)

                for r in ready:
                    if r[1] == pro.get_name():
                        r[0] = pro.get_est_burst()
                        break
                ready = sorted(ready, key=lambda element: (element[0], element[1]))

                self.print_tau(pro, ready, 20, 1, old_tau)

            # if process switching out of CPU for I/O Burst
            elif next_[1] == 1:
                pro.finish(self.t[1])
                running = 'None'

                if len(ready) > 0:
                    new_ = proc_names[ready.pop(0)[1]]
                    new_.context_switch_start(next_[0])
                    running = new_.get_name()
                    events.append([self.t[1] + self.cs, 3, new_.get_name()])

                if pro.get_ind() >= len(pro.get_io_times(0)):
                    proc_.remove(pro.get_name())
                    continue

                exp = pro.get_io_times(0)[pro.get_ind()]
                events.append([self.t[1] + exp, 2, pro.get_name()])

            # if process completes I/O burst, process
            #  is added to the ready queue after completion
            elif next_[1] == 2:
                pro.IO(self.t[1])
                ready.append([pro.get_est_burst(), pro.get_name()])
                ready = sorted(ready, key=lambda element: (element[0], element[1]))

                self.print_tau(pro, ready, 4, 1)

                if running == 'None' and self.t[1] >= vacant and len(ready) == 1:
                    if len(events) == 0 or self.t[1] != events[0][0]:
                        ready.pop(0)
                        running = pro.get_name()
                        pro.context_switch_start(self.t[1])
                        events.append((self.t[1] + self.cs, 3, pro.get_name()))
                    else:
                        same_arrival_time = True

        print("time {}ms: Simulator ended for SJF [Q empty]".format(self.t[1]))
        return


    def SRT(self):
        tau = int(1/self.lam)
        proc_names = dict()
        proc_ = []
        events = []

        for p in self.proc_SRT:
            p.set_est_burst(tau)
            proc_names[p.get_name()] = p
            proc_.append(p.get_name())
            events.append([p.get_arrival(), 0, p.get_name()])
            
        print("\ntime 0ms: Simulator started for SRT [Q empty]")

        running = 'None'
        same_arrival_time = False
        preempt = False
        vacant = -1
        ready = []

        # events will hold events to be executed
        #  each list in event holds:
        #  [time process starts, function to be executed, name of process]

        # function of process
        #  0: process arriving, added to ready queue
        #  1: process switching out of CPU for I/O
        #  2: process completed I/O, added back to ready queue
        #  3: process executing CPU burst
        #  4: process completed CPU burst

        # note:
        #  the final CPU burst calls for the termination of the process

        events = sorted(events, key = lambda element: (element[0], element[2]))

        while len(proc_) > 0:

            # if the cpu is not currently running anything
            # grab the job that arrives/arrived first
            
            if len(events) == 0 and same_arrival_time:
                ready.pop(0)
                running = pro.get_name()
                pro.context_switch_start(self.t[2])
                events.append((self.t[2] + self.cs, 3, pro.get_name()))
                same_arrival_time = False
            
            #first_run = False
            events = sorted(events, key = lambda element: (element[0], element[1]*-1 ,element[2]))
            ready = sorted(ready, key=lambda element: (element[0], element[1]))
            next_ = events.pop(0)
            self.t[2] = next_[0]
            pro = proc_names[next_[2]]
            #print("\t",next_)
            #print("\t\t",events)

            # if process is arriving
            if next_[1] == 0:
                ready.append([pro.get_est_burst(), pro.get_name()])
                ready = sorted(ready, key=lambda element: (element[0], element[1]))
                pro.arrive()

                # PRINT SOMETHING
                self.print_tau(pro, ready, 0, 2)

                if self.t[2] > vacant or running == 'None':
                    running = pro.get_name()
                    pro.context_switch_start(self.t[2])
                    events.append((self.t[2] + self.cs, 3, pro.get_name()))
                    ready.pop(0)

            # if process is starting a CPU burst
            elif next_[1] == 3:
                starting_burst_time = pro.get_burst_times(0)[pro.get_ind()]
                ending_burst_time = pro.get_burst_times(1)[pro.get_ind()]
                new_tau = pro.get_est_burst() - starting_burst_time + ending_burst_time

                #print(next_[0]+self.cs)
                #print(events[0][0],events[0][1])

                pro.run(self.t[2])
                ind = pro.get_burst_times(1)[pro.get_ind()]
                vacant = self.t[2] + self.cs + ind
                events.append((self.t[2] + ind, 4, pro.get_name()))
                # PRINT SOMETHING
                if(ind == pro.get_burst_times(0)[pro.get_ind()]):
                    self.print_tau(pro, ready, 1, 2)
                else:
                    self.print_tau(pro, ready, 6, 2)
                
                # starting_burst_time = pro.get_burst_times(0)[pro.get_ind()]
                # ending_burst_time = pro.get_burst_times(1)[pro.get_ind()]
                # new_tau = pro.get_est_burst() - starting_burst_time + ending_burst_time

                events = sorted(events, key = lambda element: (element[1]*-1, element[0] ,element[2]))

                if len(ready) > 0 and ready[0][0] < new_tau:
                    new_ = proc_names[ready[0][1]]
                    self.print_tau(new_, ready, 7, 2, 0, pro.get_name())
                    ready.pop(0)
                    running = new_.get_name()
                    new_.context_switch_start(self.t[2])
                    events.append((self.t[2] + self.cs*2, 3, new_.get_name()))
                    pro.context_switch_end(self.t[2])
                    pro.preempt(self.t[2])
                    ready.append([new_tau,pro.get_name()])
                    events.pop(0)

            # if process completed a CPU burst
            elif next_[1] == 4:
                pro.context_switch_end(self.t[2])
                events.append((self.t[2] + self.cs, 1, pro.get_name()))

                self.print_tau(pro, ready, 2, 2)

                val = pro.get_burst_times(0)[pro.get_ind()]
                old_tau = pro.get_est_burst()
                tau_tmp = math.ceil(self.alpha * val + (1 - self.alpha) * pro.get_est_burst())
                pro.set_est_burst(tau_tmp)
                pro.add_context_switch(1)

                for r in ready:
                    if r[1] == pro.get_name():
                        r[0] = pro.get_est_burst()
                        break
                ready = sorted(ready, key=lambda element: (element[0], element[1]))

                self.print_tau(pro, ready, 20, 2, old_tau)

            # if process switching out of CPU for I/O Burst
            elif next_[1] == 1:
                pro.finish(self.t[2])
                running = 'None'

                if len(ready) > 0:
                    new_ = proc_names[ready.pop(0)[1]]
                    new_.context_switch_start(next_[0])
                    running = new_.get_name()
                    events.append([self.t[2] + self.cs, 3, new_.get_name()])

                if pro.get_ind() >= len(pro.get_io_times(0)):
                    proc_.remove(pro.get_name())
                    continue

                exp = pro.get_io_times(0)[pro.get_ind()]
                events.append([self.t[2] + exp, 2, pro.get_name()])

            # if process completes I/O burst, process
            #  is added to the ready queue after completion
            elif next_[1] == 2:
                pro.IO(self.t[2])
                ready.append([pro.get_est_burst(), pro.get_name()])
                ready = sorted(ready, key=lambda element: (element[0], element[1]))


                events = sorted(events, key = lambda element: (element[1]*-1, element[0] ,element[2]))

                # preemption
                if len(events) > 0 and pro.get_est_burst() + self.t[2] < events[0][0] + proc_names[events[0][2]].get_est_burst() \
                - proc_names[events[0][2]].get_burst_times(0)[proc_names[events[0][2]].get_ind()] and events[0][1] == 4:
                    self.print_tau(pro, ready, 5, 2, 0, events[0][2])
                    ready.pop(0)
                    running = pro.get_name()
                    pro.context_switch_start(self.t[2])
                    pro.add_context_switch(1)
                    events.append((self.t[2] + self.cs*2, 3, pro.get_name()))
                    proc_names[events[0][2]].context_switch_end(self.t[2])
                    proc_names[events[0][2]].preempt(self.t[2])
                    starting_burst_time = proc_names[events[0][2]].get_burst_times(0)[proc_names[events[0][2]].get_ind()]
                    ending_burst_time = proc_names[events[0][2]].get_burst_times(1)[proc_names[events[0][2]].get_ind()]
                    new_tau = proc_names[events[0][2]].get_est_burst() - starting_burst_time + ending_burst_time
                    ready.append([new_tau,proc_names[events[0][2]].get_name()])
                    events.pop(0)
                else:
                    self.print_tau(pro, ready, 4, 2)
                

                if running == 'None' and self.t[2] >= vacant and len(ready) == 1:
                    if len(events) == 0 or self.t[2] != events[0][0]:
                        ready.pop(0)
                        running = pro.get_name()
                        pro.context_switch_start(self.t[2])
                        events.append((self.t[2] + self.cs, 3, pro.get_name()))
                    else:
                        same_arrival_time = True

                events = sorted(events, key = lambda element: (element[1]*-1, element[0] ,element[2]))


                starting_burst_time = proc_names[events[0][2]].get_burst_times(0)[proc_names[events[0][2]].get_ind()]
                ending_burst_time = proc_names[events[0][2]].get_burst_times(1)[proc_names[events[0][2]].get_ind()]
                new_tau = proc_names[events[0][2]].get_est_burst() - starting_burst_time + ending_burst_time

                if len(ready) > 0 and ready[0][0] < new_tau and next_[0] + self.cs == events[0][0] and events[0][1] == 3:
                    ready.pop(0)
                    running = pro.get_name()
                    pro.context_switch_start(self.t[2])
                    pro.add_context_switch(1)
                    events.append((self.t[2] + self.cs, 3, pro.get_name()))
                    proc_names[events[0][2]].run(self.t[2])
                    proc_names[events[0][2]].context_switch_end(self.t[2])
                    proc_names[events[0][2]].preempt(self.t[2], 0)
                    ready.append([new_tau,proc_names[events[0][2]].get_name()])
                    events.pop(0)



        print("time {}ms: Simulator ended for SRT [Q empty]".format(self.t[2]))
        return

    
    # def RR(self):
    #     tau = int(1 / self.lam)
    #     proc_names = dict()
    #     proc_ = []
    #     events = []

    #     for p in self.proc_FCFS:
    #         p.set_est_burst(tau)
    #         proc_names[p.get_name()] = p
    #         proc_.append(p.get_name())
    #         events.append([p.get_arrival(), 0, p.get_name()])

    #     print("\ntime 0ms: simulator started for RR [Q empty]")

    #     running = 'None'
    #     vacant = -1
    #     ready = []
    #     preempted = dict() #preempted[process_name] = [num processes before, num completed processes]
    #     preempt_self = False

    #     # events will hold events to be executed
    #     #  each list in event holds:
    #     #  [time process starts, function to be executed, name of process]

    #     # function of process
    #     #  0: process arriving, added to ready queue
    #     #  1: process switching out of CPU for I/O
    #     #  2: process completed I/O, added back to ready queue
    #     #  3: process executing CPU burst
    #     #  4: process completed CPU burst

    #     # note:
    #     #  the final CPU burst calls for the termination of the process

    #     while len(proc_) > 0:

    #         # Since the CPU is not running anything at this state
    #         #  grab the process with the lowest starting time

    #         events = sorted(events, key=lambda element: (element[0], element[1] * -1, element[2]))

    #         print(events)

    #         next_ = events.pop(0)
    #         self.t[3] = next_[0]
    #         pro = proc_names[next_[2]]

    #         # if the process is arriving
    #         if next_[1] == 0:
    #             ready.append([pro.get_est_burst(), pro.get_name()])
    #             pro.arrive()

    #             # print status
    #             self.print_(pro, ready, 0, 3)

    #             if self.t[3] > vacant or running == 'None':
    #                 running = pro.get_name()
    #                 pro.context_switch_start(1)
    #                 events.append((self.t[3] + self.cs, 3, pro.get_name()))
    #                 ready.pop(0)

    #         # if the process is executing a CPU burst
    #         elif next_[1] == 3:
    #             if not preempt_self and pro.get_status() == "Run":
    #                 # if ready[len(ready)-1] == pro.get_name(): #it was preempted
    #                 if len(events) > 0:
    #                     self.print_(pro, ready, 5, 3)
    #                     # pro.preempt(self.t[3])
    #                 else:
    #                     self.print_(pro, ready, 7, 3)
    #                     print(next_[0])
    #                     print(proc_names[next_[2]].get_burst_times(1)[proc_names[next_[2]].get_ind()])
    #                     events.append([next_[0]+proc_names[next_[2]].get_burst_times(1)[proc_names[next_[2]].get_ind()],4,next_[2]])
    #                     preempt_self = True
    #                     continue
    #                 for k in preempted.keys():
    #                     preempted[k][1] += 1 #or every time a process is preempted
    #                     if preempted[k][0] == preempted[k][1]:
    #                         proc_names[k].set_status
    #                         events.append([self.t[3] + self.tslice, 3, proc.get_name()])
    #                         preempted.pop(k)
    #                 preempted[proc.get_name] = [len(ready), 0]
    #                 # events.append([self.t[3], 3, pro.get_name()])
    #                 continue
    #                     #pro.context_switch_start(self.t[3])
    #                     #pro.preempt(self.t[3], 0)
    #                     #continue
    #             if not preempt_self:
    #                 pro.run(self.t[3])
    #             if (pro.get_preempt() > 0):
    #                 self.print_(pro, ready, 6, 3)
    #             else:
    #                 self.print_(pro, ready, 1, 3)
    #             ind = pro.get_burst_times(1)[pro.get_ind()] #remaining time
    #             vacant = self.t[3] + self.cs + ind

    #             print(ind)
    #             print(self.tslice)
    #             if not preempt_self and ind > self.tslice:
    #                 # pro.preempt(self.t[3])
    #                 events.append([self.t[3] + self.tslice, 3, pro.get_name()])
    #                 ready.append([pro.get_est_burst(), pro.get_name()])

    #             else:
    #                 events.append((self.t[3] + ind, 4, pro.get_name()))
    #             preempt_self = False
    #             # print status


    #         # if the process completed a CPU burst
    #         elif next_[1] == 4:
    #             pro.context_switch_end(1)
    #             events.append((self.t[3] + self.cs, 1, pro.get_name()))

    #             self.print_(pro, ready, 2, 3)

    #             val = pro.get_burst_times(0)[pro.get_ind()]
    #             tau_tmp = math.ceil(self.alpha * val + (1 - self.alpha) * pro.get_est_burst())
    #             pro.set_est_burst(tau_tmp)
    #             pro.add_context_switch(1)

    #             self.print_(pro, ready, 20, 3)

    #         # if the process is being blocked by I/O
    #         elif next_[1] == 1:
    #             pro.finish(self.t[3])
    #             running = 'None'

    #             if len(ready) > 0:
    #                 new_ = proc_names[ready.pop(0)[1]]
    #                 new_.context_switch_start(next_[0])
    #                 running = new_.get_name()
    #                 events.append([self.t[3] + self.cs, 3, new_.get_name()])

    #             if pro.get_ind() >= len(pro.get_io_times(0)):
    #                 proc_.remove(pro.get_name())
    #                 pro.preempt(self.t[3] - self.tslice)
    #                 for k in preempted.keys():
    #                     preempted[k][1] += 1  # or every time a process is preempted
    #                     if preempted[k][0] == preempted[k][1]:
    #                         events.append([self.t[3] + self.tslice, 3, proc.get_name()])
    #                         preempted.pop(k)
    #                 continue

    #             exp = pro.get_io_times(0)[pro.get_ind()]
    #             events.append([self.t[3] + exp, 2, pro.get_name()])

    #         # if the process completes I/O
    #         elif next_[1] == 2:
    #             pro.IO(self.t[3])
    #             ready.append([pro.get_est_burst(), pro.get_name()])

    #             self.print_(pro, ready, 4, 3)

    #             if running == 'None' and self.t[3] >= vacant and len(ready) == 1:
    #                 ready.pop(0)
    #                 running = pro.get_name()
    #                 pro.context_switch_start(self.t[3])
    #                 events.append((self.t[3] + self.cs, 3, pro.get_name()))

    #     print("time {}ms: Simulator ended for RR [Q empty]\n".format(self.t[3]))
    #     return




####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################




    def RR(self):
        tau = int(1 / self.lam)
        proc_names = dict()
        proc_ = []
        events = []

        for p in self.proc_RR:
            p.set_est_burst(tau)
            proc_names[p.get_name()] = p
            proc_.append(p.get_name())
            events.append([p.get_arrival(), 0, p.get_name()])

        print("\ntime 0ms: Simulator started for RR with time slice {}ms [Q empty]".format(self.tslice))

        running = 'None'
        vacant = -1
        ready = []
        preempted = dict() #preempted[process_name] = [num processes before, num completed processes]

        # events will hold events to be executed
        #  each list in event holds:
        #  [time process starts, function to be executed, name of process]

        # function of process
        #  0: process arriving, added to ready queue
        #  1: process switching out of CPU for I/O
        #  2: process completed I/O, added back to ready queue
        #  3: process executing CPU burst
        #  4: process completed CPU burst

        # note:
        #  the final CPU burst calls for the termination of the process

        while len(proc_) > 0:

            # Since the CPU is not running anything at this state
            #  grab the process with the lowest starting time

            events = sorted(events, key=lambda element: (element[0], element[1] * -1, element[2]))
            #print("events len: {}\n".format(len(events)))

            next_ = events.pop(0)

            self.t[3] = next_[0]
            pro = proc_names[next_[2]]

            # if the process is arriving
            if next_[1] == 0:
                # if (pro.get_preempt() == 0):
                ready.append([pro.get_est_burst(), pro.get_name()])
                pro.arrive()

                # print status
                # arrived; added to ready queue
                self.print_(pro, ready, 0, 3)
                #print("name: {}, t[3]: {}, vacant: {}, running: {}".format(pro.get_name(), self.t[3], vacant, running))

                if self.t[3] > vacant or running == 'None': #UPDATE VACANT
                    running = pro.get_name()
                    pro.context_switch_start(self.t[3])
                    events.append((self.t[3] + self.cs, 3, pro.get_name()))
                    r = ready.pop(0)
                #print("events after: {}".format(len(events)))


            # if the process is executing a CPU burst
            elif next_[1] == 3:
                ind = pro.get_burst_times(1)[pro.get_ind()]
                pro.run(self.t[3])

                if ind > self.tslice:
                    events.append((self.t[3] + self.tslice, 4, pro.get_name()))
                    preempted[pro.get_name()] = [len(ready), 0]
                    vacant = self.t[3] + self.tslice

                else: #remaining burst time <= time slice, regular
                    events.append((self.t[3] + ind, 4, pro.get_name()))
                    vacant = self.t[3] + self.cs + ind

                # print status
                # started using the CPU for ms burst
                self.print_(pro, ready, 1, 3)

            # if the process completed a CPU burst
            elif next_[1] == 4:
                #don't context switch if queue is empty
                pro.context_switch_end(self.t[3])
                ind = pro.get_burst_times(1)[pro.get_ind()]

                if ind > 0 and pro.get_name() in preempted.keys():
                    if len(events) > 0 and events[0][1] == 3:
                        pro.context_switch_end(self.t[3])
                        pro.context_switch_add(1)
                        pro.preempt(self.t[3])
                        self.print_(pro, ready, 5, 3)
                        ready.append([pro.get_est_burst(), pro.get_name()])
                        continue
                    if len(ready) > 0:
                        self.print_(pro, ready, 5, 3)
                        new = ready.pop(0)
                        events.append([self.t[3]+self.cs*2, 3, new[1]])
                        proc_names[new[1]].context_switch_start(self.t[3])
                        pro.preempt(self.t[3])
                        ready.append([pro.get_est_burst(), pro.get_name()])
                        continue
                    

                    rem_time = pro.get_burst_times(1)[pro.get_ind()]
                    pro.preempt(self.t[3],0)
                    pro.context_switch_start(self.t[3])
                    if rem_time > self.tslice:
                         events.append([next_[0], 3, pro.get_name()])
                         self.print_(pro,ready,7,3)
                         continue
                    pro.run(self.t[3])
                    events.append([next_[0]+rem_time, 4, pro.get_name()])
                    self.print_(pro, ready, 7, 3)

                    # if pro.get_name() in preempted.keys():
                    #     pro.preempt_(self.t[3])
                    #     self.print_(pro, ready, 5, 3)
                    #     ready.append([pro.get_est_burst(), pro.get_name()])
                    #     new_ = proc_names[ready.pop(0)[1]]
                    #     new_.context_switch_start(next_[0])
                    #     running = new_.get_name()
                    #     events.append([self.t[3] + self.cs, 3, new_.get_name()])

                else:
                    events.append((self.t[3] + self.cs, 1, pro.get_name()))
                    self.print_(pro, ready, 2, 3)


                    val = pro.get_burst_times(0)[pro.get_ind()]
                    tau_tmp = math.ceil(self.alpha * val + (1 - self.alpha) * pro.get_est_burst())
                    pro.set_est_burst(tau_tmp)
                    pro.add_context_switch(1)

                    self.print_(pro, ready, 20, 3)


            # if the process is being blocked by I/O
            elif next_[1] == 1:
                pro.finish(self.t[3])
                running = 'None'

                if len(ready) > 0:
                    new_ = proc_names[ready.pop(0)[1]]
                    new_.context_switch_start(next_[0])
                    running = new_.get_name()
                    events.append([self.t[3] + self.cs, 3, new_.get_name()])

                if pro.get_ind() >= len(pro.get_io_times(0)): #proc done
                    proc_.remove(pro.get_name())

                    # go through every preempted process (name)
                    # add to events if all processes before it have finished
                    continue

                exp = pro.get_io_times(0)[pro.get_ind()]
                events.append([self.t[3] + exp, 2, pro.get_name()])

            # if the process completes I/O
            elif next_[1] == 2:
                pro.IO(self.t[3])
                ready.append([pro.get_est_burst(), pro.get_name()])

                # process completed i/o
                self.print_(pro, ready, 4, 3)

                if running == 'None' and self.t[3] >= vacant and len(ready) == 1:
                    ready.pop(0)
                    running = pro.get_name()
                    pro.context_switch_start(self.t[3])
                    events.append((self.t[3] + self.cs, 3, pro.get_name()))

        print("time {}ms: Simulator ended for RR [Q empty]".format(self.t[3]))
        return




####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################




    
# used for printing out FCFS because tau values are not included
#  a feature could be added for RR printing, e.g. using an od == 5
#  for when a t_slice expires?

    def print_(self, pr, rdy, od, i):
        rem = len(pr.get_burst_times(0)) - pr.get_ind() - 1
        if len(rdy) == 0:
            rdy_str = "empty"
        else:
            rdy_str = "".join([k[1] for k in rdy])

        if self.t[i] > 1000:
            if od == 2:
                if rem == 0:
                    print("time {}ms: Process {} terminated [Q {}]".format(
                        self.t[i], pr.get_name(), rdy_str))
        else:
            if od == 0:
                print("time {}ms: Process {} arrived; added to ready queue [Q {}]".format(
                    self.t[i], pr.get_name(), rdy_str))
            if od == 1:
                ind = pr.get_burst_times(1)[pr.get_ind()]
                print("time {}ms: Process {} started using the CPU for {}ms burst [Q {}]".format(
                    self.t[i], pr.get_name(), ind, rdy_str))
            if od == 2:
                if rem > 1:
                    print("time {}ms: Process {} completed a CPU burst; {} bursts to go [Q {}]".format(
                        self.t[i], pr.get_name(), rem, rdy_str))
                elif rem == 1:
                    print("time {}ms: Process {} completed a CPU burst; 1 burst to go [Q {}]".format(
                        self.t[i], pr.get_name(), rdy_str))
                elif rem == 0:
                    print("time {}ms: Process {} terminated [Q {}]".format(
                        self.t[i], pr.get_name(), rdy_str))
            if od == 20:
                if pr.get_ind() < len(pr.get_burst_times(0)) - 1:
                    io_time = self.t[i] + self.cs + pr.get_io_times(0)[pr.get_ind()]
                    print("time {}ms: Process {} switching out of CPU; will block on I/O until time {}ms [Q {}]".format(
                        self.t[i], pr.get_name(), io_time, rdy_str))
            if od == 4:
                print("time {}ms: Process {} completed I/O; added to ready queue [Q {}]".format(
                    self.t[i], pr.get_name(), rdy_str))
            if od == 5:
                ind_o = pr.get_burst_times(1)[pr.get_ind()]
                ind = ind_o - (self.tslice * pr.get_preempt())

                print("time {}ms: Time slice expired; process {} preempted with {}ms to go [Q {}]".format(self.t[i], pr.get_name(), ind, rdy_str))

            if od == 6:
                print("time {}ms: Process {} started using the CPU for remaining {}ms of {}ms burst [Q {}]".format(self.t[i], pr.get_name(), ind, ind_o))
            if od == 7:
                print("time {}ms: Time slice expired; no preemption because ready queue is empty [Q empty]".format(self.t[i]))
        return


# used for printing with tau values will be modified
#  to add a preemption switch for SRT in od == 5

    def print_tau(self, pr, rdy, od, i, old_tau = 0, preempt = ""):
        rem = len(pr.get_burst_times(0)) - pr.get_ind() - 1

        if len(rdy) == 0:
            rdy_str = "empty"
        else:
            rdy_str = "".join([k[1] for k in rdy])

        if self.t[i] > 1000:
            if od == 2:
                if rem == 0:
                    print("time {}ms: Process {} terminated [Q {}]".format(
                        self.t[i], pr.get_name(), rdy_str))
        else:
            if od == 0:
                print("time {}ms: Process {} (tau {}ms) arrived; added to ready queue [Q {}]".format(
                    self.t[i], pr.get_name(), pr.get_est_burst(), rdy_str))
            if od == 1:
                ind = pr.get_burst_times(1)[pr.get_ind()]
                print("time {}ms: Process {} (tau {}ms) started using the CPU for {}ms burst [Q {}]".format(
                    self.t[i], pr.get_name(), pr.get_est_burst(), ind, rdy_str))
            if od == 2:
                if rem > 1:
                    print("time {}ms: Process {} (tau {}ms) completed a CPU burst; {} bursts to go [Q {}]".format(
                        self.t[i], pr.get_name(), pr.get_est_burst(), rem, rdy_str))
                elif rem == 1:
                    print("time {}ms: Process {} (tau {}ms) completed a CPU burst; 1 burst to go [Q {}]".format(
                        self.t[i], pr.get_name(), pr.get_est_burst(), rdy_str))
                elif rem == 0:
                    print("time {}ms: Process {} terminated [Q {}]".format(
                        self.t[i], pr.get_name(), rdy_str))
            if od == 20:
                if rem != 0:
                    print("time {}ms: Recalculated tau from {}ms to {}ms for process {} [Q {}]".format(
                        self.t[i], old_tau, pr.get_est_burst(), pr.get_name(), rdy_str))
                if pr.get_ind() < len(pr.get_burst_times(0)) - 1:
                    io_time = self.t[i] + self.cs + pr.get_io_times(0)[pr.get_ind()]
                    print("time {}ms: Process {} switching out of CPU; will block on I/O until time {}ms [Q {}]".format(
                        self.t[i], pr.get_name(), io_time, rdy_str))
            if od == 4:
                print("time {}ms: Process {} (tau {}ms) completed I/O; added to ready queue [Q {}]".format(
                    self.t[i], pr.get_name(), pr.get_est_burst(), rdy_str))
            if od == 5:
                print("time {}ms: Process {} (tau {}ms) completed I/O; preempting {} [Q {}]".format(
                    self.t[i],pr.get_name(), pr.get_est_burst(), preempt, rdy_str))
            if od == 6:
                rem_ind = pr.get_burst_times(1)[pr.get_ind()]
                ind = pr.get_burst_times(0)[pr.get_ind()]
                print("time {}ms: Process {} (tau {}ms) started using the CPU for remaining {}ms of {}ms burst [Q {}]".format(
                    self.t[i], pr.get_name(), pr.get_est_burst(), rem_ind, ind, rdy_str))
            if od == 7:
                print("time {}ms: Process {} (tau {}ms) will preempt {} [Q {}]".format(
                    self.t[i],pr.get_name(), pr.get_est_burst(), preempt, rdy_str))
        return



    def print_sim_out(self):
        f = open("simout.txt", "w")
        algorithms = ["FCFS", "SJF", "SRT", "RR"]
        process_list = [self.proc_FCFS, self.proc_SJF, self.proc_SRT, self.proc_RR]
        for j in range(4):
            burst_time = burst = wait_time = wait = turn_time = turn = total_switch = preempt_ = 0
            for process in process_list[j]:
                burst_time += sum(process.get_burst_times(0))
                burst += len(process.get_burst_times(0))
                wait_time += sum([x[0] for x in process.get_wait() if x[1] != 0])
                wait += len(process.get_wait())
                turn_time += sum([x[0] for x in process.get_turn_around() if x[1] != 0])
                turn += len(process.get_turn_around())
                total_switch += process.get_context_switch()
                preempt_ += process.get_preempt()

            avg_burst = burst_time / burst
            avg_wait = wait_time / wait
            if avg_wait < 0:
                avg_wait = 0
            avg_turn_around = (turn_time + wait_time) / turn
            utilization = (burst_time / self.t[j])*100

            f.write("Algorithm {}\n".format(algorithms[j]))
            f.write("-- average CPU burst time: {:.3f} ms\n".format(avg_burst))
            f.write("-- average wait time: {:.3f} ms\n".format(avg_wait))
            f.write("-- average turnaround time: {:.3f} ms\n".format(avg_turn_around))
            f.write("-- total number of context switches: {}\n".format(total_switch))
            f.write("-- total number of preemptions: {}\n".format(preempt_))
            f.write("-- CPU utilization: {:.3f}%\n".format(utilization))
        f.close()


def find_rand_arr(num, upper, lambd):
    while 1:
        tmp = math.floor(-(math.log(num.drand()) / lambd))
        if tmp <= upper:
            return tmp
        else:
            continue


def find_rand_burst(num, upper):
    while 1:
        tmp = math.ceil(num.drand() * 100) + 1
        if tmp <= upper:
            return tmp
        else:
            continue


def find_rand_ceil(num, upper, lambd):
    while 1:
        tmp = math.ceil(-(math.log(num.drand()) / lambd))
        if tmp <= upper:
            return tmp
        else:
            continue


if __name__ == '__main__':
    # if len(sys.argv) < 8:
    #     print("ERROR: Invalid argument.")
    #     exit(1) 

    # num_proc = int(sys.argv[1])
    # seed_ = int(sys.argv[2])
    # y = float(sys.argv[3])
    # ceil = int(sys.argv[4])
    # t_cs = int(sys.argv[5])
    # a = float(sys.argv[6])
    # t_slice = int(sys.argv[7])

    #   output 2
    # num_proc = 1
    # seed_ = 2
    # y = .01
    # ceil = 256
    # t_cs = 4
    # a = .5
    # t_slice = 128

    #   output 3
    # num_proc = 2
    # seed_ = 2
    # y = .01
    # ceil = 256
    # t_cs = 4
    # a = .5
    # t_slice = 128

    #   output 4
    num_proc = 16
    seed_ = 2
    y = .01
    ceil = 256
    t_cs = 4
    a = .75
    t_slice = 64


    alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
                'U', 'V', 'W', 'X', 'Y', 'Z']

    rand = Rand48(0)
    rand.srand(seed_)
    processes = []
    for i in range(num_proc):
        arrival_time = find_rand_arr(rand, ceil, y)
        bursts = find_rand_burst(rand, ceil)

        burst_l = []
        io_l = []
        for c in range(bursts - 1):
            burst_l.append(find_rand_ceil(rand, ceil, y))
            if c != bursts - 2:
                io_l.append(find_rand_ceil(rand, ceil, y)*10)
        
        proc = Process(alphabet[i], arrival_time, burst_l, io_l)
        processes.append(proc)

    algo_processes = []
    for i in range(4):
        algo_processes.append(deepcopy(processes))

    cpu_scheduling = Scheduling(algo_processes, seed_, t_slice, a, y)

    cpu_scheduling.FCFS()
    cpu_scheduling.SJF()
    cpu_scheduling.SRT()
    cpu_scheduling.RR()
    cpu_scheduling.print_sim_out()
