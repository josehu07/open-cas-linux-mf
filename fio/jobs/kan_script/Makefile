
multi_thread_aio: multi_thread_aio.cpp ConsumerProducerQueue.h
	g++ -std=c++11 -o multi_thread_aio -D_GNU_SOURCE multi_thread_aio.cpp ConsumerProducerQueue.h -lpthread -laio

clean:
	rm init raw_test identify_chunk identify_interleave identify_mapping
