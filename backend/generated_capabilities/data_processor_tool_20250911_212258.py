
import json
import csv
import pandas as pd
from typing import Dict, Any, List, Optional, Union
import requests
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NetworkTrafficAnalyzer:
    """
    Tool for analyzing network traffic patterns and generating optimization
    and security recommendations.

    Note: This class provides a framework. Actual network traffic analysis
    requires specialized libraries (e.g., scapy, pyshark) and potentially
    access to raw packet data, which are outside the scope of this generic
    data processing tool. This enhanced version simulates such analysis
    based on loaded tabular data that *represents* network traffic logs.
    """

    def __init__(self):
        self.traffic_data = None
        self.recommendations = []
        self.security_alerts = []

    def load_traffic_log(self, filepath: str) -> Dict[str, Any]:
        """
        Load network traffic log data from a CSV file.
        Assumes the CSV contains columns relevant to network traffic,
        such as 'timestamp', 'source_ip', 'destination_ip', 'protocol',
        'port', 'packet_size', 'flags', 'flow_duration', etc.
        """
        if not isinstance(filepath, str) or not filepath:
            return {"success": False, "error": "Invalid filepath provided. Filepath must be a non-empty string."}
        if not filepath.lower().endswith('.csv'):
            logging.warning(f"File {filepath} does not have a .csv extension. Attempting to load anyway.")

        try:
            df = pd.read_csv(filepath)
            logging.info(f"Successfully loaded {len(df)} rows from {filepath}")

            # Basic validation for expected network traffic columns
            expected_columns = ['timestamp', 'source_ip', 'destination_ip', 'protocol', 'port', 'packet_size']
            missing_expected = [col for col in expected_columns if col not in df.columns]
            if missing_expected:
                logging.warning(f"CSV is missing some expected network traffic columns: {missing_expected}. Analysis might be limited.")

            # Attempt to convert timestamp if present
            if 'timestamp' in df.columns:
                try:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                except Exception as e:
                    logging.warning(f"Could not convert 'timestamp' column to datetime: {e}. Analysis based on time might be inaccurate.")

            self.traffic_data = df
            return {
                "success": True,
                "message": f"Successfully loaded {len(df)} rows from {filepath}",
                "rows": len(df),
                "columns": list(df.columns),
                "sample_data": df.head().to_dict('records')
            }
        except FileNotFoundError:
            logging.error(f"File not found at {filepath}")
            return {"success": False, "error": f"File not found at {filepath}"}
        except pd.errors.EmptyDataError:
            logging.error(f"The file {filepath} is empty.")
            return {"success": False, "error": f"The file {filepath} is empty."}
        except Exception as e:
            logging.error(f"An unexpected error occurred while loading {filepath}: {e}")
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

    def analyze_traffic_patterns(self) -> Dict[str, Any]:
        """
        Performs basic analysis of loaded network traffic data.
        This is a simulated analysis. Real analysis would involve
        packet inspection and more sophisticated metrics.
        """
        if self.traffic_data is None:
            return {"success": False, "error": "No network traffic data loaded. Use 'load_traffic_log' first."}

        try:
            df = self.traffic_data.copy()
            analysis_results = {}

            # Basic statistics
            analysis_results['total_packets'] = len(df)
            analysis_results['unique_sources'] = df['source_ip'].nunique() if 'source_ip' in df.columns else 'N/A'
            analysis_results['unique_destinations'] = df['destination_ip'].nunique() if 'destination_ip' in df.columns else 'N/A'

            if 'packet_size' in df.columns:
                analysis_results['average_packet_size'] = df['packet_size'].mean()
                analysis_results['max_packet_size'] = df['packet_size'].max()
                analysis_results['min_packet_size'] = df['packet_size'].min()
            else:
                analysis_results['packet_size_stats'] = "Column 'packet_size' not found."

            if 'protocol' in df.columns:
                analysis_results['protocol_distribution'] = df['protocol'].value_counts().to_dict()
            else:
                analysis_results['protocol_distribution'] = "Column 'protocol' not found."

            if 'port' in df.columns:
                analysis_results['common_ports'] = df['port'].value_counts().head(10).to_dict()
            else:
                analysis_results['common_ports'] = "Column 'port' not found."

            if 'timestamp' in df.columns and pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                analysis_results['start_time'] = df['timestamp'].min().isoformat()
                analysis_results['end_time'] = df['timestamp'].max().isoformat()
                analysis_results['traffic_duration_seconds'] = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()
            else:
                analysis_results['time_range'] = "Timestamp data not suitable for time-based analysis."

            logging.info("Basic traffic pattern analysis completed.")
            return {"success": True, "analysis": analysis_results, "message": "Traffic pattern analysis completed."}

        except KeyError as e:
            logging.error(f"Missing expected column for analysis: {e}")
            return {"success": False, "error": f"Missing expected column for analysis: {e}. Please ensure your log file has relevant columns."}
        except Exception as e:
            logging.error(f"An error occurred during traffic pattern analysis: {e}")
            return {"success": False, "error": f"An unexpected error occurred during analysis: {str(e)}"}

    def generate_optimization_recommendations(self) -> Dict[str, Any]:
        """
        Generates optimization recommendations based on traffic patterns.
        This is a rule-based simulation.
        """
        if self.traffic_data is None:
            return {"success": False, "error": "No network traffic data loaded. Use 'load_traffic_log' first."}

        self.recommendations = []
        df = self.traffic_data.copy()

        try:
            # Rule 1: High volume of small packets to certain destinations might indicate inefficient protocols or overhead.
            if 'packet_size' in df.columns and 'destination_ip' in df.columns:
                avg_packet_size = df['packet_size'].mean()
                small_packet_threshold = avg_packet_size * 0.2  # Example threshold
                small_packets_df = df[df['packet_size'] < small_packet_threshold]
                if not small_packets_df.empty:
                    large_destinations = small_packets_df['destination_ip'].value_counts().head(5)
                    for ip, count in large_destinations.items():
                        self.recommendations.append({
                            "type": "Optimization",
                            "area": "Protocol Efficiency",
                            "description": f"High volume of small packets ({count} detected) targeting {ip}. Consider optimizing protocols or payload packaging for efficiency.",
                            "details": {"target_ip": ip, "packet_count": count, "avg_packet_size_threshold": small_packet_threshold}
                        })

            # Rule 2: Unusually high traffic volume to a single destination might warrant investigation.
            if 'destination_ip' in df.columns:
                dest_counts = df['destination_ip'].value_counts()
                if not dest_counts.empty:
                    total_packets = len(df)
                    high_volume_threshold = total_packets * 0.1  # Example: more than 10% of total traffic
                    high_volume_dests = dest_counts[dest_counts > high_volume_threshold]
                    for ip, count in high_volume_dests.items():
                        self.recommendations.append({
                            "type": "Optimization",
                            "area": "Bandwidth Management",
                            "description": f"Destination IP {ip} receives a disproportionately high volume of traffic ({count} packets, {count/total_packets:.1%}). Investigate for potential bottlenecks or misconfigurations.",
                            "details": {"target_ip": ip, "packet_count": count, "percentage_of_total": count/total_packets}
                        })

            # Rule 3: Identify unused or rarely used ports.
            if 'port' in df.columns:
                port_counts = df['port'].value_counts()
                rare_port_threshold = len(df) * 0.001 # Example: less than 0.1% of traffic
                rare_ports = port_counts[port_counts < rare_port_threshold]
                for port, count in rare_ports.items():
                    self.recommendations.append({
                        "type": "Optimization",
                        "area": "Port Management",
                        "description": f"Port {port} is rarely used ({count} packets detected). Consider disabling or reallocating if not essential.",
                        "details": {"port": port, "packet_count": count}
                    })

            logging.info(f"Generated {len(self.recommendations)} optimization recommendations.")
            return {"success": True, "recommendations": self.recommendations, "message": "Optimization recommendations generated."}

        except KeyError as e:
            logging.error(f"Missing expected column for optimization analysis: {e}")
            return {"success": False, "error": f"Missing expected column for optimization analysis: {e}. Ensure relevant columns exist."}
        except Exception as e:
            logging.error(f"An error occurred during optimization recommendation generation: {e}")
            return {"success": False, "error": f"An unexpected error occurred during optimization recommendation generation: {str(e)}"}

    def analyze_security_considerations(self) -> Dict[str, Any]:
        """
        Analyzes network traffic for potential security threats and generates alerts.
        This is a rule-based simulation. Real security analysis requires advanced techniques.
        """
        if self.traffic_data is None:
            return {"success": False, "error": "No network traffic data loaded. Use 'load_traffic_log' first."}

        self.security_alerts = []
        df = self.traffic_data.copy()

        try:
            # Security Rule 1: High frequency of connection attempts from a single source (potential brute-force/DoS).
            if 'source_ip' in df.columns and 'timestamp' in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                    time_window_seconds = 60  # Look for attempts within a 60-second window
                    source_counts = df.groupby('source_ip')['timestamp'].apply(
                        lambda x: (x.diff().dt.total_seconds() < time_window_seconds).sum()
                    )
                    high_frequency_sources = source_counts[source_counts > 50] # Example threshold: > 50 attempts in a short window
                    for ip, count in high_frequency_sources.items():
                        self.security_alerts.append({
                            "type": "Security Alert",
                            "severity": "High",
                            "category": "Suspicious Activity",
                            "description": f"Source IP {ip} shows a high rate of connection attempts ({count} within a short window). Potential brute-force or DoS attack.",
                            "details": {"source_ip": ip, "attempt_count": count, "time_window_seconds": time_window_seconds}
                        })
                else:
                    logging.warning("Timestamp column not suitable for time-based security analysis.")

            # Security Rule 2: Access to known sensitive ports from unexpected sources (e.g., external IPs to management ports).
            if 'source_ip' in df.columns and 'destination_ip' in df.columns and 'port' in df.columns:
                sensitive_ports = {22, 23, 3389, 8080, 5900}  # SSH, Telnet, RDP, common proxy, VNC
                external_sources = df[~df['source_ip'].isin(['127.0.0.1', '::1'])] # Exclude localhost
                sensitive_access = external_sources[external_sources['port'].isin(sensitive_ports)]

                if not sensitive_access.empty:
                    for index, row in sensitive_access.head(10).iterrows(): # Report first 10 instances
                        self.security_alerts.append({
                            "type": "Security Alert",
                            "severity": "Medium",
                            "category": "Unauthorized Access Attempt",
                            "description": f"External source {row['source_ip']} attempted to access sensitive port {row['port']} on {row['destination_ip']}.",
                            "details": {"source_ip": row['source_ip'], "destination_ip": row['destination_ip'], "port": row['port']}
                        })

            # Security Rule 3: Unusual protocol usage (e.g., excessive UDP to non-standard ports).
            if 'protocol' in df.columns and 'port' in df.columns:
                udp_traffic = df[df['protocol'].str.lower() == 'udp']
                unusual_udp_ports = {80, 443} # Ports typically for TCP
                if not udp_traffic.empty:
                    for port in unusual_udp_ports:
                        count = udp_traffic[udp_traffic['port'] == port].shape[0]
                        if count > 10: # Example threshold
                            self.security_alerts.append({
                                "type": "Security Alert",
                                "severity": "Low",
                                "category": "Anomalous Traffic",
                                "description": f"High volume of UDP traffic detected on port {port} ({count} packets), typically used for TCP. Investigate for potential misuse.",
                                "details": {"port": port, "protocol": "UDP", "packet_count": count}
                            })

            logging.info(f"Generated {len(self.security_alerts)} security alerts.")
            return {"success": True, "alerts": self.security_alerts, "message": "Security analysis completed."}

        except KeyError as e:
            logging.error(f"Missing expected column for security analysis: {e}")
            return {"success": False, "error": f"Missing expected column for security analysis: {e}. Ensure relevant columns exist."}
        except Exception as e:
            logging.error(f"An error occurred during security analysis: {e}")
            return {"success": False, "error": f"An unexpected error occurred during security analysis: {str(e)}"}

    def get_recommendations_and_alerts(self) -> Dict[str, Any]:
        """Returns all generated recommendations and alerts."""
        return {
            "success": True,
            "recommendations": self.recommendations,
            "alerts": self.security_alerts,
            "message": "Retrieved all generated recommendations and alerts."
        }

    def clear_data_and_results(self) -> Dict[str, Any]:
        """Clears loaded data and any generated recommendations/alerts."""
        self.traffic_data = None
        self.recommendations = []
        self.security_alerts = []
        logging.info("Cleared loaded data, recommendations, and alerts.")
        return {"success": True, "message": "Data and results have been cleared."}

