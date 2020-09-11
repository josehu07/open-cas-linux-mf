#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <assert.h> 
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <time.h>
#include <pthread.h>
#include <atomic>
#include <fstream>
#include <vector>
#include <iostream>
#include <libaio.h>
#include <mutex>
#include <condition_variable>
#include "ConsumerProducerQueue.h"

#define MAX_COUNT 65536

std::atomic<long> pointer(0);
std::vector<long> read_order;

// Note: all pos in sector unless before passed in read/write
int SECTOR_SIZE = 512;
int STRIDE_SIZE = SECTOR_SIZE * 1;      // chunk size actually
int num_ios = 5000000;
int completed_ios = 0;

int D = 0;
int shared_space_ratio = 0;
int j = 0;
int d = 0;
int fd = 0;
io_context_t ctx_;

std::condition_variable cond;
std::mutex mutex;
int queue_depth = 0;
int max_qd = 16;
ConsumerProducerQueue<long> job_queue;
int pattern = 7;

struct io_event events[MAX_COUNT];
struct timespec timeout;
char * read_buf;

void *eachThread(void *vargp) 
{
    // consumer	
    int id = *(int*)vargp;
    long pos;    // in unit of sector
    printf("Thread %d ready to run \n", id);
    
    int sz;

    for ( ; ; ) {
	// Consumer wait the queue depth control
	job_queue.consume(pos);
	if (pos == -1) {
	    break;
	}
	//std::cout << "to issue IO " << pos/4096 << std::endl;
        struct iocb * p = (struct iocb *)malloc(sizeof(struct iocb));
        if (pos % 2 == 0) {
	    io_prep_pread(p, fd, read_buf, STRIDE_SIZE, pos / 2);
	} else {
	    io_prep_pwrite(p, fd, read_buf, STRIDE_SIZE, pos / 2);
	}
	p->data = (void *) read_buf;

        if (io_submit(ctx_, 1, &p) != 1) {
            io_destroy(ctx_);
            std::cout << "io submit error" << std::endl;
            exit(1);
        }
    }
    std::cout << "Thread " << id << " issued all IOs" << std::endl;
    return NULL; 
} 


void generate_read_trace(char type) {
     if (type == 'r') {
	 std::cout << "To read randomly" << std::endl;
         srand(time(0));
	 long tmp_pos;
	 
	 long total_chunks = (long) 1*1024*1024*2/d; 
	 long read_start_chunk = 0;
	 long read_end_chunk = total_chunks;
	 long write_start_chunk = (long) (total_chunks * (1.0 - (shared_space_ratio)/100.0));
	 //long read_end_chunk = (long) (total_chunks * (0.5 + (shared_space_ratio/2)/100.0));
	 //long write_start_chunk = (long) (total_chunks * (0.5 - (shared_space_ratio/2)/100.0));

	 std::cout << "chunks for read and write, total: " << total_chunks << "\n";
	 std::cout << "       reads: " << read_start_chunk << ", " << read_end_chunk << "\n";
	 std::cout << "       writes: " << write_start_chunk << ", " << total_chunks << "\n";

	 for (int i = 0; i < num_ios; i++) {
             if (rand() % 100 >= D) {
	         // generate a read
		 //tmp_pos = (long)((rand() %(1*1024*1024*2/d)))*STRIDE_SIZE;
		 tmp_pos = (long)(rand()%(read_end_chunk - read_start_chunk) + read_start_chunk) * STRIDE_SIZE;
	         tmp_pos = tmp_pos * 2;
                 read_order.push_back(tmp_pos);
	     } else {
	         // generate a read
		 tmp_pos = (long)(rand()%(total_chunks - write_start_chunk) + write_start_chunk) * STRIDE_SIZE;
		 //tmp_pos = (long)((rand() %(1*1024*1024*2/d)))*STRIDE_SIZE;
	         tmp_pos = tmp_pos * 2 + 1;
                 read_order.push_back(tmp_pos);
	     }
	     
	 }
     } else if (type == '4') {  // split 8 sectors into 1*QD sectors
         int small = 4;
         num_ios *= small;
	 for (int i = 0; i < num_ios/small; i++) {
	     for (int j = 0; j < small; j++)
	         read_order.push_back((long)(i)*(8*SECTOR_SIZE + D*SECTOR_SIZE) + j*STRIDE_SIZE);
	 }
     }else {
        std::cout << "Wrong choice of workloads, should be seq/random" << std::endl;
	exit(1);
     }

     return;
}

