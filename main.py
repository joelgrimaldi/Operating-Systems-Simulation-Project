if __name__ == '__main__':
    if len(sys.argv) < 8:
        print("ERROR: Invalid argument.")
        exit(1)

    num_proc = sys.argv[1]
    seed_ = sys.argv[2]
    y = sys.argv[3]
    ceil = sys.argv[4]
    t_cs = sys.argv[5]
    a = sys.argv[6]
    t_slice = sys.argv[7]

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
    cpu_scheduling.SRT()
    cpu_scheduling.SJF()
    cpu_scheduling.RR()