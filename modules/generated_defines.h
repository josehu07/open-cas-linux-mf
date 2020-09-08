#define cas_blk_rq_append_bio(rq, bounce_bio) \
            blk_rq_append_bio(rq, &bounce_bio)
#define CAS_LOOKUP_BDEV(PATH) \
            lookup_bdev(PATH)
static inline struct bio *cas_bio_clone(struct bio *bio, gfp_t gfp_mask)
            {
                return bio_clone_fast(bio, gfp_mask, NULL);
            }
#define CAS_BIO_SET_DEV(bio, bdev) \
            bio_set_dev(bio, bdev)
#define CAS_BIO_GET_DEV(bio) \
            bio->bi_disk
#define CAS_IS_DISCARD(bio) \
			(((CAS_BIO_OP_FLAGS(bio)) & REQ_OP_MASK) == REQ_OP_DISCARD)
#define CAS_BIO_DISCARD \
			((REQ_OP_WRITE | REQ_OP_DISCARD))
#define CAS_BIO_OP_STATUS(bio) \
			bio->bi_status
#define CAS_BIO_OP_FLAGS_FORMAT "0x%016X"
#define CAS_BIO_OP_FLAGS(bio) \
			(bio)->bi_opf
#define CAS_BIO_BISIZE(bio) \
			bio->bi_iter.bi_size
#define CAS_BIO_BIIDX(bio) \
			bio->bi_iter.bi_idx
#define CAS_BIO_BISECTOR(bio) \
			bio->bi_iter.bi_sector
#define CAS_SEGMENT_BVEC(vec) \
			(&(vec))
#define CAS_END_REQUEST_ALL blk_mq_end_request
#define CAS_BLK_STATUS_T blk_status_t
#define CAS_BLK_STS_OK BLK_STS_OK

        #include <linux/blk-mq.h>
        #include <scsi/scsi_request.h>
        #include <scsi/scsi_cmnd.h>
        static inline void cas_blk_rq_set_block_pc(struct request *rq)
        {
            struct scsi_cmnd *cmd = blk_mq_rq_to_pdu(rq);

            scsi_req_init(&cmd->req);
        }
#define CAS_DAEMONIZE(name, arg...) \
			do { } while (0)
#define CAS_ALIAS_NODE_TO_DENTRY(alias) \
			container_of(alias, struct dentry, d_u.d_alias)
#define CAS_SET_DISCARD_ZEROES_DATA(queue_limits, val) \
			({})
#define CAS_ERRNO_TO_BLK_STS(status) errno_to_blk_status(status)
#define CAS_REQ_FLUSH \
			REQ_PREFLUSH
#define CAS_FLUSH_SUPPORTED \
			1

		static inline void cas_generic_start_io_acct(struct request_queue *q,
			int rw, unsigned long sectors, struct hd_struct *part) {
			generic_start_io_acct(q, rw, sectors, part);
		}

		static inline void cas_generic_end_io_acct(struct request_queue *q,
			int rw, struct hd_struct *part, unsigned long start_time)
		{
			generic_end_io_acct(q, rw, part, start_time);
		}

	static inline unsigned long cas_get_free_mem(void)
		{	return si_mem_available() << PAGE_SHIFT;
		}
#define CAS_ALIAS_NODE_TYPE \
			struct hlist_node
#define CAS_DENTRY_LIST_EMPTY(head) \
			hlist_empty(head)
#define CAS_INODE_FOR_EACH_DENTRY(pos, head) \
			hlist_for_each(pos, head)
#define CAS_FILE_INODE(file) \
			file->f_inode

#include <uapi/asm-generic/mman-common.h>
#include <uapi/linux/mman.h>
	static inline unsigned long cas_vm_mmap(struct file *file,
			unsigned long addr, unsigned long len)
	{
		return vm_mmap(file, addr, len, PROT_READ | PROT_WRITE,
			MAP_ANONYMOUS | MAP_PRIVATE, 0);
	}

	static inline int cas_vm_munmap(unsigned long start, size_t len)
	{
		return vm_munmap(start, len);
	}
#define cas_blk_queue_bounce(q, bounce_bio) \
			({})
#define CAS_SET_QUEUE_CHUNK_SECTORS(queue, chunk_size) \
			queue->limits.chunk_sectors = chunk_size