# Example Usage (for demonstration, not part of the tool class itself):
if __name__ == "__main__":
    analyzer = NetworkTrafficAnalyzer()

    # Create a dummy CSV for testing
    dummy_data = {
        'timestamp': [
            datetime.now() - pd.Timedelta(seconds=i*5) for i in range(200)
        ],
        'source_ip': ['192.168.1.10'] * 50 + ['10.0.0.5'] * 100 + ['192.168.1.20'] * 50,
        'destination_ip': ['8.8.8.8'] * 70 + ['192.168.1.1'] * 100 + ['10.0.0.1'] * 30,
        'protocol': ['TCP'] * 150 + ['UDP'] * 50,
        'port': [80] * 60 + [443] * 90 + [53] * 30 + [8080] * 20,
        'packet_size': [60] * 100 + [1500] * 50 + [32] * 50,
        'flags': ['SYN'] * 100 + ['ACK'] * 100
    }
    # Add some specific patterns for testing rules
    # Brute force simulation
    for i in range(60):
        dummy_data['timestamp'].append(datetime.now() - pd.Timedelta(seconds=i*0.5))
        dummy_data['source_ip'].append('172.16.0.100')
        dummy_data['destination_ip'].append('192.168.1.50')
        dummy_data['protocol'].append('TCP')
        dummy_data['port'].append(22)
        dummy_data['packet_size'].append(64)
        dummy_data['flags'].append('SYN')

    # High volume to one destination
    for i in range(80):
        dummy_data['timestamp'].append(datetime.now() - pd.Timedelta(seconds=i*2))
        dummy_data['source_ip'].append('192.168.1.200')
        dummy_data['destination_ip'].append('192.168.1.1') # Internal server
        dummy_data['protocol'].append('TCP')
        dummy_data['port'].append(80)
        dummy_data['packet_size'].append(1500)
        dummy_data['flags'].append('ACK')

    # Unusual UDP
    for i in range(20):
        dummy_data['timestamp'].append(datetime.now() - pd.Timedelta(seconds=i*10))
        dummy_data['source_ip'].append('10.10.10.10')
        dummy_data['destination_ip'].append('8.8.4.4')
        dummy_data['protocol'].append('UDP')
        dummy_data['port'].append(443) # Standard HTTPS port, but UDP
        dummy_data['packet_size'].append(500)
        dummy_data['flags'].append('')


    df_dummy = pd.DataFrame(dummy_data)
    dummy_filepath = "dummy_network_traffic.csv"
    df_dummy.to_csv(dummy_filepath, index=False)

    print(f"--- Loading data from {dummy_filepath} ---")
    load_result = analyzer.load_traffic_log(dummy_filepath)
    print(json.dumps(load_result, indent=2))

    if load_result["success"]:
        print("\n--- Analyzing traffic patterns ---")
        analysis_result = analyzer.analyze_traffic_patterns()
        print(json.dumps(analysis_result, indent=2))

        print("\n--- Generating optimization recommendations ---")
        optimization_result = analyzer.generate_optimization_recommendations()
        print(json.dumps(optimization_result, indent=2))

        print("\n--- Analyzing security considerations ---")
        security_result = analyzer.analyze_security_considerations()
        print(json.dumps(security_result, indent=2))

        print("\n--- Getting all recommendations and alerts ---")
        all_results = analyzer.get_recommendations_and_alerts()
        print(json.dumps(all_results, indent=2))

    print("\n--- Clearing data ---")
    clear_result = analyzer.clear_data_and_results()
    print(json.dumps(clear_result, indent=2))

    print("\n--- Attempting analysis after clearing ---")
    print(analyzer.analyze_traffic_patterns())
