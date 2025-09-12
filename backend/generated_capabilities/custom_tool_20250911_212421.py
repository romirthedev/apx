
import json
from typing import Dict, Any, List, Optional

class ComplianceAuditTool:
    """
    A specialized Python tool class for generating comprehensive compliance audit reports
    with regulatory requirements and gap analysis.

    This tool aims to bridge the gap by simulating the understanding and interpretation
    of regulatory requirements and performing an audit against them. It relies on structured
    input data for compliance controls and regulatory frameworks to perform the analysis.
    It's designed to be extensible for more complex scenarios.
    """

    def __init__(self):
        """
        Initializes the ComplianceAuditTool.
        """
        pass

    def generate_audit_report(
        self,
        compliance_data: Dict[str, Any],
        regulatory_frameworks: Dict[str, Any],
        assessment_scope: str = "All"
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive compliance audit report, including regulatory
        requirements and a detailed gap analysis.

        Args:
            compliance_data: A dictionary containing current compliance status
                             and evidence for internal controls. Expected structure:
                             {
                                 "controls": [
                                     {
                                         "id": "string",         # Unique identifier for the control
                                         "name": "string",       # Human-readable name of the control
                                         "description": "string",# Detailed description of the control
                                         "status": "Compliant" | "Non-Compliant" | "Partially Compliant" | "Not Applicable", # Current status
                                         "evidence": "string"    # Documentation or proof of compliance
                                     },
                                     ...
                                 ]
                             }
            regulatory_frameworks: A dictionary defining regulatory requirements and their mapping
                                   to internal controls. Expected structure:
                                   {
                                       "FrameworkName": {
                                           "description": "string", # Description of the framework
                                           "controls": [
                                               {
                                                   "id": "string",        # Unique identifier for the regulatory requirement
                                                   "name": "string",      # Human-readable name of the regulatory requirement
                                                   "description": "string", # Detailed description of the requirement
                                                   "mapped_controls": ["string"] # List of internal control IDs that address this requirement
                                               },
                                               ...
                                           ]
                                       }
                                   }
            assessment_scope: A string specifying the scope of the assessment (e.g., "All", "Network", "Data").
                              This parameter is currently informational and can be used for future filtering/segmentation.

        Returns:
            A dictionary containing the audit report and gap analysis.
            Example:
            {
                "success": True,
                "message": "Audit report generated successfully.",
                "report": {
                    "assessment_scope": "string",
                    "overall_compliance_status": "Compliant" | "Partial" | "Non-Compliant" | "No data to assess",
                    "framework_compliance": {
                        "FrameworkName": {
                            "description": "string",
                            "compliance_status": "Compliant" | "Partial" | "Non-Compliant",
                            "gaps": [
                                {
                                    "regulatory_requirement_id": "string",
                                    "regulatory_requirement_name": "string",
                                    "description": "string",
                                    "unmapped_compliance_controls_for_this_req": ["string"], # Compliance controls not mapped to this specific req
                                    "compliance_status": "Non-Compliant" | "Partially Compliant",
                                    "recommendations": ["string"]
                                },
                                ...
                            ]
                        }
                    },
                    "unmapped_compliance_controls": [
                        {
                            "control_id": "string",
                            "control_name": "string",
                            "description": "string",
                            "status": "Compliant" | "Non-Compliant" | "Partially Compliant" | "Not Applicable",
                            "recommendations": ["string"]
                        },
                        ...
                    ],
                    "summary": {
                        "total_regulatory_requirements_assessed": int,
                        "total_gaps_identified": int,
                        "compliant_frameworks": int,
                        "partially_compliant_frameworks": int,
                        "non_compliant_frameworks": int,
                        "unmapped_controls_count": int
                    }
                }
            }
        """
        try:
            # --- Input Validation ---
            if not isinstance(compliance_data, dict) or not self._validate_input_data(compliance_data, ["controls"]):
                return {"success": False, "message": "Invalid 'compliance_data' format. Expected a dictionary with a 'controls' key."}
            if not isinstance(compliance_data["controls"], list):
                return {"success": False, "message": "Invalid 'compliance_data'. 'controls' must be a list."}

            if not isinstance(regulatory_frameworks, dict) or not regulatory_frameworks:
                return {"success": False, "message": "Invalid or empty 'regulatory_frameworks' provided. This is required for a compliance audit."}
            for framework_name, framework_details in regulatory_frameworks.items():
                if not isinstance(framework_details, dict) or not self._validate_input_data(framework_details, ["controls", "description"]):
                    return {"success": False, "message": f"Invalid format for regulatory framework '{framework_name}'. Missing 'controls' or 'description'."}
                if not isinstance(framework_details["controls"], list):
                    return {"success": False, "message": f"Invalid format for regulatory framework '{framework_name}'. 'controls' must be a list."}

            # --- Data Preparation ---
            compliance_control_map: Dict[str, Dict[str, Any]] = {}
            for control in compliance_data.get("controls", []):
                if not isinstance(control, dict) or not self._validate_input_data(control, ["id", "name", "description", "status"]):
                    print(f"Warning: Skipping malformed compliance control: {control}")
                    continue
                if control["id"] in compliance_control_map:
                    print(f"Warning: Duplicate compliance control ID found: {control['id']}. Using the first encountered.")
                    continue
                compliance_control_map[control["id"]] = control

            # --- Audit Report Generation ---
            audit_report: Dict[str, Any] = {
                "assessment_scope": assessment_scope,
                "overall_compliance_status": "Compliant", # Default to Compliant
                "framework_compliance": {},
                "unmapped_compliance_controls": [],
                "summary": {
                    "total_regulatory_requirements_assessed": 0,
                    "total_gaps_identified": 0,
                    "compliant_frameworks": 0,
                    "partially_compliant_frameworks": 0,
                    "non_compliant_frameworks": 0,
                    "unmapped_controls_count": 0
                }
            }

            all_mapped_compliance_control_ids_in_frameworks = set()

            # Iterate through each regulatory framework
            for framework_name, framework_details in regulatory_frameworks.items():
                framework_compliance_status = "Compliant"
                framework_gaps: List[Dict[str, Any]] = []

                framework_req_count = len(framework_details.get("controls", []))
                audit_report["summary"]["total_regulatory_requirements_assessed"] += framework_req_count

                # Iterate through each regulatory control (requirement) within the framework
                for reg_control in framework_details.get("controls", []):
                    reg_control_id = reg_control.get("id")
                    reg_control_name = reg_control.get("name", "Unnamed Regulatory Control")
                    reg_control_description = reg_control.get("description", "")
                    mapped_compliance_control_ids = reg_control.get("mapped_controls", [])

                    is_regulatory_requirement_met = True
                    unmet_mapped_controls_for_this_req = []

                    # Track all compliance controls that are mapped to ANY regulatory requirement
                    all_mapped_compliance_control_ids_in_frameworks.update(mapped_compliance_control_ids)

                    if not mapped_compliance_control_ids:
                        # This regulatory requirement has no mapped internal controls
                        is_regulatory_requirement_met = False
                        audit_report["summary"]["total_gaps_identified"] += 1
                        framework_gaps.append({
                            "regulatory_requirement_id": reg_control_id,
                            "regulatory_requirement_name": reg_control_name,
                            "description": reg_control_description,
                            "unmapped_compliance_controls_for_this_req": [], # None found
                            "compliance_status": "Non-Compliant",
                            "recommendations": [f"No internal controls are mapped to this regulatory requirement. Please map relevant controls or implement new ones to satisfy '{reg_control_name}'."]
                        })
                    else:
                        # Check the status of the mapped internal compliance controls
                        for mapped_id in mapped_compliance_control_ids:
                            compliance_control = compliance_control_map.get(mapped_id)
                            if not compliance_control:
                                unmet_mapped_controls_for_this_req.append(f"{mapped_id} (Not Found)")
                                is_regulatory_requirement_met = False
                            elif compliance_control.get("status") not in ["Compliant", "Not Applicable"]:
                                unmet_mapped_controls_for_this_req.append(f"{mapped_id} ({compliance_control.get('status', 'Unknown Status')})")
                                is_regulatory_requirement_met = False
                            # If compliance_control is "Compliant" or "Not Applicable", it's considered met for this mapping

                        if not is_regulatory_requirement_met:
                            audit_report["summary"]["total_gaps_identified"] += 1
                            recommendations = [f"Ensure compliance for mapped controls: {', '.join(unmet_mapped_controls_for_this_req)} to meet regulatory requirement '{reg_control_name}'."]
                            if "Not Found" in str(unmet_mapped_controls_for_this_req):
                                recommendations.append("Consider implementing or properly mapping the missing controls.")
                            framework_gaps.append({
                                "regulatory_requirement_id": reg_control_id,
                                "regulatory_requirement_name": reg_control_name,
                                "description": reg_control_description,
                                "unmapped_compliance_controls_for_this_req": unmet_mapped_controls_for_this_req,
                                "compliance_status": "Non-Compliant", # Simplified to Non-Compliant if any part is not met
                                "recommendations": recommendations
                            })

                # Update framework's overall compliance status and store gaps
                if framework_gaps:
                    framework_compliance_status = "Non-Compliant" # Assume non-compliant if any gaps exist
                    audit_report["summary"]["non_compliant_frameworks"] += 1
                else:
                    framework_compliance_status = "Compliant"
                    audit_report["summary"]["compliant_frameworks"] += 1

                audit_report["framework_compliance"][framework_name] = {
                    "description": framework_details.get("description", "No description"),
                    "compliance_status": framework_compliance_status,
                    "gaps": framework_gaps
                }

            # --- Identify Compliance Controls Not Mapped to Any Regulatory Requirement ---
            for control_id, control_data in compliance_control_map.items():
                if control_id not in all_mapped_compliance_control_ids_in_frameworks:
                    recommendations = ["This internal control is not mapped to any regulatory requirement. Please map it to relevant requirements or reassess its necessity and document the rationale."]
                    if control_data.get("status") != "Compliant":
                        recommendations.append(f"This control is also '{control_data.get('status', 'Unknown')}' and may require attention.")
                        audit_report["summary"]["total_gaps_identified"] += 1
                    else:
                        # Even compliant controls not mapped might be flagged for review
                        pass

                    audit_report["unmapped_compliance_controls"].append({
                        "control_id": control_id,
                        "control_name": control_data.get("name", "Unnamed Compliance Control"),
                        "description": control_data.get("description", ""),
                        "status": control_data.get("status", "Unknown"),
                        "recommendations": recommendations
                    })
            audit_report["summary"]["unmapped_controls_count"] = len(audit_report["unmapped_compliance_controls"])


            # --- Final Overall Status Calculation ---
            all_framework_statuses = [fw_status["compliance_status"] for fw_status in audit_report["framework_compliance"].values()]

            if not audit_report["framework_compliance"] and not audit_report["unmapped_compliance_controls"]:
                audit_report["overall_compliance_status"] = "No data to assess"
            elif "Non-Compliant" in all_framework_statuses:
                audit_report["overall_compliance_status"] = "Non-Compliant"
            elif "Partial" in all_framework_statuses or audit_report["unmapped_compliance_controls"]:
                 # If any framework is partial, or there are unmapped controls, it's partial.
                 # (Note: current logic assigns Non-Compliant if any gap exists in a framework)
                 # Re-evaluating for Partial: If there are identified gaps in frameworks or unmapped controls.
                 if audit_report["summary"]["total_gaps_identified"] > 0:
                     audit_report["overall_compliance_status"] = "Partial"
                 else:
                     audit_report["overall_compliance_status"] = "Compliant" # Should not happen if gaps > 0
            else: # All frameworks are Compliant and no unmapped controls
                audit_report["overall_compliance_status"] = "Compliant"

            # Recalculate summary counts based on final statuses
            audit_report["summary"]["compliant_frameworks"] = sum(1 for fs in all_framework_statuses if fs == "Compliant")
            audit_report["summary"]["partially_compliant_frameworks"] = sum(1 for fs in all_framework_statuses if fs == "Partial") # This might need adjustment if frameworks are only marked Non-Compliant or Compliant
            audit_report["summary"]["non_compliant_frameworks"] = sum(1 for fs in all_framework_statuses if fs == "Non-Compliant")

            if not audit_report["framework_compliance"]: # If no frameworks were processed
                audit_report["summary"]["compliant_frameworks"] = 0
                audit_report["summary"]["partially_compliant_frameworks"] = 0
                audit_report["summary"]["non_compliant_frameworks"] = 0


            return {"success": True, "message": "Audit report generated successfully.", "report": audit_report}

        except Exception as e:
            # Enhanced error logging for debugging
            import traceback
            print(f"--- An unexpected error occurred during audit report generation ---")
            traceback.print_exc()
            print(f"Error message: {e}")
            return {"success": False, "message": f"An unexpected error occurred: {e}"}

    def _validate_input_data(self, data: Dict[str, Any], expected_keys: List[str]) -> bool:
        """
        Internal helper to validate if a dictionary contains expected keys.

        Args:
            data: The dictionary to validate.
            expected_keys: A list of keys that are expected to be present.

        Returns:
            True if all expected keys are present, False otherwise.
        """
        return all(key in data for key in expected_keys)

if __name__ == '__main__':
    # --- Example Usage ---
    tool = ComplianceAuditTool()

    # --- Sample Data ---
    sample_compliance_data = {
        "controls": [
            {
                "id": "C1",
                "name": "Strong Password Policy",
                "description": "Enforces complexity, length, and history for passwords.",
                "status": "Compliant",
                "evidence": "Password policy configured in Active Directory, audited quarterly."
            },
            {
                "id": "C2",
                "name": "Access Logging",
                "description": "Logs all access attempts to sensitive systems.",
                "status": "Compliant",
                "evidence": "Syslog server configured, logs retained for 1 year."
            },
            {
                "id": "C3",
                "name": "Firewall Configuration",
                "description": "Network firewall rules are reviewed and approved.",
                "status": "Non-Compliant",
                "evidence": "Last review was 18 months ago, pending approval."
            },
            {
                "id": "C4",
                "name": "Data Encryption",
                "description": "Sensitive data is encrypted at rest.",
                "status": "Compliant",
                "evidence": "Database uses TDE, all sensitive files are encrypted."
            },
            {
                "id": "C5",
                "name": "Vulnerability Scanning",
                "description": "Regular scanning for known vulnerabilities.",
                "status": "Compliant",
                "evidence": "Monthly scans performed, critical vulnerabilities remediated within 30 days."
            },
            {
                "id": "C6",
                "name": "Employee Training",
                "description": "Mandatory security awareness training for all employees.",
                "status": "Non-Compliant",
                "evidence": "Only 75% of employees completed training."
            },
             {
                "id": "C7", # This control is compliant but not mapped to any framework requirement
                "name": "Incident Response Plan",
                "description": "A documented and tested incident response plan.",
                "status": "Compliant",
                "evidence": "Plan documented and reviewed annually."
            }
        ]
    }

    sample_regulatory_frameworks = {
        "NIST_CSF": {
            "description": "National Institute of Standards and Technology Cybersecurity Framework",
            "controls": [
                {
                    "id": "R1_NIST",
                    "name": "Access Control Policy",
                    "description": "Access control policies are developed, documented, and disseminated.",
                    "mapped_controls": ["C1"] # C1 is Compliant
                },
                {
                    "id": "R2_NIST",
                    "name": "Audit Logging",
                    "description": "System and application audit logs are collected, protected, and reviewed.",
                    "mapped_controls": ["C2"] # C2 is Compliant
                },
                {
                    "id": "R3_NIST",
                    "name": "Network Segmentation",
                    "description": "Network traffic is segmented to prevent lateral movement.",
                    "mapped_controls": ["C3"] # C3 is Non-Compliant
                },
                {
                    "id": "R4_NIST",
                    "name": "Data Encryption",
                    "description": "Data is protected through encryption.",
                    "mapped_controls": ["C4"] # C4 is Compliant
                },
                {
                    "id": "R5_NIST",
                    "name": "Vulnerability Management",
                    "description": "Processes to identify, assess, and remediate vulnerabilities.",
                    "mapped_controls": ["C5", "C3"] # C5 is Compliant, C3 is Non-Compliant -> Partially Met/Non-Compliant for this req
                }
            ]
        },
        "GDPR": {
            "description": "General Data Protection Regulation",
            "controls": [
                {
                    "id": "R1_GDPR",
                    "name": "Data Minimisation",
                    "description": "Personal data collected shall be adequate, relevant and limited to what is necessary.",
                    "mapped_controls": [] # No direct compliance control mapped -> Gap
                },
                {
                    "id": "R2_GDPR",
                    "name": "Security of Processing",
                    "description": "Processing of personal data shall be done in a manner that ensures appropriate security.",
                    "mapped_controls": ["C4", "C2"] # C4 Compliant, C2 Compliant
                },
                {
                    "id": "R3_GDPR",
                    "name": "Regular Testing and Assessment",
                    "description": "Regularly test, assess and evaluate the effectiveness of technical and organisational measures for ensuring the security of the processing.",
                    "mapped_controls": ["C5", "C6"] # C5 Compliant, C6 Non-Compliant -> Partially Met/Non-Compliant for this req
                }
            ]
        },
        "HIPAA": {
            "description": "Health Insurance Portability and Accountability Act",
            "controls": [
                {
                    "id": "R1_HIPAA",
                    "name": "Access Controls",
                    "description": "Implement technical policies and procedures that grant access to electronic protected health information only to authorized users.",
                    "mapped_controls": ["C1", "C2"] # C1 Compliant, C2 Compliant
                },
                {
                    "id": "R2_HIPAA",
                    "name": "Security Awareness and Training",
                    "description": "Implement a security awareness and training program for all workforce members.",
                    "mapped_controls": ["C6"] # C6 Non-Compliant
                }
            ]
        }
    }

    # --- Test Case 1: Full Successful Report ---
    print("--- Test Case 1: Full Successful Report ---")
    report_result = tool.generate_audit_report(
        compliance_data=sample_compliance_data,
        regulatory_frameworks=sample_regulatory_frameworks,
        assessment_scope="Full Organization"
    )

    if report_result["success"]:
        print(json.dumps(report_result["report"], indent=4))
    else:
        print(f"Error generating report: {report_result['message']}")

    # --- Test Case 2: Empty Compliance Data ---
    print("\n--- Test Case 2: Empty Compliance Data ---")
    empty_compliance_result = tool.generate_audit_report(
        compliance_data={"controls": []},
        regulatory_frameworks=sample_regulatory_frameworks
    )
    print(json.dumps(empty_compliance_result, indent=4))

    # --- Test Case 3: Invalid Compliance Data (missing 'controls') ---
    print("\n--- Test Case 3: Invalid Compliance Data (missing 'controls') ---")
    invalid_compliance_data_result = tool.generate_audit_report(
        compliance_data={"some_other_key": []},
        regulatory_frameworks=sample_regulatory_frameworks
    )
    print(json.dumps(invalid_compliance_data_result, indent=4))

    # --- Test Case 4: Empty Regulatory Frameworks ---
    print("\n--- Test Case 4: Empty Regulatory Frameworks ---")
    empty_frameworks_result = tool.generate_audit_report(
        compliance_data=sample_compliance_data,
        regulatory_frameworks={}
    )
    print(json.dumps(empty_frameworks_result, indent=4))

    # --- Test Case 5: Invalid Regulatory Frameworks format ---
    print("\n--- Test Case 5: Invalid Regulatory Frameworks format ---")
    invalid_frameworks_format_result = tool.generate_audit_report(
        compliance_data=sample_compliance_data,
        regulatory_frameworks={"NIST_CSF": {"description": "Invalid"}} # Missing 'controls'
    )
    print(json.dumps(invalid_frameworks_format_result, indent=4))

    # --- Test Case 6: Compliance control with status 'Not Applicable' ---
    print("\n--- Test Case 6: Compliance control with status 'Not Applicable' ---")
    compliance_data_na = {
        "controls": [
            {"id": "C1", "name": "Test", "description": "Test", "status": "Compliant", "evidence": ""},
            {"id": "C_NA", "name": "Not Applicable Control", "description": "This control is not applicable to our environment.", "status": "Not Applicable", "evidence": "Rationale documented."}
        ]
    }
    frameworks_na = {
        "TestFramework": {
            "description": "Test",
            "controls": [
                {"id": "R1", "name": "Requirement for Test", "description": "Test", "mapped_controls": ["C1"]},
                {"id": "R2", "name": "Requirement for NA", "description": "Test", "mapped_controls": ["C_NA"]} # Mapped to Not Applicable control
            ]
        }
    }
    na_result = tool.generate_audit_report(compliance_data=compliance_data_na, regulatory_frameworks=frameworks_na)
    print(json.dumps(na_result, indent=4))
