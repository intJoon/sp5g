#!/usr/bin/env python3

import argparse
import sys
import time
import logging
import os
import random
from scapy.all import *
from scapy.contrib.sctp import SCTP, SCTPChunkData
import struct

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class F1APFuzzer:
    def __init__(self, target_ip, target_port=38472, source_ip=None):
        self.target_ip = target_ip
        self.target_port = target_port
        self.source_ip = source_ip or self._get_source_ip()
        self.crashes_detected = []
        self.anomalies_detected = []
        self.test_cases = 0
        
        logger.info(f"F1AP Fuzzer initialized")
        logger.info(f"Target: {self.target_ip}:{self.target_port}")
        logger.info(f"Source: {self.source_ip}")
    
    def _get_source_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "192.168.1.100"
    
    def generate_malformed_f1ap(self):
        fuzzing_strategies = [
            self._fuzz_random_bytes,
            self._fuzz_overflow,
            self._fuzz_underflow,
            self._fuzz_format_string,
            self._fuzz_null_bytes,
            self._fuzz_special_chars,
            self._fuzz_length_mismatch,
            self._fuzz_invalid_ie,
            self._fuzz_sequence_error,
            self._fuzz_boundary_values
        ]
        
        strategy = random.choice(fuzzing_strategies)
        return strategy()
    
    def _fuzz_random_bytes(self):
        size = random.randint(1, 4096)
        return os.urandom(size)
    
    def _fuzz_overflow(self):
        overflow_patterns = [
            b'A' * 1000,
            b'A' * 10000,
            b'\xff' * 1000,
            b'\x00' * 1000 + b'A' * 100
        ]
        return random.choice(overflow_patterns)
    
    def _fuzz_underflow(self):
        return b''
    
    def _fuzz_format_string(self):
        format_strings = [
            b'%s%s%s%s%s%s%s%s%s%s',
            b'%x%x%x%x%x%x%x%x%x%x',
            b'%n%n%n%n%n%n',
            b'%08x.%08x.%08x.%08x'
        ]
        return random.choice(format_strings)
    
    def _fuzz_null_bytes(self):
        patterns = [
            b'\x00' * 100,
            b'test\x00\x00\x00',
            b'\x00test\x00',
            b'\x00' * 10 + b'A' * 50 + b'\x00' * 10
        ]
        return random.choice(patterns)
    
    def _fuzz_special_chars(self):
        special_chars = b'<>\'\"&;|`$(){}[]!@#^*~'
        return special_chars * random.randint(1, 50)
    
    def _fuzz_length_mismatch(self):
        declared_length = random.randint(10, 100)
        actual_data = os.urandom(random.randint(1, 200))
        
        header = struct.pack('>H', declared_length)
        return header + actual_data
    
    def _fuzz_invalid_ie(self):
        invalid_ie_id = random.randint(1000, 9999)
        ie_data = os.urandom(random.randint(1, 100))
        
        return struct.pack('>H', invalid_ie_id) + ie_data
    
    def _fuzz_sequence_error(self):
        sequence_num = random.choice([0xFFFFFFFF, 0, -1, 0x7FFFFFFF])
        data = struct.pack('>I', sequence_num & 0xFFFFFFFF)
        data += os.urandom(random.randint(10, 100))
        return data
    
    def _fuzz_boundary_values(self):
        boundary_values = [
            struct.pack('>I', 0),
            struct.pack('>I', 0xFFFFFFFF),
            struct.pack('>I', 0x7FFFFFFF),
            struct.pack('>I', 0x80000000),
            struct.pack('>H', 0),
            struct.pack('>H', 0xFFFF),
            struct.pack('>H', 0x7FFF),
            struct.pack('>H', 0x8000),
            struct.pack('>B', 0),
            struct.pack('>B', 0xFF),
            struct.pack('>B', 0x7F),
            struct.pack('>B', 0x80)
        ]
        return random.choice(boundary_values) + os.urandom(random.randint(0, 50))
    
    def send_fuzz_packet(self, payload):
        try:
            packet = IP(dst=self.target_ip, src=self.source_ip) / \
                     SCTP(sport=random.randint(10000, 65000), dport=self.target_port) / \
                     SCTPChunkData(data=payload)
            
            send(packet, verbose=False)
            return True
        except Exception as e:
            logger.error(f"Failed to send fuzz packet: {e}")
            return False
    
    def check_target_alive(self):
        try:
            response = sr1(
                IP(dst=self.target_ip)/ICMP(),
                timeout=2,
                verbose=False
            )
            return response is not None
        except:
            return False
    
    def run_fuzzing_campaign(self, iterations=1000, check_interval=100):
        logger.info(f"Starting fuzzing campaign: {iterations} iterations")
        logger.info("="*80)
        
        initial_alive = self.check_target_alive()
        if not initial_alive:
            logger.warning("Target may not be responding to ICMP initially")
        
        start_time = time.time()
        successful_tests = 0
        
        for i in range(iterations):
            self.test_cases += 1
            
            payload = self.generate_malformed_f1ap()
            
            if self.send_fuzz_packet(payload):
                successful_tests += 1
            
            time.sleep(0.01)
            
            if (i + 1) % check_interval == 0:
                logger.info(f"Progress: {i+1}/{iterations} ({(i+1)/iterations*100:.1f}%)")
                
                if not self.check_target_alive():
                    crash_info = {
                        'iteration': i + 1,
                        'timestamp': time.time(),
                        'payload_sample': payload[:50].hex()
                    }
                    self.crashes_detected.append(crash_info)
                    logger.warning(f"⚠️  Potential crash detected at iteration {i+1}!")
                    logger.warning(f"   Payload sample: {payload[:20].hex()}...")
                    
                    logger.info("Waiting 5 seconds for target recovery...")
                    time.sleep(5)
        
        elapsed_time = time.time() - start_time
        
        logger.info("="*80)
        logger.info("FUZZING CAMPAIGN COMPLETE")
        logger.info("="*80)
        logger.info(f"Total test cases: {self.test_cases}")
        logger.info(f"Successful sends: {successful_tests}")
        logger.info(f"Potential crashes detected: {len(self.crashes_detected)}")
        logger.info(f"Elapsed time: {elapsed_time:.2f}s")
        logger.info(f"Average rate: {self.test_cases/elapsed_time:.2f} tests/sec")
        
        if self.crashes_detected:
            logger.info("\nCrash Details:")
            for crash in self.crashes_detected:
                logger.info(f"  Iteration {crash['iteration']}: {crash['payload_sample']}")
        
        self._save_results()
    
    def _save_results(self):
        import json
        
        results = {
            'target': f"{self.target_ip}:{self.target_port}",
            'test_cases': self.test_cases,
            'crashes': len(self.crashes_detected),
            'crash_details': self.crashes_detected,
            'anomalies': len(self.anomalies_detected),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open('fuzzing_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info("\nResults saved to fuzzing_results.json")
        
        with open('potential_cves.txt', 'w') as f:
            f.write("="*80 + "\n")
            f.write("POTENTIAL F1AP VULNERABILITIES\n")
            f.write("="*80 + "\n\n")
            
            if self.crashes_detected:
                f.write(f"Discovered {len(self.crashes_detected)} potential crash conditions:\n\n")
                
                for i, crash in enumerate(self.crashes_detected, 1):
                    f.write(f"Finding #{i}:\n")
                    f.write(f"  Iteration: {crash['iteration']}\n")
                    f.write(f"  Payload: {crash['payload_sample']}\n")
                    f.write(f"  Impact: Denial of Service (service crash)\n")
                    f.write(f"  Severity: HIGH\n")
                    f.write(f"  Recommendation: Input validation on F1AP message parsing\n")
                    f.write("\n")
            else:
                f.write("No crashes detected during fuzzing campaign.\n")
                f.write("Target appears robust against basic fuzzing attempts.\n")
        
        logger.info("Potential CVEs saved to potential_cves.txt")

def main():
    parser = argparse.ArgumentParser(description='F1AP Fuzzer - Vulnerability Discovery Tool')
    parser.add_argument('--target', '-t', required=True, help='Target IP address')
    parser.add_argument('--port', '-p', type=int, default=38472, help='Target port (default: 38472)')
    parser.add_argument('--source', '-s', help='Source IP address')
    parser.add_argument('--iterations', '-i', type=int, default=1000, 
                       help='Number of fuzzing iterations')
    parser.add_argument('--check-interval', '-c', type=int, default=100,
                       help='Check target health every N iterations')
    
    args = parser.parse_args()
    
    if os.geteuid() != 0:
        logger.error("This script requires root privileges. Please run with sudo.")
        sys.exit(1)
    
    logger.info("="*80)
    logger.info("F1AP FUZZER - Vulnerability Discovery")
    logger.info("WARNING: For authorized testing only!")
    logger.info("="*80)
    logger.info("")
    
    fuzzer = F1APFuzzer(
        target_ip=args.target,
        target_port=args.port,
        source_ip=args.source
    )
    
    fuzzer.run_fuzzing_campaign(
        iterations=args.iterations,
        check_interval=args.check_interval
    )
    
    logger.info("\n✓ Fuzzing complete. Check fuzzing_results.json and potential_cves.txt")

if __name__ == '__main__':
    main()

