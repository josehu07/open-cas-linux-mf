import itertools
from pyreuse.helpers import *
from pyreuse.sysutils.cgroup import Cgroup
import os.path
import time
import json
import os
import datetime

from pyreuse.sysutils.blocktrace import *
from pyreuse.sysutils.ncq import *
from pyreuse.sysutils.iostat_parser import *

# basis
KB = 1024
MB = 1024 * KB
GB = 1024 * MB 


# experiment setup
class Experiment(object):
    def __init__(self):
        # config something
        #self.exp_name = 'optane_flash'
        #self.exp_name = 'nvdimm_optane'
        #self.exp_name = 'nvdimm_flash'
        self.exp_name = 'dram_nvdimm'
        self.home_dir = '/home/kanwu/Research/open-cas-linux-mf/fio/jobs/kan_script/'
        self.res_dir = self.home_dir + 'results/' + self.exp_name
        self.tmp_dir = '/dev/shm/'
        prepare_dir(self.res_dir)
       
        # tools config
        self.tools_config = {
            'clear_page_cache': True,   # whether clear page cache before each run 
            'blktrace'        : False,   # check block IOs
            'iostat'          : False,  # check ios and cpu/io utilization
            'perf'            : False,  # draw flamegraph
            'sar'             : False   # check page faults
        }

        # experiment config
        config = {
          #'type': ['randread_optane_ssd_flash_80_hit'],
          #'type': ['randread_nvdimm_99_hit'],
          'type': ['randread_nvdimm_80_hit'],
          'script': ['./run_with_mf.sh mfwa', './run_with_pure.sh wa'], # remember to modify the casadm commands
          #'qd': [1, 3, 5, 6], # optane SSD as cache
          #'qd': [4, 8, 12, 16], # NVDIMM as cache
          'qd': [16], # NVDIMM as cache
        }

        # handle
        self.handle_config(config) 
        print '========================= overall ', len(self.all_configs), ' experiments ============================='
        print '==================== results in ', self.res_dir, ' ============================'
 
    def handle_config(self, config):
        config_dic = list(config.keys())
        config_lists = list(config.values())

        self.all_configs = []
        for element in itertools.product(*config_lists):
            new_config = dict(list(itertools.izip(config_dic, list(element))))
            self.all_configs.append(new_config)
        
    def dump_config(self, config):
        self.cur_exp_dir = self.res_dir + '/' + datetime.now().strftime("%H-%M-%S_%Y%m%d")
        os.mkdir(self.cur_exp_dir)
        with open(self.cur_exp_dir + '/config.json', 'w') as config_output:
            json.dump(config, config_output)

    def before_each(self, config):
        print '                ********* Configured with **********'
        print config
        self.dump_config(config)

        # create job file
        with open('/home/kanwu/Research/open-cas-linux-mf/fio/jobs/kan_script/fio_jobs/'+config['type'] + '.fio.template', 'r') as input_file, open('/home/kanwu/Research/open-cas-linux-mf/fio/jobs/kan_script/fio_jobs/' + config['type'] + '.fio', 'w') as output_file:
            for line in input_file:
                #TODO optane SSD and NVDIMM as a cache is a bit different, since optane SSD use async IO
                #if 'iodepth' in line:
                #    output_file.write('iodepth=' + str(config['qd']) + '\n') 
                #    continue
                
                if 'numjobs' in line:
                    output_file.write('numjobs=' + str(config['qd']/2) + '\n')  #TODO divded by 2 to creat 80% hit ratios with two jobs, nvdimm as a cache, 80% hit rate
                    #output_file.write('numjobs=' + str(config['qd']) + '\n')  #TODO divded by 2 to creat 80% hit ratios with two jobs, nvdimm as a cache, 80% hit rate
                    continue
                
                output_file.write(line)

        # clear page cache
        if self.tools_config['clear_page_cache']:
            shcmd('sync; echo 3 > /proc/sys/vm/drop_caches; sleep 1')
        # start iostat
        if self.tools_config['iostat']:
            shcmd('pkill iostat', ignore_error = True)
            shcmd('iostat -mx 1 ' + ' > ' + self.tmp_dir + '/iostat.out &')

        # start blktrace
        stop_blktrace_on_bg()
        if self.tools_config['blktrace']:
            #start_blktrace_on_bg('/dev/nvme0n1p4', self.tmp_dir +'/blktrace.output', ['issue', 'complete'])
            start_blktrace_on_bg(self.dev_dir, self.tmp_dir +'/blktrace.output', ['issue', 'complete'])
       
        # start perf
        shcmd('pkill perf', ignore_error = True)
        if self.tools_config['perf']:
            shcmd('rm perf.data', ignore_error = True)
            shcmd('perf record -F 99 -a -g -- sleep 30 &')
            #shcmd('perf record -F 99 -a -g -- sleep 60 &')

        # kill exp workload
        shcmd('pkill -9 fio', ignore_error = True)
   
        # start sar to trace page faults
        shcmd('pkill sar', ignore_error = True)
        if self.tools_config['sar']:
            shcmd('sar -B 1 > ' + self.tmp_dir + '/sar.out &')


 
    def exp(self, config):
        print '              *********** start running ***********'
        # read/ write
        #shcmd("bash ./run_with_mf.sh mfwa   ./fio_jobs/" + config['type'] + ".fio > " + self.tmp_dir + "/running")
        shcmd("bash " + config['script'] + "  ./fio_jobs/" + config['type'] + ".fio > " + self.tmp_dir + "/running")
    
    def handle_iostat_out(self, iostat_output):
        print "==== utilization statistics ===="
        stats = parse_batch(iostat_output.read())
        with open(self.cur_exp_dir + '/iostat.out.cpu_parsed', 'w') as parsed_iostat:
            parsed_iostat.write('iowait system user idle \n')
            item_len = average_iowait = average_system = average_user = average_idle = 0
            for item in stats['cpu']:
                parsed_iostat.write(str(item['iowait']) + ' ' + str(item['system']) + ' ' + str(item['user']) + ' ' + str(item['idle']) + '\n')
                #if float(item['idle']) > 79:
                #    continue
                item_len += 1
                average_iowait += float(item['iowait'])
                average_system += float(item['system'])
                average_user += float(item['user'])
                average_idle += float(item['idle'])
            if item_len > 0:
                print 'iowait  system  user  idle'
                print str(average_iowait/item_len), str(average_system/item_len), str(average_user/item_len), str(average_idle/item_len)
            else:
                print 'seems too idle of CPU'

        with open(self.cur_exp_dir + '/iostat.out.disk_parsed', 'w') as parsed_iostat:
            parsed_iostat.write('r_iops r_bw(MB/s) w_iops w_bw(MB/s) avgrq_sz(KB) avgqu_sz\n')
            item_len = average_rbw = average_wbw = 0
            for item in stats['io']:
                parsed_iostat.write(item['r/s'] + ' ' + item['rMB/s'] + ' ' + item['w/s'] + ' ' + item['wMB/s'] + ' ' + str(float(item['wareq-sz'])) + ' '+ item['aqu-sz'] +'\n')
                #if float(item['rMB/s']) + float(item['wMB/s']) < 20:
                #    continue
                item_len += 1
                average_rbw += float(item['rMB/s'])
                average_wbw += float(item['wMB/s'])
            if item_len > 0:
                print str(average_rbw/item_len), str(average_wbw/item_len)
            else:
                print 'seems too idle of Disk'
        print "================================="    

    def latency_stat(self, events):
        min_latency = 100000.0
        avg_latency = 0.0
        count = 0
        max_latency = 0.0
        lats = []
        for line in events:
            lat = float(line.split()[-2])
            if lat > 0:
                lats.append(lat)
                count += 1
                avg_latency += lat
                if lat < min_latency:
                    min_latency = lat
                if lat > max_latency:
                    max_latency = lat
        with open(self.cur_exp_dir + '/latency.sort','w') as lat_out:
            for lat in sorted(lats):
                lat_out.write(str(lat * 1000000) +'\n')

        with open(self.cur_exp_dir + '/latency.stat','w') as lat_out:
            lat_out.write('======= Latency statistics ========\n')
            lat_out.write('  num_req: ' +  str(count) + '\n')
            lat_out.write('  average: ' + str(avg_latency/count * 1000000) + 'us\n')
            lat_out.write('  min_lat: ' + str(min_latency * 1000000) + 'us\n')
            lat_out.write('  max_lat: ' + str(max_latency * 1000000) + 'us\n')
            lat_out.write('===================================')
    
    def after_each(self, config):
        print '              **************** done ***************'


        shcmd("sync")
        # kill something at first, not to introduce IOs during analysis 
        if self.tools_config['iostat']:
            shcmd('pkill iostat; sleep 2')
        if self.tools_config['sar']:
            shcmd('pkill sar')
        if self.tools_config['blktrace']:
            stop_blktrace_on_bg()

        shcmd("sync")
        # copy running results(contain throughput)
        shcmd('cp ' + self.tmp_dir + '/running ' + self.cur_exp_dir + '/running')
        shcmd('cp ' + "./fio_jobs/" + config['type'] + ".fio " + self.cur_exp_dir + '/fio.config')
        # wrapup iostat
        if self.tools_config['iostat']:
            with open(self.tmp_dir + '/iostat.out') as iostat_output:
                self.handle_iostat_out(iostat_output)
            shcmd('cp ' + self.tmp_dir + '/iostat.out ' + self.cur_exp_dir + '/iostat.out')
        # wrapup sar
        if self.tools_config['sar']:
            shcmd('cp ' + self.tmp_dir + '/sar.out ' + self.cur_exp_dir + '/sar.out')

        # wrapup flamegraph(perf)
        if self.tools_config['perf']:
            shcmd('cp perf.data ' + self.cur_exp_dir + '/')
            #shcmd('perf script | /mnt/ssd/fio_test/experiments/FlameGraph/stackcollapse-perf.pl > ' + self.cur_exp_dir + '/out.perf-folded')
            #shcmd('perf script | /mnt/ssd/fio_test/experiments/FlameGraph/stackcollapse-perf.pl > out.perf-folded')
            #shcmd('/mnt/ssd/fio_test/experiments/FlameGraph/flamegraph.pl out.perf-folded > ' + self.cur_exp_dir + '/perf-kernel.svg')
        
        # wrapup blktrace
        if self.tools_config['blktrace']:
            shcmd('cp ' + self.tmp_dir + '/blktrace.output ' + self.cur_exp_dir + '/blktrace.output')
            #return
            blkresult = BlktraceResultInMem(
                    sector_size=512,
                    event_file_column_names=['pid', 'action', 'operation', 'offset', 'size',
                        'timestamp', 'pre_wait_time', 'latency', 'sync'],
                    raw_blkparse_file_path=self.tmp_dir+'/blktrace.output',
                    parsed_output_path=self.cur_exp_dir+'/blkparse-output.txt.parsed')
            
            blkresult.create_event_file()
            with open(self.cur_exp_dir + '/blkparse-output.txt.parsed','r') as event_file:
                self.latency_stat(event_file)

            return
            # generate ncq
            table = parse_ncq(event_path = self.cur_exp_dir + '/blkparse-output.txt.parsed')
            with open(self.cur_exp_dir + '/ncq.txt','w') as ncq_output:
                for item in table:
                    ncq_output.write("%s\n" % ' '.join(str(e) for e in [item['pid'], item['action'], item['operation'], item['offset'], item['size'], item['timestamp'], item['pre_depth'], item['post_depth']]))

    def run(self):
        for config in self.all_configs:
            self.before_each(config)
            self.exp(config)
            self.after_each(config)

if __name__=='__main__':

    exp = Experiment()
    exp.run()