int main(int argc, char* * argv) {
     printf("===== Multi-thread libaio to Specified Device =====\n");
     // identify chunk size
     if (argc < 7) {
         printf("Wrong parameters: multi_thread_aio dev_name D(write_ratio) j(number of threads to submit IO) d(io_size in sector) shared_read_write_ratio(shared access space for reads and writes, e.g. 20%) queue_depth\n");
         return 1;
     }
     D = atoi(argv[2]);    //write ratio
     shared_space_ratio = atoi(argv[5]); // shared read, write access space
     j = atoi(argv[3]);
     d = atoi(argv[4]);        // request size
     STRIDE_SIZE = SECTOR_SIZE * d;
     max_qd = atoi(argv[6]);
     //max_qd = 16;
     pattern = atoi(argv[6])/16;
     job_queue.set_max(max_qd);

     printf("To run with:\n   write ratio: %d, num_threads: %d, request_size: %d, device_name: %s, shared_read_write_space_ratio: %s, qd: %d\n", D, j, STRIDE_SIZE, argv[1], argv[5], max_qd);

     // open raw block device
     fd = open(argv[1], O_RDWR | O_DIRECT);      // O_DIRECT
     if (fd < 0) {
         printf("Raw Device Open failed\n");
         return 1;
     } 
    // context to do async IO 
    memset(&ctx_, 0, sizeof(ctx_));
    if (io_setup(MAX_COUNT, &ctx_) != 0) {
        std::cout << "io_context_t set failed" << std::endl;
        exit(1);
    }
    // generate read trace
    generate_read_trace('r');

     //parallel reads
     
     // start the number of threads
     pthread_t * thread_pool = (pthread_t *)malloc(sizeof(pthread_t) * j);

     
     for (int i = 0; i < j; i++) {
         int *arg = (int *)malloc(sizeof(*arg));
         *arg = i;
         pthread_create(&thread_pool[i], NULL, eachThread, (void *)arg);
     }


     read_buf = (char *) malloc(sizeof(char) * (STRIDE_SIZE + SECTOR_SIZE));
     int ret = posix_memalign((void **)&read_buf, SECTOR_SIZE, STRIDE_SIZE + SECTOR_SIZE);
     sleep(1);
    
     //as a producer
     struct timeval start, end;
     gettimeofday(&start, NULL);
     int onflight_io = 0;

     timeout.tv_sec = 0;
     timeout.tv_nsec = 100;
     for (int i = 0; i < num_ios;) {
	// just add
        int ret = io_getevents(ctx_, 0, MAX_COUNT, events, &timeout);
        if (ret < 0) {
            std::cout << "Getevents Error" << std::endl; 
            exit(1);
        } 
	if (ret > 0) {
	    onflight_io -= ret;
            //std::cout << "=== Get Events("<< ret << "): " << ret << std::endl;
            //for (int j = 0; j < ret; j++) {
            //    std::cout << "=== Complete " << "::" << events[j].obj->aio_fildes << std::endl;
            //    free((struct iocb *)events[j].obj);
            //}
        }

        //if (onflight_io >= max_qd)
        //continue;
	
	//std::cout << "Add " << i << ": " << read_order[i] << std::endl;
	if (argv[5][0] == 'j') {
                if (onflight_io >= max_qd)
                //if (onflight_io/2 >= max_qd)
                  continue;
		job_queue.add(read_order[i]);
	        //std::cout << "Add " << i << ": " << read_order[i] << std::endl;
		//job_queue.add(read_order[i] + SECTOR_SIZE);
	        //onflight_io+=2;
	        onflight_io++;
        } else {
                if (onflight_io >= max_qd)
                  continue;
	        job_queue.add(read_order[i]);
	        onflight_io++;
	}
	i++;
     }

     //wait until all IO finished
     while (onflight_io) {
        int ret = io_getevents(ctx_, 0, MAX_COUNT, events, &timeout);
        if (ret < 0) {
            std::cout << "Getevents Error" << std::endl; 
            exit(1);
        } 
	if (ret > 0) {
	    onflight_io -= ret;
            //std::cout << "=== Get Events("<< ret << "): " << ret << std::endl;
            //for (int j = 0; j < ret; j++) {
            //    std::cout << "=== Complete " << "::" << events[j].obj->aio_fildes << std::endl;
            //}
        } 
     }



     gettimeofday(&end, NULL);
     long time_us = ((end.tv_sec * 1000000 + end.tv_usec)
                  - (start.tv_sec * 1000000 + start.tv_usec));
     
     
     // Signal to exit 
     for (int i = 0; i < j; i++) {
         job_queue.add(-1);
     }
     for (int i = 0; i < j; i++) {
         pthread_join(thread_pool[i], NULL);
     }
     std::cout << "All IO finished" << std::endl;
     printf("Time taken: %ld us, Bandwidth: %f MB/s \n", time_us, (float)((long)STRIDE_SIZE*num_ios)/1024/1024*1000000/time_us);

     free(read_buf);
     close(fd);
     return 0;
}
