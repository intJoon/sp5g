#!/usr/bin/env python3

import json
import sys
import os
import argparse
from datetime import datetime

class ScenarioVisualizer:
    def __init__(self, scenario_file):
        with open(scenario_file, 'r') as f:
            self.scenario = json.load(f)
        
        self.ue_status = {}
        for ue in self.scenario['ues']:
            key = f"{ue['type']}:{ue['id']}"
            self.ue_status[key] = 'normal'
    
    def get_scenario_info(self):
        return {
            'name': self.scenario['scenario_name'],
            'description': self.scenario['description'],
            'criticality': self.scenario['criticality'],
            'total_ues': len(self.scenario['ues'])
        }
    
    def get_ue_list(self):
        return self.scenario['ues']
    
    def update_ue_status(self, ue_key, network_quality):
        if network_quality >= 90:
            status = 'normal'
        elif network_quality >= 60:
            status = 'degraded'
        elif network_quality >= 30:
            status = 'severe'
        else:
            status = 'critical'
        
        self.ue_status[ue_key] = status
        return status
    
    def get_ue_impact(self, ue_id):
        for ue in self.scenario['ues']:
            if ue['id'] == ue_id:
                status = self.ue_status.get(f"{ue['type']}:{ue['id']}", 'normal')
                
                if status == 'normal':
                    return ue['normal_status']
                else:
                    return ue['attack_impact'].get(status, 'Unknown impact')
        return None
    
    def get_overall_impact(self):
        status_counts = {'normal': 0, 'degraded': 0, 'severe': 0, 'critical': 0}
        
        for status in self.ue_status.values():
            status_counts[status] += 1
        
        total = len(self.ue_status)
        if status_counts['critical'] > total * 0.3:
            overall = 'critical'
        elif status_counts['severe'] + status_counts['critical'] > total * 0.5:
            overall = 'severe'
        elif status_counts['degraded'] > total * 0.5:
            overall = 'degraded'
        else:
            overall = 'normal'
        
        return {
            'overall_status': overall,
            'status_distribution': status_counts,
            'impact_details': self.scenario['impact_matrix'][overall]
        }
    
    def render_ascii_map(self):
        width = 80
        height = 30
        
        print("=" * width)
        print(f"SCENARIO: {self.scenario['scenario_name']}")
        print(f"Background: {self.scenario['background']}")
        print("=" * width)
        
        grid = [[' ' for _ in range(width)] for _ in range(height)]
        
        for ue in self.scenario['ues']:
            x = min(int(ue['location']['x'] / 10), width - 5)
            y = min(int(ue['location']['y'] / 15), height - 1)
            
            status = self.ue_status.get(f"{ue['type']}:{ue['id']}", 'normal')
            
            icon_map = {
                'industrial_robot': '🤖',
                'autonomous_vehicle': '🚗',
                'military_drone': '✈️ ',
                'smartphone': '📱',
                'broadcast_camera': '📹'
            }
            
            status_indicator = {
                'normal': '●',
                'degraded': '◐',
                'severe': '◑',
                'critical': '○'
            }
            
            icon = icon_map.get(ue['type'], '?')
            indicator = status_indicator.get(status, '?')
            
            label = f"[{indicator}]{icon}"
            for i, char in enumerate(label):
                if x + i < width:
                    grid[y][x + i] = char
        
        for row in grid:
            print(''.join(row))
        
        print("=" * width)
        print("Legend: ● Normal  ◐ Degraded  ◑ Severe  ○ Critical")
        print("=" * width)
    
    def generate_report(self):
        print("\n" + "="*80)
        print(f"SCENARIO IMPACT REPORT: {self.scenario['scenario_name']}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        print(f"\nDescription: {self.scenario['description']}")
        print(f"Criticality: {self.scenario['criticality'].upper()}")
        
        print("\n" + "-"*80)
        print("UE STATUS DETAILS:")
        print("-"*80)
        
        for ue in self.scenario['ues']:
            key = f"{ue['type']}:{ue['id']}"
            status = self.ue_status.get(key, 'unknown')
            
            status_color = {
                'normal': '🟢',
                'degraded': '🟡',
                'severe': '🟠',
                'critical': '🔴'
            }
            
            print(f"\n{status_color.get(status, '⚪')} {ue['id']} ({ue['type']})")
            print(f"   Role: {ue['role']}")
            print(f"   Status: {status.upper()}")
            
            if status == 'normal':
                print(f"   Impact: {ue['normal_status']}")
            else:
                print(f"   Impact: {ue['attack_impact'].get(status, 'Unknown')}")
        
        print("\n" + "-"*80)
        print("OVERALL SCENARIO IMPACT:")
        print("-"*80)
        
        overall = self.get_overall_impact()
        
        print(f"\nOverall Status: {overall['overall_status'].upper()}")
        print(f"\nStatus Distribution:")
        for status, count in overall['status_distribution'].items():
            percentage = (count / len(self.ue_status)) * 100
            print(f"  {status.capitalize()}: {count} UEs ({percentage:.1f}%)")
        
        print(f"\nImpact Details:")
        for key, value in overall['impact_details'].items():
            print(f"  {key}: {value}")
        
        print("\n" + "="*80)

def main():
    parser = argparse.ArgumentParser(description='5G Scenario Visualizer')
    parser.add_argument('scenario', choices=['nuclear', 'highway', 'military', 'public', 'residential'],
                       help='Scenario to visualize')
    parser.add_argument('--simulate-attack', '-a', action='store_true',
                       help='Simulate attack impact')
    parser.add_argument('--severity', '-s', choices=['degraded', 'severe', 'critical'],
                       default='severe', help='Attack severity')
    
    args = parser.parse_args()
    
    scenario_files = {
        'nuclear': 'scenarios/nuclear_facility.json',
        'highway': 'scenarios/highway.json',
        'military': 'scenarios/military_operation.json',
        'public': 'scenarios/public_event.json',
        'residential': 'scenarios/residential.json'
    }
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scenario_file = os.path.join(script_dir, scenario_files[args.scenario])
    
    visualizer = ScenarioVisualizer(scenario_file)
    
    if args.simulate_attack:
        severity_map = {
            'degraded': 70,
            'severe': 40,
            'critical': 10
        }
        
        network_quality = severity_map[args.severity]
        
        for ue in visualizer.get_ue_list():
            key = f"{ue['type']}:{ue['id']}"
            
            import random
            ue_quality = network_quality + random.randint(-10, 10)
            ue_quality = max(0, min(100, ue_quality))
            
            visualizer.update_ue_status(key, ue_quality)
    
    visualizer.render_ascii_map()
    visualizer.generate_report()

if __name__ == '__main__':
    main()

