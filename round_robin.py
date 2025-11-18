# src/algorithms/round_robin.py
# Penanggung Jawab: Tim Logika (Backend - Orang A)

import copy
from collections import deque

def run_rr(proses_list, time_quantum):
    """
    Menjalankan simulasi Round Robin.
    Mengembalikan (gantt_chart_data, completed_processes)
    """
    processes = copy.deepcopy(proses_list)
    
    # Antrian untuk proses yang siap (ready)
    ready_queue = deque()
    
    # Urutkan proses berdasarkan waktu kedatangan (untuk memasukkan ke antrian)
    processes.sort(key=lambda p: p.arrival_time)
    
    current_time = 0
    gantt_data = []
    completed_processes = []
    n = len(processes)
    
    arrival_index = 0 # Penanda untuk proses berikutnya yang akan datang
    
    # Masukkan proses pertama yang datang
    while arrival_index < n and processes[arrival_index].arrival_time <= current_time:
        ready_queue.append(processes[arrival_index])
        arrival_index += 1
        
    while ready_queue or arrival_index < n:
        if not ready_queue:
            # CPU Idle, majukan waktu
            next_arrival_time = processes[arrival_index].arrival_time
            gantt_data.append(("IDLE", current_time, next_arrival_time))
            current_time = next_arrival_time
            
            # Masukkan semua proses yang datang saat idle
            while arrival_index < n and processes[arrival_index].arrival_time <= current_time:
                ready_queue.append(processes[arrival_index])
                arrival_index += 1
            continue

        # Ambil proses dari depan antrian
        p = ready_queue.popleft()
        
        if p.start_time == -1:
            p.start_time = current_time
            
        # Tentukan lama eksekusi: min(sisa waktu, quantum)
        run_time = min(p.remaining_time, time_quantum)
        
        gantt_data.append((p.pid, current_time, current_time + run_time))
        
        p.remaining_time -= run_time
        last_time_executed = current_time # Catat waktu SEBELUM dieksekusi
        current_time += run_time
        
        # PENTING: Cek proses baru yang datang SAAT proses ini berjalan
        while arrival_index < n and processes[arrival_index].arrival_time <= current_time:
            ready_queue.append(processes[arrival_index])
            arrival_index += 1
            
        if p.remaining_time == 0:
            # Proses selesai
            p.finish_time = current_time
            completed_processes.append(p)
        else:
            # Proses belum selesai, masukkan kembali ke AKHIR antrian
            ready_queue.append(p)
            
    return gantt_data, completed_processes