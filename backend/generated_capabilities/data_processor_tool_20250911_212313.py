
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
    recommendations with security considerations.

    NOTE: This class serves as a foundational structure. Actual network packet
    capture, deep analysis, and advanced security recommendations require
    specialized libraries (like scapy, pyshark) and domain expertise,
    which are beyond the scope of this foundational implementation.
    """

    def __init__(self):
        self.traffic_data: Optional[pd.DataFrame] = None
        self.supported_protocols = ["TCP", "UDP", "ICMP", "HTTP", "HTTPS", "DNS"]
        self.security_risk_thresholds = {
            "high_bandwidth_usage": 1000000,  # e.g., 1 Mbps in bytes/sec
            "excessive_connections": 50,  # e.g., connections per second from one source
            "suspicious_ports": [21, 22, 23, 25, 135, 137, 138, 139, 445, 3389],
            "unusual_protocol_mix": 0.8 # e.g., >80% of traffic is non-standard protocols
        }

    def load_traffic_data_from_csv(self, filepath: str) -> Dict[str, Any]:
        """
        Load network traffic data from a CSV file.

        Expected CSV columns: 'timestamp', 'source_ip', 'destination_ip',
                              'source_port', 'destination_port', 'protocol',
                              'packet_size', 'flags' (optional, for TCP)

        Args:
            filepath: The path to the CSV file.

        Returns:
            A dictionary containing the status of the operation, including
            success, number of rows, columns, sample data, and a message.
        """
        logging.info(f"Attempting to load network traffic data from: {filepath}")
        if not isinstance(filepath, str) or not filepath.lower().endswith('.csv'):
            logging.error("Invalid filepath provided. Must be a string ending with .csv")
            return {"success": False, "error": "Invalid filepath. Must be a string ending with .csv"}

        try:
            df = pd.read_csv(filepath)
            self.traffic_data = df

            # Basic validation of required columns
            required_columns = ['timestamp', 'source_ip', 'destination_ip', 'source_port', 'destination_port', 'protocol', 'packet_size']
            if not all(col in df.columns for col in required_columns):
                missing = [col for col in required_columns if col not in df.columns]
                error_msg = f"CSV file is missing required columns: {', '.join(missing)}. Found columns: {', '.join(df.columns)}"
                logging.error(error_msg)
                return {"success": False, "error": error_msg}

            # Convert timestamp to datetime if it exists
            if 'timestamp' in df.columns:
                try:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                except Exception as e:
                    logging.warning(f"Could not convert 'timestamp' column to datetime: {e}. Proceeding without datetime conversion.")

            logging.info(f"Successfully loaded {len(df)} rows from {filepath}")
            return {
                "success": True,
                "rows": len(df),
                "columns": list(df.columns),
                "sample_data": df.head().to_dict('records'),
                "message": f"Loaded {len(df)} rows from {filepath}"
            }
        except FileNotFoundError:
            logging.error(f"File not found at: {filepath}")
            return {"success": False, "error": f"File not found at: {filepath}"}
        except pd.errors.EmptyDataError:
            logging.error(f"The file {filepath} is empty.")
            return {"success": False, "error": f"The file {filepath} is empty."}
        except Exception as e:
            logging.error(f"An error occurred while loading {filepath}: {e}")
            return {"success": False, "error": f"An error occurred while loading {filepath}: {e}"}

    def analyze_traffic_patterns(self) -> Dict[str, Any]:
        """
        Performs basic analysis on loaded network traffic data.
        Identifies potential areas for optimization and security concerns.

        Returns:
            A dictionary containing analysis results, optimization suggestions,
            and security alerts.
        """
        logging.info("Starting network traffic pattern analysis.")
        if self.traffic_data is None:
            logging.error("No traffic data loaded for analysis.")
            return {"success": False, "error": "No traffic data loaded"}

        df = self.traffic_data.copy()
        analysis_results = {}
        optimization_recommendations = []
        security_alerts = []

        try:
            # --- Basic Data Profiling ---
            analysis_results["data_profile"] = {
                "shape": df.shape,
                "columns": list(df.columns),
                "data_types": df.dtypes.apply(lambda x: x.name).to_dict(),
                "missing_values": df.isnull().sum().to_dict(),
            }
            if len(df.select_dtypes(include='number').columns) > 0:
                analysis_results["numeric_summary"] = df.describe().to_dict()

            # --- Traffic Volume Analysis ---
            total_traffic = df['packet_size'].sum()
            analysis_results["total_traffic_bytes"] = int(total_traffic)
            analysis_results["average_packet_size"] = int(df['packet_size'].mean()) if not df.empty else 0

            # --- Protocol Distribution ---
            protocol_counts = df['protocol'].value_counts()
            analysis_results["protocol_distribution"] = protocol_counts.to_dict()

            uncommon_protocols = protocol_counts[~protocol_counts.index.isin(self.supported_protocols)]
            if not uncommon_protocols.empty:
                uncommon_ratio = uncommon_protocols.sum() / len(df)
                if uncommon_ratio > 0.1: # Threshold for considering a significant amount of uncommon protocols
                    security_alerts.append({
                        "type": "Unusual Protocol Mix",
                        "description": f"Detected a significant amount of non-standard protocols ({uncommon_ratio:.1%}). "
                                       f"Consider investigating protocols: {', '.join(uncommon_protocols.index.tolist())}",
                        "severity": "medium"
                    })
                    optimization_recommendations.append(
                        "Investigate the use of non-standard protocols. They might indicate legacy systems, misconfigurations, or potential security risks."
                    )

            # --- Top Communicating Hosts ---
            source_ip_counts = df['source_ip'].value_counts().head(5)
            destination_ip_counts = df['destination_ip'].value_counts().head(5)
            analysis_results["top_source_ips"] = source_ip_counts.to_dict()
            analysis_results["top_destination_ips"] = destination_ip_counts.to_dict()

            # --- Bandwidth Usage per Host (Approximate) ---
            # This is a simplified approach. True bandwidth per host would need time series analysis.
            bandwidth_per_source = df.groupby('source_ip')['packet_size'].sum().sort_values(ascending=False)
            bandwidth_per_destination = df.groupby('destination_ip')['packet_size'].sum().sort_values(ascending=False)

            analysis_results["bandwidth_per_source_bytes"] = bandwidth_per_source.to_dict()
            analysis_results["bandwidth_per_destination_bytes"] = bandwidth_per_destination.to_dict()

            for ip, bw in bandwidth_per_source.items():
                if bw > self.security_risk_thresholds["high_bandwidth_usage"]:
                    security_alerts.append({
                        "type": "High Bandwidth Consumption",
                        "source_ip": ip,
                        "bandwidth_bytes": int(bw),
                        "description": f"Source IP {ip} is consuming excessive bandwidth ({bw} bytes).",
                        "severity": "high"
                    })
                    optimization_recommendations.append(
                        f"Optimize network traffic from source IP {ip} which is consuming high bandwidth. Consider QOS, traffic shaping, or identifying the source of large data transfers."
                    )

            # --- Port Usage Analysis ---
            suspicious_source_ports = df[df['source_port'].isin(self.security_risk_thresholds["suspicious_ports"])]['source_port'].value_counts()
            suspicious_destination_ports = df[df['destination_port'].isin(self.security_risk_thresholds["suspicious_ports"])]['destination_port'].value_counts()

            if not suspicious_source_ports.empty:
                for port, count in suspicious_source_ports.items():
                    security_alerts.append({
                        "type": "Suspicious Port Usage",
                        "port": int(port),
                        "direction": "source",
                        "count": int(count),
                        "description": f"Detected {count} outgoing connections on suspicious source port {port}.",
                        "severity": "medium"
                    })
                    optimization_recommendations.append(
                        f"Investigate outgoing traffic on suspicious source port {port}. Ensure it's necessary and properly secured."
                    )

            if not suspicious_destination_ports.empty:
                for port, count in suspicious_destination_ports.items():
                    security_alerts.append({
                        "type": "Suspicious Port Usage",
                        "port": int(port),
                        "direction": "destination",
                        "count": int(count),
                        "description": f"Detected {count} incoming connections on suspicious destination port {port}.",
                        "severity": "medium"
                    })
                    optimization_recommendations.append(
                        f"Investigate incoming traffic on suspicious destination port {port}. Ensure necessary firewall rules are in place and the service is secure."
                    )

            # --- Connection Frequency (Simplified per second - requires timestamp) ---
            if 'timestamp' in df.columns and pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df_sorted_by_time = df.sort_values('timestamp')
                df_sorted_by_time['time_diff'] = df_sorted_by_time.groupby(['source_ip', 'destination_ip'])['timestamp'].diff().dt.total_seconds()

                # Count connections within a 1-second window per source IP
                connections_per_second_per_ip = df_sorted_by_time.groupby('source_ip').apply(
                    lambda x: (x['time_diff'] <= 1).sum()
                )
                for ip, count in connections_per_second_per_ip.items():
                    if count > self.security_risk_thresholds["excessive_connections"]:
                        security_alerts.append({
                            "type": "Excessive Connection Rate",
                            "source_ip": ip,
                            "connections_per_second": int(count),
                            "description": f"Source IP {ip} is making an excessive number of connections ({count} within a second).",
                            "severity": "high"
                        })
                        optimization_recommendations.append(
                            f"Investigate source IP {ip} for potential brute-force attacks or network misconfigurations causing excessive connections."
                        )

            # --- Recommendations based on basic analysis ---
            if not optimization_recommendations:
                optimization_recommendations.append("No immediate optimization recommendations based on current analysis. Monitor traffic for changes.")
            if not security_alerts:
                security_alerts.append("No critical security alerts triggered based on current analysis. Continuous monitoring is advised.")

            logging.info(f"Analysis complete. Found {len(security_alerts)} security alerts and {len(optimization_recommendations)} recommendations.")
            return {
                "success": True,
                "analysis_summary": analysis_results,
                "optimization_recommendations": list(set(optimization_recommendations)), # Remove duplicates
                "security_alerts": security_alerts,
                "message": "Network traffic analysis completed."
            }

        except Exception as e:
            logging.error(f"An unexpected error occurred during traffic analysis: {e}")
            return {"success": False, "error": f"An unexpected error occurred during traffic analysis: {e}"}

    def generate_report(self, analysis_results: Dict[str, Any], output_format: str = "json") -> Dict[str, Any]:
        """
        Generates a report from the analysis results.

        Args:
            analysis_results: The dictionary containing analysis results,
                              recommendations, and alerts.
            output_format: The desired output format ('json', 'csv', 'text').

        Returns:
            A dictionary containing the report content and status.
        """
        logging.info(f"Generating report in format: {output_format}")
        if not isinstance(analysis_results, dict) or not analysis_results.get("success"):
            return {"success": False, "error": "Invalid analysis results provided."}

        report_content = ""
        filename_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            if output_format.lower() == "json":
                report_content = json.dumps(analysis_results, indent=4)
                filename = f"network_traffic_report_{filename_suffix}.json"
                return {"success": True, "report_content": report_content, "filename": filename, "message": "JSON report generated."}

            elif output_format.lower() == "csv":
                # For CSV, we'll create a more structured output, focusing on alerts and recommendations
                report_data = []
                if "security_alerts" in analysis_results:
                    for alert in analysis_results["security_alerts"]:
                        report_data.append({"type": "Security Alert", **alert})
                if "optimization_recommendations" in analysis_results:
                    for i, rec in enumerate(analysis_results["optimization_recommendations"]):
                        report_data.append({"type": "Optimization Recommendation", "id": i+1, "recommendation": rec})

                if not report_data:
                    report_content = "No security alerts or optimization recommendations to report in CSV format."
                    filename = f"network_traffic_report_{filename_suffix}.txt"
                    return {"success": True, "report_content": report_content, "filename": filename, "message": "No data for CSV report."}

                df_report = pd.DataFrame(report_data)
                # Convert DataFrame to CSV string
                report_content = df_report.to_csv(index=False)
                filename = f"network_traffic_report_{filename_suffix}.csv"
                return {"success": True, "report_content": report_content, "filename": filename, "message": "CSV report generated."}

            elif output_format.lower() == "text":
                report_lines = ["--- Network Traffic Analysis Report ---", f"Generated on: {datetime.now().isoformat()}\n"]

                if "analysis_summary" in analysis_results:
                    report_lines.append("--- Data Profile ---")
                    profile = analysis_results["analysis_summary"]
                    report_lines.append(f"  Shape: {profile.get('shape')}")
                    report_lines.append(f"  Columns: {', '.join(profile.get('columns', []))}")
                    report_lines.append(f"  Data Types: {json.dumps(profile.get('data_types', {}))}")
                    report_lines.append(f"  Missing Values: {json.dumps(profile.get('missing_values', {}))}")
                    if profile.get("numeric_summary"):
                        report_lines.append("  Numeric Summary:")
                        for col, desc in profile["numeric_summary"].items():
                            report_lines.append(f"    {col}: {json.dumps(desc)}")
                    report_lines.append(f"  Total Traffic: {analysis_results['analysis_summary'].get('total_traffic_bytes', 'N/A')} bytes")
                    report_lines.append(f"  Average Packet Size: {analysis_results['analysis_summary'].get('average_packet_size', 'N/A')} bytes")
                    report_lines.append(f"  Protocol Distribution: {json.dumps(analysis_results['analysis_summary'].get('protocol_distribution', {}))}\n")

                if "security_alerts" in analysis_results and analysis_results["security_alerts"]:
                    report_lines.append("--- Security Alerts ---")
                    for i, alert in enumerate(analysis_results["security_alerts"]):
                        report_lines.append(f"  {i+1}. Type: {alert.get('type', 'N/A')}, Severity: {alert.get('severity', 'N/A')}")
                        for key, value in alert.items():
                            if key not in ['type', 'severity']:
                                report_lines.append(f"     {key.capitalize()}: {value}")
                        report_lines.append("")
                else:
                    report_lines.append("--- Security Alerts ---\n  No security alerts detected.\n")

                if "optimization_recommendations" in analysis_results and analysis_results["optimization_recommendations"]:
                    report_lines.append("--- Optimization Recommendations ---")
                    for i, rec in enumerate(analysis_results["optimization_recommendations"]):
                        report_lines.append(f"  {i+1}. {rec}")
                else:
                    report_lines.append("--- Optimization Recommendations ---\n  No specific optimization recommendations found.\n")

                report_content = "\n".join(report_lines)
                filename = f"network_traffic_report_{filename_suffix}.txt"
                return {"success": True, "report_content": report_content, "filename": filename, "message": "Text report generated."}

            else:
                logging.error(f"Unsupported output format: {output_format}")
                return {"success": False, "error": f"Unsupported output format: {output_format}. Please choose from 'json', 'csv', or 'text'."}

        except Exception as e:
            logging.error(f"An error occurred during report generation: {e}")
            return {"success": False, "error": f"An error occurred during report generation: {e}"}

# Example Usage (for demonstration, not part of the final tool code structure unless invoked)
if __name__ == '__main__':
    # Create a dummy CSV for testing
    dummy_data = {
        'timestamp': [
            '2023-10-27 10:00:01', '2023-10-27 10:00:02', '2023-10-27 10:00:03',
            '2023-10-27 10:00:03', '2023-10-27 10:00:04', '2023-10-27 10:00:05',
            '2023-10-27 10:00:05', '2023-10-27 10:00:06', '2023-10-27 10:00:07',
            '2023-10-27 10:00:08'
        ],
        'source_ip': [
            '192.168.1.100', '192.168.1.100', '192.168.1.101', '192.168.1.102',
            '192.168.1.100', '192.168.1.103', '192.168.1.101', '192.168.1.100',
            '192.168.1.104', '192.168.1.102'
        ],
        'destination_ip': [
            '8.8.8.8', '8.8.8.8', '192.168.1.200', '10.0.0.5',
            '8.8.8.8', '192.168.1.201', '8.8.8.8', '10.0.0.5',
            '8.8.8.8', '192.168.1.202'
        ],
        'source_port': [
            54321, 54322, 12345, 6789,
            54323, 9876, 12346, 54324,
            56789, 6790
        ],
        'destination_port': [
            80, 443, 8080, 22,
            53, 80, 443, 22,
            80, 22
        ],
        'protocol': [
            'TCP', 'TCP', 'HTTP', 'TCP',
            'UDP', 'TCP', 'HTTPS', 'TCP',
            'TCP', 'TCP'
        ],
        'packet_size': [
            150, 200, 500, 1000,
            60, 180, 300, 1200,
            170, 1100
        ],
        'flags': [ # Example for TCP flags
            'S', 'A', None, 'P',
            None, 'A', 'S', 'P',
            'A', 'P'
        ]
    }
    df_dummy = pd.DataFrame(dummy_data)
    dummy_filepath = "dummy_traffic_data.csv"
    df_dummy.to_csv(dummy_filepath, index=False)
    print(f"Created dummy data file: {dummy_filepath}\n")

    analyzer = NetworkTrafficAnalyzer()

    # Load data
    load_result = analyzer.load_traffic_data_from_csv(dummy_filepath)
    print("Load Data Result:", json.dumps(load_result, indent=2))
    print("-" * 30)

    if load_result["success"]:
        # Analyze data
        analysis_result = analyzer.analyze_traffic_patterns()
        print("Analysis Result:", json.dumps(analysis_result, indent=2))
        print("-" * 30)

        # Generate reports
        if analysis_result["success"]:
            json_report = analyzer.generate_report(analysis_result, output_format="json")
            print(f"JSON Report Filename: {json_report.get('filename')}")
            # print(f"JSON Report Content:\n{json_report.get('report_content')}\n")

            csv_report = analyzer.generate_report(analysis_result, output_format="csv")
            print(f"CSV Report Filename: {csv_report.get('filename')}")
            # print(f"CSV Report Content:\n{csv_report.get('report_content')}\n")

            text_report = analyzer.generate_report(analysis_result, output_format="text")
            print(f"Text Report Filename: {text_report.get('filename')}")
            print(f"Text Report Content:\n{text_report.get('report_content')}\n")
        else:
            print("Analysis failed, cannot generate report.")
    else:
        print("Data loading failed, cannot proceed with analysis.")