#define CAS_QUEUE_FLAG_SET(flag, request_queue) \
			blk_queue_flag_set(flag, request_queue)

	static inline void cas_copy_queue_limits(struct request_queue *exp_q,
			struct request_queue *cache_q, struct request_queue *core_q)
	{
		exp_q->limits = cache_q->limits;
		exp_q->limits.max_sectors = core_q->limits.max_sectors;
		exp_q->limits.max_hw_sectors = core_q->limits.max_hw_sectors;
		exp_q->limits.max_segments = core_q->limits.max_segments;
		exp_q->limits.max_write_same_sectors = 0;
		exp_q->limits.max_write_zeroes_sectors = 0;
	}
#define CAS_QUEUE_SPIN_LOCK(q) spin_lock_irq(&q->queue_lock)
#define CAS_QUEUE_SPIN_UNLOCK(q) spin_unlock_irq(&q->queue_lock)

	static inline int cas_is_rq_type_fs(struct request *rq)
	{
		switch (req_op(rq)){
		case REQ_OP_READ:
		case REQ_OP_WRITE:
		case REQ_OP_FLUSH:
		case REQ_OP_DISCARD:
			return true;
		default:
			return false;
		}
	}

	static inline blk_qc_t cas_submit_bio(int rw, struct bio *bio)
	{
		CAS_BIO_OP_FLAGS(bio) |= rw;
		return submit_bio(bio);
	}
#define CAS_RQ_DATA_DIR_WR \
			WRITE
#define CAS_IS_WRITE_FUA(flags) \
			((flags) & REQ_FUA)
#define CAS_WRITE_FUA \
			REQ_FUA
#define CAS_WLTH_SUPPORT \
			1
#define CAS_CHECK_BARRIER(bio) \
			((CAS_BIO_OP_FLAGS(bio) & RQF_SOFTBARRIER) != 0)
#define CAS_REFER_BLOCK_CALLBACK(name) \
				   name##_callback
#define CAS_BLOCK_CALLBACK_INIT(BIO) \
			{; }
#define CAS_BLOCK_CALLBACK_RETURN(BIO) \
			{ return; }
#define CAS_BIO_ENDIO(BIO, BYTES_DONE, ERROR) \
			({ CAS_BIO_OP_STATUS(BIO) = ERROR; bio_endio(BIO); })
#define CAS_DECLARE_BLOCK_CALLBACK(name, BIO, BYTES_DONE, ERROR) \
			void name##_callback(BIO)
#define CAS_BLOCK_CALLBACK_ERROR(BIO, ERROR) \
			CAS_BIO_OP_STATUS(BIO)
#define CAS_IS_WRITE_FLUSH_FUA(flags) \
			((REQ_PREFLUSH | REQ_FUA) == ((flags) & (REQ_PREFLUSH |REQ_FUA)))
#define CAS_WRITE_FLUSH_FUA \
			(REQ_PREFLUSH | REQ_FUA)

	static inline struct request *cas_blk_make_request(struct request_queue *q,
		struct bio *bio, gfp_t gfp_mask)
	{
		struct request *rq = blk_get_request(q, bio_data_dir(bio), gfp_mask);
		if (IS_ERR(rq))
			return rq;
		cas_blk_rq_set_block_pc(rq);
		rq->q = q;
		for_each_bio(bio) {
			struct bio *bounce_bio = bio;
			int ret;
			cas_blk_queue_bounce(q, &bounce_bio);
			ret = cas_blk_rq_append_bio(rq, bounce_bio);
			if (unlikely(ret)) {
				blk_put_request(rq);
				return ERR_PTR(ret);
			}
		}
		return rq;
	}
#define CAS_CHECK_QUEUE_FLUSH(q) \
			test_bit(QUEUE_FLAG_WC, &(q)->queue_flags)
#define CAS_CHECK_QUEUE_FUA(q) \
			test_bit(QUEUE_FLAG_FUA, &(q)->queue_flags)

	static inline void cas_set_queue_flush_fua(struct request_queue *q,
			bool flush, bool fua)
	{
		blk_queue_write_cache(q, flush, fua);
	}
#define CAS_RQ_IS_FLUSH(rq) \
			((rq)->cmd_flags & REQ_PREFLUSH)
#define CAS_WRITE_FLUSH \
			(REQ_OP_WRITE | REQ_PREFLUSH)
#define CAS_IS_WRITE_FLUSH(flags) \
			(CAS_WRITE_FLUSH == ((flags) & CAS_WRITE_FLUSH))
